import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from PIL import Image

MODEL_ID = os.getenv("AI_DETECTOR_MODEL_ID", "Organika/sdxl-detector")
MODEL_REVISION = os.getenv("AI_DETECTOR_MODEL_REVISION")


@lru_cache(maxsize=1)
def _load_model() -> tuple[Any, Any, Any]:
    import torch
    from transformers import AutoImageProcessor, AutoModelForImageClassification

    options: dict[str, str] = {}
    if MODEL_REVISION:
        options["revision"] = MODEL_REVISION
    processor = AutoImageProcessor.from_pretrained(MODEL_ID, **options)
    model = AutoModelForImageClassification.from_pretrained(MODEL_ID, **options)
    model.eval()
    return torch, processor, model


def detect_ai_image(image_path: str | Path) -> dict[str, Any]:
    try:
        torch, processor, model = _load_model()
    except ModuleNotFoundError as error:
        return {
            "status": "unavailable",
            "model": MODEL_ID,
            "model_revision": MODEL_REVISION or "not pinned",
            "details": (
                "AI classification requires the configured PyTorch and Transformers "
                f"dependencies: {error}"
            ),
        }
    with Image.open(image_path) as source:
        image = source.convert("RGB")
        inputs = processor(images=image, return_tensors="pt")

    with torch.inference_mode():
        logits = model(**inputs).logits[0]
        probabilities = torch.softmax(logits, dim=-1).cpu().tolist()

    labels = model.config.id2label
    scores = {
        str(labels.get(index, labels.get(str(index), f"LABEL_{index}"))): float(score)
        for index, score in enumerate(probabilities)
    }
    artificial_score = next(
        (
            score
            for label, score in scores.items()
            if any(term in label.casefold() for term in ("artificial", "synthetic", "fake", "ai"))
        ),
        None,
    )
    return {
        "model": MODEL_ID,
        "model_revision": getattr(model.config, "_commit_hash", None)
        or MODEL_REVISION
        or "unknown (model config does not expose a revision)",
        "scores": scores,
        "artificial_class_score": artificial_score,
        "predicted_label": max(scores, key=scores.get),
        "limitations": (
            "This classifier is a probabilistic indicator, not proof of provenance. "
            "Its documented training is SDXL-focused and performance varies across "
            "generators, edits, and image domains."
        ),
    }
