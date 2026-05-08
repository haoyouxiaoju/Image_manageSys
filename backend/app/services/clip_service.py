from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import logging
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.exceptions import ApiError

logger = logging.getLogger(__name__)

_LABELS_PATH = Path(__file__).resolve().parents[3] / "data" / "labels.json"

_DEFAULT_LABELS: dict[str, list[str]] = {
    "style": ["产品摄影", "商务海报", "写实风格", "极简风格", "科技风格"],
    "color": ["暖色调", "冷色调", "高对比", "低饱和", "明亮"],
    "scene": ["室内", "室外", "办公环境", "电商场景", "自然环境", "图书馆", "书桌", "书架", "阅读场景"],
    "content": ["书籍", "书本", "书页", "书封面", "翻开的书", "闭合的书", "纸张", "笔记本", "杂志", "文件", "教材", "报纸", "文档", "商品"],
    "objects": [
        "人物", "电脑", "手机", "文档", "建筑", "车辆", "食物", "植物", "宠物", "商品",
        "书籍", "书本", "书页", "书封面", "翻开的书", "闭合的书", "纸张", "笔记本", "杂志", "文件", "教材", "报纸",
    ],
}


def _load_labels() -> dict[str, list[str]]:
    if _LABELS_PATH.exists():
        try:
            with open(_LABELS_PATH, encoding="utf-8") as f:
                data = json.load(f)
            loaded: dict[str, list[str]] = {}
            for key in ("style", "color", "scene", "content", "objects"):
                items = data.get(key)
                if isinstance(items, list) and all(isinstance(v, str) for v in items):
                    loaded[key] = items
                else:
                    logger.warning("labels.json missing or invalid key '%s', using defaults.", key)
                    loaded[key] = _DEFAULT_LABELS[key]
            logger.info("Loaded %d label categories from %s", len(loaded), _LABELS_PATH)
            return loaded
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load labels.json (%s), using defaults.", exc)
    else:
        logger.info("labels.json not found at %s, using built-in defaults.", _LABELS_PATH)
    return dict(_DEFAULT_LABELS)


_LABELS = _load_labels()


@dataclass
class ClipAnalysisResult:
    provider: str
    model_name: str
    model_version: str
    embedding: list[float]
    features: dict[str, Any]
    suggested_description: str
    suggested_tags: list[str]


class ClipService:
    def __init__(self) -> None:
        self._provider = settings.clip_provider.strip().lower()
        self._device = settings.clip_device
        self._initialized = False
        self._ready = False
        self._last_error: str | None = None
        self._model: Any | None = None
        self._processor: Any | None = None
        self._torch: Any | None = None
        self._image_cls: Any | None = None

    def initialize(self) -> None:
        self._initialized = True
        self._ready = False
        self._last_error = None

        if not settings.clip_enabled:
            logger.info("CLIP service disabled by CLIP_ENABLED.")
            return

        if self._provider == "mock":
            self._ready = True
            logger.info("CLIP service started in mock provider mode.")
            return

        if self._provider != "chinese_clip":
            self._last_error = f"Unsupported CLIP_PROVIDER: {self._provider}"
            logger.error(self._last_error)
            return

        self._initialize_chinese_clip()

    def _initialize_chinese_clip(self) -> None:
        try:
            import torch
            from PIL import Image
            from transformers import AutoModel, AutoProcessor
        except ModuleNotFoundError as exc:
            self._last_error = (
                "Chinese-CLIP dependencies are missing. Install backend\\requirements-clip.txt. "
                f"Missing module: {exc.name}"
            )
            logger.error(self._last_error)
            return

        try:
            model = AutoModel.from_pretrained(
                settings.clip_model_name,
                revision=settings.clip_model_revision,
                trust_remote_code=True,
            )
            processor = AutoProcessor.from_pretrained(
                settings.clip_model_name,
                revision=settings.clip_model_revision,
                trust_remote_code=True,
            )
        except OSError as exc:
            self._last_error = f"Failed to load Chinese-CLIP model: {exc}"
            logger.error(self._last_error)
            return

        self._torch = torch
        self._image_cls = Image
        self._model = model.to(self._device).eval()
        self._processor = processor
        self._ready = True
        logger.info(
            "Chinese-CLIP model loaded. provider=%s model=%s revision=%s device=%s",
            self._provider,
            settings.clip_model_name,
            settings.clip_model_revision,
            self._device,
        )

    def status(self) -> dict[str, Any]:
        return {
            "enabled": settings.clip_enabled,
            "provider": self._provider,
            "model_name": settings.clip_model_name if self._provider == "chinese_clip" else "mock-clip",
            "model_version": settings.clip_model_revision if self._provider == "chinese_clip" else "mock-v1",
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
        return self._analyze_chinese_clip(path)

    def encode_text(self, text: str) -> list[float]:
        self._ensure_ready()
        cleaned = text.strip()
        if not cleaned:
            raise ApiError(status_code=400, code="EMPTY_QUERY", message="Query cannot be empty.")

        if self._provider == "mock":
            return self._encode_text_mock(cleaned)
        return self._encode_text_chinese_clip(cleaned)

    def _ensure_ready(self) -> None:
        if not settings.clip_enabled:
            raise ApiError(status_code=503, code="CLIP_DISABLED", message="CLIP service is disabled.")
        if not self._initialized:
            raise ApiError(status_code=503, code="CLIP_NOT_INITIALIZED", message="CLIP service is not initialized.")
        if not self._ready:
            reason = self._last_error or "CLIP model is not ready."
            raise ApiError(status_code=503, code="CLIP_MODEL_UNAVAILABLE", message=reason)

    def _analyze_mock(self, image_path: Path) -> ClipAnalysisResult:
        digest = sha256(image_path.read_bytes()).digest()
        embedding = self._digest_to_embedding(digest)
        style = _LABELS["style"][digest[0] % len(_LABELS["style"])]
        color = _LABELS["color"][digest[1] % len(_LABELS["color"])]
        scene = _LABELS["scene"][digest[2] % len(_LABELS["scene"])]
        content = _LABELS["content"][digest[3] % len(_LABELS["content"])]
        objects = [
            _LABELS["objects"][digest[4] % len(_LABELS["objects"])],
            _LABELS["objects"][digest[5] % len(_LABELS["objects"])],
        ]
        objects = list(dict.fromkeys(objects))
        suggested_tags = list(dict.fromkeys([style, color, scene, content, *objects]))
        return ClipAnalysisResult(
            provider="mock",
            model_name="mock-clip",
            model_version="mock-v1",
            embedding=embedding,
            features={"style": style, "color_tone": color, "scene": scene, "content": content, "objects": objects},
            suggested_description=f"{style}，{scene}，{color}，主体：{content}，包含：{'、'.join(objects)}",
            suggested_tags=suggested_tags,
        )

    def _encode_text_mock(self, text: str) -> list[float]:
        digest = sha256(text.encode("utf-8")).digest()
        return self._digest_to_embedding(digest)

    def _analyze_chinese_clip(self, image_path: Path) -> ClipAnalysisResult:
        torch = self._torch
        model = self._model
        processor = self._processor
        image_cls = self._image_cls
        if torch is None or model is None or processor is None or image_cls is None:
            raise ApiError(status_code=503, code="CLIP_MODEL_UNAVAILABLE", message="CLIP internals are not ready.")

        try:
            image = image_cls.open(image_path).convert("RGB")
            image_inputs = processor(images=image, return_tensors="pt")
            image_inputs = {
                key: value.to(self._device) if hasattr(value, "to") else value
                for key, value in image_inputs.items()
            }

            with torch.no_grad():
                image_features = model.get_image_features(**image_inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            embedding = image_features[0].detach().cpu().tolist()

            style = self._top_label(image_features, _LABELS["style"])
            color = self._top_label(image_features, _LABELS["color"])
            scene = self._top_label(image_features, _LABELS["scene"])
            content = self._top_label(image_features, _LABELS["content"])
            objects = self._top_labels(image_features, _LABELS["objects"], top_k=5)
            suggested_tags = list(dict.fromkeys([style, color, scene, content, *objects]))
            return ClipAnalysisResult(
                provider="chinese_clip",
                model_name=settings.clip_model_name,
                model_version=settings.clip_model_revision,
                embedding=embedding,
                features={"style": style, "color_tone": color, "scene": scene, "content": content, "objects": objects},
                suggested_description=f"{style}，{scene}，{color}，主体：{content}，包含：{'、'.join(objects)}",
                suggested_tags=suggested_tags,
            )
        except (RuntimeError, ValueError, OSError) as exc:
            raise ApiError(
                status_code=500,
                code="CLIP_ANALYZE_FAILED",
                message=f"CLIP analyze failed: {exc}",
            ) from exc

    def _top_label(self, image_features: Any, labels: list[str]) -> str:
        scores = self._label_scores(image_features, labels)
        best_index = int(scores.argmax().item())
        return labels[best_index]

    def _top_labels(self, image_features: Any, labels: list[str], top_k: int) -> list[str]:
        scores = self._label_scores(image_features, labels)
        torch = self._torch
        if torch is None:
            return labels[:top_k]
        top = torch.topk(scores, k=min(top_k, len(labels))).indices.tolist()
        return [labels[index] for index in top]

    def _label_scores(self, image_features: Any, labels: list[str]) -> Any:
        torch = self._torch
        model = self._model
        processor = self._processor
        if torch is None or model is None or processor is None:
            raise ApiError(status_code=503, code="CLIP_MODEL_UNAVAILABLE", message="CLIP internals are not ready.")

        prompts = [f"一张{label}的图片" for label in labels]
        text_inputs = processor(text=prompts, return_tensors="pt", padding=True, truncation=True)
        text_inputs = {
            key: value.to(self._device) if hasattr(value, "to") else value
            for key, value in text_inputs.items()
        }
        with torch.no_grad():
            text_features = model.get_text_features(**text_inputs)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        return (image_features @ text_features.T)[0]

    def _encode_text_chinese_clip(self, text: str) -> list[float]:
        torch = self._torch
        model = self._model
        processor = self._processor
        if torch is None or model is None or processor is None:
            raise ApiError(status_code=503, code="CLIP_MODEL_UNAVAILABLE", message="CLIP internals are not ready.")

        try:
            text_inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True)
            text_inputs = {
                key: value.to(self._device) if hasattr(value, "to") else value
                for key, value in text_inputs.items()
            }
            with torch.no_grad():
                text_features = model.get_text_features(**text_inputs)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            return text_features[0].detach().cpu().tolist()
        except (RuntimeError, ValueError, OSError) as exc:
            raise ApiError(
                status_code=500,
                code="CLIP_TEXT_ENCODE_FAILED",
                message=f"CLIP text encode failed: {exc}",
            ) from exc

    def rank_text_labels(self, text: str, labels: list[str]) -> list[tuple[str, float]]:
        self._ensure_ready()
        if self._provider == "mock":
            return self._rank_text_labels_mock(text, labels)
        return self._rank_text_labels_chinese_clip(text, labels)

    def _rank_text_labels_mock(self, text: str, labels: list[str]) -> list[tuple[str, float]]:
        text_bytes = sha256(text.encode("utf-8")).digest()
        scored = []
        for index, label in enumerate(labels):
            label_bytes = sha256(f"{text}|{label}".encode("utf-8")).digest()
            score = ((text_bytes[index % len(text_bytes)] + label_bytes[(index * 7) % len(label_bytes)]) % 1000) / 1000.0
            scored.append((label, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored

    def _rank_text_labels_chinese_clip(self, text: str, labels: list[str]) -> list[tuple[str, float]]:
        torch = self._torch
        model = self._model
        processor = self._processor
        if torch is None or model is None or processor is None:
            raise ApiError(status_code=503, code="CLIP_MODEL_UNAVAILABLE", message="CLIP internals are not ready.")

        try:
            query_inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True)
            query_inputs = {
                key: value.to(self._device) if hasattr(value, "to") else value
                for key, value in query_inputs.items()
            }
            label_inputs = processor(text=labels, return_tensors="pt", padding=True, truncation=True)
            label_inputs = {
                key: value.to(self._device) if hasattr(value, "to") else value
                for key, value in label_inputs.items()
            }
            with torch.no_grad():
                query_features = model.get_text_features(**query_inputs)
                label_features = model.get_text_features(**label_inputs)
            query_features = query_features / query_features.norm(dim=-1, keepdim=True)
            label_features = label_features / label_features.norm(dim=-1, keepdim=True)
            scores = (query_features @ label_features.T)[0]
            ranked = [(label, float(scores[index].item())) for index, label in enumerate(labels)]
            ranked.sort(key=lambda item: item[1], reverse=True)
            return ranked
        except (RuntimeError, ValueError, OSError) as exc:
            raise ApiError(
                status_code=500,
                code="CLIP_TEXT_RANK_FAILED",
                message=f"CLIP text rank failed: {exc}",
            ) from exc

    @staticmethod
    def _digest_to_embedding(digest: bytes) -> list[float]:
        return [round((byte - 127.5) / 127.5, 6) for byte in digest]


clip_service = ClipService()
