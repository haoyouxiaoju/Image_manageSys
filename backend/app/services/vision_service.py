from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import mimetypes
from pathlib import Path
import re
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.core.exceptions import ApiError

logger = logging.getLogger(__name__)

_ANALYSIS_PROMPT = """# Role
你是企业级数字资产库的元数据生成专家。你的任务是将输入的图片转化为结构化的 JSON 数据，用于图像检索和AI重绘。

# Output Format
 strictly output a valid JSON object. Do NOT include markdown code blocks (like ```json), explanations, or extra text.
Format:
{
  "prompt": "string",
  "summary": "string",
  "keywords": ["string"]
}

# Field Definitions & Guidelines

1. **prompt (中文提示词)**:
   - 目标：能够被 Midjourney/Stable Diffusion 等工具高精度复现原图。
   - 结构必须包含：[主体描述] + [环境/背景] + [构图/视角] + [光影/天气] + [艺术风格/渲染引擎] + [色调/氛围]。
   - 要求：描述需具象化。例如，不要说"一个漂亮的女人"，要说"一位穿着白色丝绸衬衫的亚洲女性，黑色长发，自然妆容"。

2. **summary (画面核心陈述)**:
   - 定义：用简练、客观的语言概括图片的核心内容（谁/什么 + 在做什么/状态 + 在哪里）。
   - 长度：限制在 20-40 字以内。
   - 禁忌：禁止使用"这张图片展示了..."、"图中有..."等废话开头，直接描述画面。

3. **keywords (标签列表)**:
   - 数量：严格控制在 6-15 个之间。
   - 类型：优先提取实体名词（如： MacBook Pro, 拿铁咖啡, 绿植）、具体风格（如： 极简主义, 赛博朋克）、具体动作或状态。
   - 禁忌：严禁使用"高清"、"精美"、"高质量"、"图片"、"摄影"等无信息量的泛词。

# Example Logic
Input: [一张在阳光下办公桌上的笔记本电脑图片]
Output:
{
  "prompt": "特写镜头，一台银色的MacBook Pro打开放置在浅色木纹办公桌上，屏幕显示着代码界面，旁边有一杯冒着热气的拿铁咖啡和一盆小型多肉植物。自然光从左侧窗户射入，形成柔和的高光和阴影，景深效果，背景虚化，现代简约办公风格，明亮清新的色调。",
  "summary": "阳光下的木纹办公桌上放置着打开的笔记本电脑和咖啡。",
  "keywords": ["笔记本电脑", "MacBook", "办公桌", "木纹", "拿铁咖啡", "多肉植物", "自然光", "特写", "办公场景", "简约风格", "代码界面", "窗边"]
}
"""


@dataclass
class VisionAnalysisResult:
    provider: str
    model_name: str
    model_version: str
    embedding: list[float] | None
    features: dict[str, Any] | None
    generated_prompt: str
    suggested_description: str
    suggested_tags: list[str]


class VisionService:
    def __init__(self) -> None:
        self._provider = settings.vision_provider.strip().lower()
        self._initialized = False
        self._ready = False
        self._last_error: str | None = None
        self._client: OpenAI | None = None

    def initialize(self) -> None:
        self._initialized = True
        self._ready = False
        self._last_error = None
        self._client = None

        if not settings.vision_enabled:
            logger.info("Vision service disabled by VISION_ENABLED.")
            return

        if self._provider != "qwen3_vl":
            self._last_error = f"Unsupported VISION_PROVIDER: {self._provider}"
            logger.error(self._last_error)
            return

        if not settings.dashscope_api_key:
            self._last_error = "DASHSCOPE_API_KEY is missing."
            logger.error(self._last_error)
            return

        self._client = OpenAI(
            base_url=settings.qwen_base_url,
            api_key=settings.dashscope_api_key,
            timeout=90.0,
            max_retries=2,
        )
        self._ready = True
        logger.info("Qwen3-VL service configured. model=%s endpoint=%s", settings.vision_model_name, settings.qwen_base_url)

    def status(self) -> dict[str, Any]:
        return {
            "enabled": settings.vision_enabled,
            "provider": self._provider,
            "model_name": settings.vision_model_name,
            "model_version": settings.vision_model_revision,
            "initialized": self._initialized,
            "ready": self._ready,
            "last_error": self._last_error,
        }

    def analyze_file(self, image_path: str | Path) -> VisionAnalysisResult:
        self._ensure_ready()
        path = Path(image_path)
        if not path.exists():
            raise ApiError(status_code=404, code="FILE_NOT_FOUND", message="Image file does not exist.")
        return self._analyze_qwen(path)

    def _ensure_ready(self) -> None:
        if not settings.vision_enabled:
            raise ApiError(status_code=503, code="VISION_DISABLED", message="Vision service is disabled.")
        if not self._initialized:
            raise ApiError(status_code=503, code="VISION_NOT_INITIALIZED", message="Vision service is not initialized.")
        if not self._ready:
            reason = self._last_error or "Vision model is not ready."
            raise ApiError(status_code=503, code="VISION_MODEL_UNAVAILABLE", message=reason)

    def _analyze_qwen(self, image_path: Path) -> VisionAnalysisResult:
        mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
        image_b64 = _b64encode(image_path.read_bytes())
        data_uri = f"data:{mime_type};base64,{image_b64}"

        try:
            response = self._client.chat.completions.create(
                model=settings.vision_model_name,
                messages=[
                    {"role": "system", "content": "你是严格输出 JSON 的视觉理解助手。"},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": _ANALYSIS_PROMPT},
                            {"type": "image_url", "image_url": {"url": data_uri}},
                        ],
                    },
                ],
                temperature=0.1,
            )
            raw_content = response.choices[0].message.content or ""
        except Exception as exc:
            raise ApiError(status_code=502, code="QWEN_REQUEST_FAILED", message=f"Qwen API request failed: {exc}") from exc

        parsed = self._parse_qwen_json(raw_content)
        keywords = [item.strip() for item in parsed.get("keywords", []) if isinstance(item, str) and item.strip()]
        if not keywords:
            raise ApiError(status_code=500, code="QWEN_EMPTY_KEYWORDS", message="Qwen returned empty keywords.")

        generated_prompt = parsed.get("prompt", "").strip() if isinstance(parsed.get("prompt"), str) else ""
        if not generated_prompt:
            generated_prompt = (
                f"{'、'.join(keywords[:8])}，商业摄影，主体清晰，构图完整，光线自然，写实风格。"
            )

        summary = parsed.get("summary", "").strip() if isinstance(parsed.get("summary"), str) else ""
        if not summary:
            summary = f"图片包含：{'、'.join(keywords[:6])}。"

        return VisionAnalysisResult(
            provider="qwen3_vl",
            model_name=settings.vision_model_name,
            model_version=settings.vision_model_revision,
            embedding=None,
            features={"strategy": "qwen-prompt-keywords"},
            generated_prompt=generated_prompt,
            suggested_description=summary,
            suggested_tags=list(dict.fromkeys(keywords)),
        )

    @staticmethod
    def _parse_qwen_json(content: str) -> dict[str, Any]:
        cleaned = content.strip()
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if not match:
            raise ApiError(status_code=500, code="QWEN_PARSE_FAILED", message="Qwen response does not contain JSON.")
        try:
            parsed = json.loads(match.group(0))
            if not isinstance(parsed, dict):
                raise ValueError("Parsed content is not an object.")
            return parsed
        except (json.JSONDecodeError, ValueError) as exc:
            raise ApiError(status_code=500, code="QWEN_PARSE_FAILED", message=f"Qwen JSON parse failed: {exc}") from exc


def _b64encode(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")


vision_service = VisionService()
