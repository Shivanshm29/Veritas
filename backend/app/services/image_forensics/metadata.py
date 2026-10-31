import hashlib
from pathlib import Path
from typing import Any

from PIL import ExifTags, Image


def analyze_metadata(image_path: str | Path) -> dict[str, Any]:
    path = Path(image_path)
    with Image.open(path) as image:
        exif = {
            str(ExifTags.TAGS.get(tag_id, tag_id)): str(value)
            for tag_id, value in image.getexif().items()
        }
        properties = {
            "filename": path.name,
            "format": image.format,
            "width": image.width,
            "height": image.height,
            "frame_count": getattr(image, "n_frames", 1),
            "is_animated": bool(getattr(image, "is_animated", False)),
            "mode": image.mode,
            "color_bands": list(image.getbands()),
            "has_transparency": "A" in image.getbands() or "transparency" in image.info,
            "exif": exif,
        }

    digest = hashlib.sha256()
    with path.open("rb") as image_file:
        for chunk in iter(lambda: image_file.read(1024 * 1024), b""):
            digest.update(chunk)

    return {
        **properties,
        "file_size_bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
        "limitations": (
            "Missing EXIF metadata is common and does not by itself indicate "
            "manipulation. Only the first frame of animated or multi-page images "
            "is analyzed."
        ),
    }
