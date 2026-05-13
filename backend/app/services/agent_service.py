from __future__ import annotations

import json
import logging
import re
from time import perf_counter
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.core.exceptions import ApiError
from app.services.vector_search_service import vector_search_service

logger = logging.getLogger(__name__)

_REWRITE_SYSTEM_PROMPT = """将用户的简短搜索词改写为一段丰富的描述语句，用于语义向量搜索。
规则：
- 保留原始意图，不添加用户没提到的内容
- 补充同义词、相关概念、常见搭配（如"汽车"→ 补充"轿车、SUV、跑车"）
- 输出纯中文描述，不要任何解释或 markdown
- 一句话即可，80字以内"""

_SYSTEM_PROMPT = """# 角色
你是企业数字资产库的智能检索助手。系统已完成语义向量搜索，你的任务是为候选结果评分并生成匹配理由。

# 输入格式
系统提供每条结果的 asset_id、summary（画面核心描述）和 tags（实体/风格标签列表）。

# 输出格式（严格 JSON，无 markdown 包裹）
{
  "results": [
    {
      "asset_id": 1,
      "relevance": 0.92,
      "match_reason": "画面中蓝色科技感背景与查询高度吻合，包含代码界面和现代办公风格"
    }
  ],
  "summary": "检索策略简述，20字以内"
}

# relevance 打分规则
- 0.9-1.0: 高度匹配，画面主体与查询完全一致
- 0.7-0.9: 较好匹配，画面主体相关但存在部分差异
- 0.5-0.7: 部分匹配，相关元素但整体偏差较大
- 0.3-0.5: 弱匹配，仅边缘相关
- <0.3: 不相关，过滤掉

关注用户查询中的细化限定词（如"炸"vs"清汤"、"面"vs"饭"、"现代"vs"古典"），根据 summary 和 tags 具体描述严格区分。

# 规则
- **必须为输入中的每一条结果都评分**，不要跳过、不要省略
- asset_id 必须使用输入中给出的 ID
- match_reason 基于 summary 和 tags 实际内容生成（15-30字），简述与查询的关联点和差异点
- 每条结果一条记录
"""


class AgentService:
    def __init__(self) -> None:
        self._enabled = settings.agent_enabled
        self._initialized = False
        self._ready = False
        self._last_error: str | None = None
        self._client: OpenAI | None = None

    def initialize(self) -> None:
        self._initialized = True
        self._ready = False
        self._last_error = None
        self._client = None

        if not self._enabled:
            logger.info("Agent search disabled by AGENT_ENABLED.")
            return

        if not settings.dashscope_api_key:
            self._last_error = "DASHSCOPE_API_KEY is missing."
            logger.error(self._last_error)
            return

        self._client = OpenAI(
            base_url=settings.qwen_base_url,
            api_key=settings.dashscope_api_key,
        )
        self._ready = True
        logger.info("Agent service initialized. model=%s", settings.agent_chat_model)

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self._enabled,
            "initialized": self._initialized,
            "ready": self._ready,
            "last_error": self._last_error,
            "model": settings.agent_chat_model,
        }

    def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        t_total = perf_counter()
        self._ensure_ready()

        normalized_query = query.strip()
        if not normalized_query:
            raise ApiError(status_code=400, code="EMPTY_QUERY", message="Search query cannot be empty.")

        # Step 1: LLM 改写查询 — 扩展语义覆盖（同义词、相关概念、不同角度）
        t_rewrite = perf_counter()
        enriched_query = self._rewrite_query(normalized_query)
        t_rewrite_elapsed = (perf_counter() - t_rewrite) * 1000
        logger.info("[agent-search] rewrite query=%r -> %r elapsed=%.0fms",
                     normalized_query, enriched_query, t_rewrite_elapsed)

        # Step 2: 向量搜索
        t_vs = perf_counter()
        hits, vs_total = vector_search_service.search_assets(
            query=enriched_query,
            limit=page_size,
            offset=(page - 1) * page_size,
        )
        t_vs_elapsed = (perf_counter() - t_vs) * 1000
        logger.info("[agent-search] vector_search hits=%d total=%d elapsed=%.0fms",
                     len(hits), vs_total, t_vs_elapsed)

        if not hits:
            return {"items": [], "reasoning": "未找到匹配的图片素材。"}

        # Step 3: 过滤低分噪声
        min_score = settings.agent_min_score
        filtered = [h for h in hits if h.score >= min_score]
        if not filtered:
            filtered = hits[:1]
        logger.info("[agent-search] filtered min_score=%.2f before=%d after=%d",
                     min_score, len(hits), len(filtered))

        # Step 4: LLM 评分 + 写理由（覆盖全部过滤后结果，上限 10 条控制延迟）
        top_for_llm = filtered[:10]
        llm_reasons: dict[int, str] = {}
        llm_scores: dict[int, float] = {}
        reasoning_summary = ""

        t_llm = perf_counter()
        try:
            llm_reasons, llm_scores, reasoning_summary = self._generate_reasons(normalized_query, top_for_llm)
            t_llm_elapsed = (perf_counter() - t_llm) * 1000
            logger.info("[agent-search] llm_reasons count=%d elapsed=%.0fms",
                        len(llm_reasons), t_llm_elapsed)
        except Exception as exc:
            t_llm_elapsed = (perf_counter() - t_llm) * 1000
            logger.warning("[agent-search] llm_reasons failed elapsed=%.0fms error=%s", t_llm_elapsed, exc)

        # Step 5: 合并结果
        items: list[dict[str, Any]] = []
        for hit in filtered:
            items.append({
                "asset_id": hit.asset_id,
                "score": round(hit.score, 4),
                "llm_relevance": llm_scores.get(hit.asset_id),
                "match_reason": llm_reasons.get(hit.asset_id, ""),
            })

        t_total_elapsed = (perf_counter() - t_total) * 1000
        logger.info("[agent-search] DONE query=%r results=%d rewrite=%.0fms vs=%.0fms total=%.0fms",
                     normalized_query, len(items), t_rewrite_elapsed, t_vs_elapsed, t_total_elapsed)

        return {"items": items, "reasoning": reasoning_summary}

    def _rewrite_query(self, query: str) -> str:
        """LLM 将用户简短查询改写为丰富的搜索描述，扩展语义覆盖。"""
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": _REWRITE_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]
        try:
            response = self._client.chat.completions.create(
                model=settings.agent_chat_model,
                messages=messages,
                temperature=0.2,
                max_tokens=256,
            )
            rewritten = (response.choices[0].message.content or "").strip()
            if rewritten:
                return rewritten
        except Exception as exc:
            logger.warning("[agent-search] rewrite failed: %s", exc)
        return query  # 降级：用原始查询

    def _generate_reasons(
        self,
        query: str,
        hits: list,
    ) -> tuple[dict[int, str], dict[int, float], str]:
        """Ask LLM to score and write match_reasons for top results."""
        results_lines = []
        for h in hits:
            kw = ", ".join(h.keywords[:6]) if h.keywords else ""
            results_lines.append(f"  {h.asset_id}: {h.summary}  [标签: {kw}]")
        results_text = "\n".join(results_lines)
        user_message = f"查询：{query}\n\n搜索结果：\n{results_text}"

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        response = self._client.chat.completions.create(
            model=settings.agent_chat_model,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )

        parsed = self._parse_agent_response(response.choices[0].message.content or "")
        reasons: dict[int, str] = {}
        llm_scores: dict[int, float] = {}
        for r in parsed.get("results", []):
            aid = r.get("asset_id")
            if aid is None:
                continue
            reason = r.get("match_reason", "")
            relevance = r.get("relevance")
            if reason:
                reasons[int(aid)] = reason
            if relevance is not None and isinstance(relevance, (int, float)):
                llm_scores[int(aid)] = round(float(relevance), 4)
        return reasons, llm_scores, parsed.get("summary", "")

    def _ensure_ready(self) -> None:
        if not self._enabled:
            raise ApiError(status_code=503, code="AGENT_DISABLED", message="Agent search is disabled.")
        if not self._initialized:
            raise ApiError(status_code=503, code="AGENT_NOT_INITIALIZED", message="Agent service is not initialized.")
        if not self._ready or not self._client:
            reason = self._last_error or "Agent service is not ready."
            raise ApiError(status_code=503, code="AGENT_UNAVAILABLE", message=reason)

    @staticmethod
    def _parse_agent_response(content: str) -> dict[str, Any]:
        cleaned = content.strip()
        # Try to find JSON object in the content
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if not match:
            logger.warning("Agent response does not contain JSON: %s", cleaned[:200])
            return {"results": [], "summary": cleaned[:100]}
        try:
            parsed = json.loads(match.group(0))
            if not isinstance(parsed, dict):
                return {"results": [], "summary": str(parsed)[:100]}
            return parsed
        except json.JSONDecodeError as exc:
            logger.warning("Agent JSON parse failed: %s", exc)
            return {"results": [], "summary": cleaned[:100]}


agent_service = AgentService()
