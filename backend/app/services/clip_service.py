from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import logging
import mimetypes
from pathlib import Path
import re
from typing import Any
from urllib import request as urllib_request

from app.core.config import settings
from app.core.exceptions import ApiError

logger = logging.getLogger(__name__)

_MOCK_KEYWORDS = [
    "书籍",
    "商品",
    "人物",
    "电子产品",
    "办公场景",
    "自然风景",
    "建筑",
    "美食",
    "文档",
    "设备",
    "室内",
    "室外",
]


@dataclass
class ClipAnalysisResult:
    provider: str
    model_name: str
    model_version: str
    embedding: list[float] | None
    features: dict[str, Any] | None
    suggested_description: str
    suggested_tags: list[str]


class ClipService:
    def __init__(self) -> None:
        self._provider = settings.clip_provider.strip().lower()
        self._initialized = False
        self._ready = False
        self._last_error: str | None = None

    def initialize(self) -> None:
        self._initialized = True
        self._ready = False
        self._last_error = None

        if not settings.clip_enabled:
            logger.info("Vision service disabled by CLIP_ENABLED.")
            return

        if self._provider == "mock":
            self._ready = True
            logger.info("Vision service started in mock provider mode.")
            return

        if self._provider != "qwen3_vl":
            self._last_error = f"Unsupported CLIP_PROVIDER: {self._provider}"
            logger.error(self._last_error)
            return

        if not settings.dashscope_api_key:
            self._last_error = "DASHSCOPE_API_KEY is missing."
            logger.error(self._last_error)
            return

        self._ready = True
        logger.info("Qwen3-VL service configured. model=%s endpoint=%s", settings.clip_model_name, settings.qwen_base_url)

    def status(self) -> dict[str, Any]:
        return {
            "enabled": settings.clip_enabled,
            "provider": self._provider,
            "model_name": settings.clip_model_name if self._provider != "mock" else "mock-vision",
            "model_version": settings.clip_model_revision if self._provider != "mock" else "mock-v1",
            "initialized": self._initialized,
            "ready": self._ready,
            "last_error": self._last_error,
        }

    def analyze_file(self, image_path: str | Path) -> ClipAnalysisResult:
        self._ensure_ready()
        path = Path(image_path)
        if not path.exists():
            raise ApiError(status_code=404, code="FILE_NOT_FOUND", message="Image file does not exist.")

        if self._provider == "mock":
            return self._analyze_mock(path)
        return self._analyze_qwen(path)

    def _ensure_ready(self) -> None:
        if not settings.clip_enabled:
            raise ApiError(status_code=503, code="VISION_DISABLED", message="Vision service is disabled.")
        if not self._initialized:
            raise ApiError(status_code=503, code="VISION_NOT_INITIALIZED", message="Vision service is not initialized.")
        if not self._ready:
            reason = self._last_error or "Vision model is not ready."
            raise ApiError(status_code=503, code="VISION_MODEL_UNAVAILABLE", message=reason)

    def _analyze_mock(self, image_path: Path) -> ClipAnalysisResult:
        digest = sha256(image_path.read_bytes()).digest()
        keywords = [
            _MOCK_KEYWORDS[digest[0] % len(_MOCK_KEYWORDS)],
            _MOCK_KEYWORDS[digest[1] % len(_MOCK_KEYWORDS)],
            _MOCK_KEYWORDS[digest[2] % len(_MOCK_KEYWORDS)],
            _MOCK_KEYWORDS[digest[3] % len(_MOCK_KEYWORDS)],
        ]
        deduped = list(dict.fromkeys(keywords))
        summary = f"图片主要内容涉及：{'、'.join(deduped)}。"
        return ClipAnalysisResult(
            provider="mock",
            model_name="mock-vision",
            model_version="mock-v1",
            embedding=None,
            features={"strategy": "mock-keywords"},
            suggested_description=summary,
            suggested_tags=deduped,
        )

    def _analyze_qwen(self, image_path: Path) -> ClipAnalysisResult:
        mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
        image_b64 = _b64encode(image_path.read_bytes())
        data_uri = f"data:{mime_type};base64,{image_b64}"

        prompt = (
            "你是企业素材库的图片解析助手。请根据图片内容输出 JSON，字段固定为："
            "{\"summary\":\"一句中文摘要\",\"keywords\":[\"关键词1\",\"关键词2\",...] }。"
            "keywords 输出 5-12 个中文关键词，避免泛词，优先主体名词（如书籍、笔记本电脑、咖啡杯）。"
            "只输出 JSON，不要输出其它内容。"
        )

        payload = {
            "model": settings.clip_model_name,
            "messages": [
                {"role": "system", "content": "你是严格输出 JSON 的视觉理解助手。"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                },
            ],
            "temperature": 0.1,
        }

        url = settings.qwen_base_url.rstrip("/") + "/chat/completions"
        req = urllib_request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.dashscope_api_key}",
            },
            method="POST",
        )

        try:
            with urllib_request.urlopen(req, timeout=90) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise ApiError(status_code=502, code="QWEN_REQUEST_FAILED", message=f"Qwen API request failed: {exc}") from exc

        content = self._extract_content(raw)
        parsed = self._parse_qwen_json(content)
        keywords = [item.strip() for item in parsed.get("keywords", []) if isinstance(item, str) and item.strip()]
        if not keywords:
            raise ApiError(status_code=500, code="QWEN_EMPTY_KEYWORDS", message="Qwen returned empty keywords.")

        summary = parsed.get("summary", "").strip() if isinstance(parsed.get("summary"), str) else ""
        if not summary:
            summary = f"图片包含：{'、'.join(keywords[:6])}。"

        return ClipAnalysisResult(
            provider="qwen3_vl",
            model_name=settings.clip_model_name,
            model_version=settings.clip_model_revision,
            embedding=None,
            features={"strategy": "qwen-keywords"},
            suggested_description=summary,
            suggested_tags=list(dict.fromkeys(keywords)),
        )

    @staticmethod
    def _extract_content(raw: dict[str, Any]) -> str:
        try:
            return raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ApiError(status_code=500, code="QWEN_INVALID_RESPONSE", message="Qwen response format is invalid.") from exc

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


clip_service = ClipService()
