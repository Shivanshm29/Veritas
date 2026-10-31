from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageEnhance


def analyze_ela(
    image_path: str | Path,
    output_dir: str | Path,
    quality: int = 90,
    scale: float = 15.0,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    heatmap_path = output_dir / "ela_heatmap.png"

    with Image.open(image_path) as source:
        original = source.convert("RGB")
        recompressed_path = output_dir / "ela_recompressed.jpg"
        original.save(recompressed_path, format="JPEG", quality=quality)
        with Image.open(recompressed_path) as recompressed_file:
            recompressed = recompressed_file.convert("RGB")
        difference = ImageChops.difference(original, recompressed)
        enhanced = ImageEnhance.Brightness(difference).enhance(scale)
        enhanced.save(heatmap_path)

    difference_values = np.asarray(difference, dtype=np.float32)
    pixel_error = difference_values.mean(axis=2)
    return {
        "method": "JPEG recompression difference",
        "recompression_quality": quality,
        "display_amplification": scale,
        "mean_absolute_difference": float(difference_values.mean()),
        "maximum_channel_difference": int(difference_values.max()),
        "pixel_difference_percentiles": {
            "50": float(np.percentile(pixel_error, 50)),
            "90": float(np.percentile(pixel_error, 90)),
            "99": float(np.percentile(pixel_error, 99)),
        },
        "interpretation": (
            "ELA differences are affected by image content, prior compression, and "
            "processing; bright regions alone do not establish manipulation."
        ),
        "limitations": (
            "ELA is a visualization aid, not a calibrated detector or proof of "
            "manipulation."
        ),
        "artifact_paths": {
            "heatmap": str(heatmap_path.resolve()),
            "recompressed_image": str(recompressed_path.resolve()),
        },
    }
