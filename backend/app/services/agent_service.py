from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.core.exceptions import ApiError
from app.services.vector_search_service import vector_search_service

logger = logging.getLogger(__name__)

_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "vector_search",
            "description": "语义搜索图片素材库，输入中文或英文描述返回匹配的素材列表。可以多次调用，从不同角度进行检索（如 '现代办公室' 可分别搜 '现代办公空间'、'minimalist office'、'coworking space'）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询词，中文或英文描述",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量上限",
                        "default": 10,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "分页偏移量",
                        "default": 0,
                    },
                },
                "required": ["query"],
            },
        },
    },
]

_SYSTEM_PROMPT = """# 角色
你是企业数字资产库的智能检索引擎。用户用自然语言描述需要的图片素材，你理解意图后进行语义检索。

# 工作流程
1. 分析用户意图，提取核心检索概念
2. 调用 vector_search 工具进行搜索。如果用户需求涉及多个角度，分别用不同查询词调用多次（如 "找现代办公室风格的图" → 分别搜 "现代办公空间"、"minimalist office"、"coworking space"）
3. 评估返回结果是否满足用户需求，如果结果不够好，调整查询词再搜一轮
4. 汇总所有结果，去重，为每张匹配的图片生成中文匹配理由（如 "色调是典型的现代明亮办公风格"、"画面包含开放式工位布局"）

# 最终输出格式
严格输出 JSON 对象，不要包含 markdown 代码块或额外文字：
{
  "results": [
    {
      "asset_id": 1,
      "match_reason": "画面中的蓝色科技感背景与查询高度吻合"
    }
  ],
  "summary": "本次检索的推理过程简要说明"
}

# 规则
- asset_id 必须是 vector_search 返回的实际 ID，不要编造
- match_reason 为每张图片生成一条中文匹配理由
- summary 简要说明你的检索策略和判断过程，50字以内
- 如果 vector_search 返回空结果，尝试换个角度重新搜索，不要直接放弃
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
        self._ensure_ready()

        normalized_query = query.strip()
        if not normalized_query:
            raise ApiError(status_code=400, code="EMPTY_QUERY", message="Search query cannot be empty.")

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": normalized_query},
        ]

        max_calls = settings.agent_max_tool_calls
        reasoning_summary = ""
        final_results: list[dict[str, Any]] = []

        for _ in range(max_calls):
            response = self._client.chat.completions.create(
                model=settings.agent_chat_model,
                messages=messages,
                tools=_TOOL_SCHEMAS,
                temperature=0.3,
            )

            choice = response.choices[0]
            message = choice.message

            if message.tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in message.tool_calls
                    ],
                })

                for tc in message.tool_calls:
                    if tc.function.name != "vector_search":
                        continue
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    search_query = args.get("query", normalized_query)
                    limit = args.get("limit", 10)
                    offset = args.get("offset", 0)

                    try:
                        hits, _total = vector_search_service.search_assets(
                            query=search_query,
                            limit=limit,
                            offset=offset,
                        )
                        tool_result = {
                            "query": search_query,
                            "results": [
                                {"asset_id": hit.asset_id, "score": round(hit.score, 6)}
                                for hit in hits
                            ],
                        }
                    except ApiError as exc:
                        tool_result = {"error": exc.message}

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    })
            else:
                # LLM returned final text response
                final_text = message.content or ""
                parsed = self._parse_agent_response(final_text)
                final_results = parsed.get("results", [])
                reasoning_summary = parsed.get("summary", "")
                break

        if not final_results:
            # If agent didn't produce a structured response, try to parse from last message
            reasoning_summary = "Agent 未返回结构化结果，请尝试更精确的描述。"

        return {
            "items": final_results,
            "reasoning": reasoning_summary,
        }

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
