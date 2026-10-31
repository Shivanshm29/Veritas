"""
MIME and media signature validation service for Veritas evidence assets.

Enforces conservative allowlists, header sniffing (magic bytes), and filename sanitization
to prevent arbitrary file uploads, path traversal, and file spoofing.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from backend.app.core.errors import InvalidMimeTypeError, InvalidAssetError, EmptyFileError

# Conservative allowlist of multimedia MIME types accepted by Veritas
ALLOWED_MIME_TYPES: Set[str] = {
    # Images
    "image/jpeg",
    "image/png",
    "image/webp",
    # Video
    "video/mp4",
    "video/webm",
    "video/quicktime",
    # Audio
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/mp4",
}

# Standard extension mappings
EXTENSION_MIME_MAP: Dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
}


def sanitize_filename(filename: Optional[str]) -> str:
    """
    Sanitizes an untrusted filename to prevent path traversal, null-byte injection,
    and filesystem reserved name collisions.
    """
    if not filename:
        return "unnamed_asset"

    # Remove null bytes
    sanitized = filename.replace("\x00", "")

    # Extract basename to eliminate directory traversal sequences (../, C:\, etc.)
    sanitized = Path(sanitized).name
    sanitized = os.path.basename(sanitized)

    # Disallow leading/trailing dots and spaces
    sanitized = sanitized.strip(". ")

    # Strip dangerous characters, keeping alphanumeric, dots, dashes, and underscores
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", sanitized)

    # Collapse multiple consecutive underscores
    sanitized = re.sub(r"_+", "_", sanitized)

    if not sanitized or sanitized in {".", ".."}:
        sanitized = "unnamed_asset"

    # Truncate length if excessively long
    if len(sanitized) > 200:
        stem = Path(sanitized).stem[:190]
        suffix = Path(sanitized).suffix[:10]
        sanitized = f"{stem}{suffix}"

    return sanitized


def detect_and_validate_mime(
    header_bytes: bytes,
    original_filename: str,
    declared_mime: Optional[str] = None,
) -> str:
    """
    Validates file signatures (magic bytes) against the declared or extension MIME type.
    Ensures the asset is an authentic multimedia file in the conservative allowlist.
    """
    if not header_bytes:
        raise EmptyFileError("Uploaded asset stream contains 0 bytes.")

    # Dangerous payload checks
    if header_bytes.startswith(b"MZ"):  # Windows PE executable
        raise InvalidAssetError("Executable binary uploads (MZ/PE) are forbidden.")
    if header_bytes.startswith(b"\x7fELF"):  # Linux ELF binary
        raise InvalidAssetError("Executable binary uploads (ELF) are forbidden.")
    if header_bytes.startswith(b"#!/") or header_bytes.startswith(b"<?php"):
        raise InvalidAssetError("Script execution uploads are forbidden.")

    detected_mime: Optional[str] = None

    # Magic byte inspection
    if header_bytes.startswith(b"\xFF\xD8\xFF"):
        detected_mime = "image/jpeg"
    elif header_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_mime = "image/png"
    elif len(header_bytes) >= 12 and header_bytes[:4] == b"RIFF" and header_bytes[8:12] == b"WEBP":
        detected_mime = "image/webp"
    elif len(header_bytes) >= 12 and header_bytes[:4] == b"RIFF" and header_bytes[8:12] == b"WAVE":
        detected_mime = "audio/wav"
    elif header_bytes.startswith(b"OggS"):
        detected_mime = "audio/ogg"
    elif header_bytes.startswith(b"\x1a\x45\xdf\xa3"):
        # EBML header (Matroska / WebM)
        detected_mime = "video/webm"
    elif header_bytes.startswith(b"ID3") or (
        len(header_bytes) >= 2 and header_bytes[0] == 0xFF and (header_bytes[1] & 0xE0) == 0xE0
    ):
        detected_mime = "audio/mpeg"
    elif len(header_bytes) >= 8 and header_bytes[4:8] in {b"ftyp", b"moov", b"wide", b"mdat"}:
        # ISO Base Media File Format (MP4, QuickTime, M4A)
        ftyp_brand = header_bytes[8:12] if len(header_bytes) >= 12 else b""
        if ftyp_brand in {b"qt  ", b"moov"}:
            detected_mime = "video/quicktime"
        elif ftyp_brand in {b"M4A ", b"M4B "}:
            detected_mime = "audio/mp4"
        else:
            detected_mime = "video/mp4"

    # If magic bytes identified a supported format, prioritize it
    chosen_mime = detected_mime

    # If magic bytes could not identify, check if declared MIME matches extension
    if not chosen_mime:
        ext = Path(original_filename).suffix.lower()
        ext_mime = EXTENSION_MIME_MAP.get(ext)
        if ext_mime and declared_mime == ext_mime:
            chosen_mime = ext_mime
        elif declared_mime in ALLOWED_MIME_TYPES:
            chosen_mime = declared_mime
        elif ext_mime:
            chosen_mime = ext_mime

    if not chosen_mime or chosen_mime not in ALLOWED_MIME_TYPES:
        unsupported = declared_mime or chosen_mime or "unknown"
        raise InvalidMimeTypeError(
            mime_type=unsupported,
            allowed_types=sorted(list(ALLOWED_MIME_TYPES)),
        )

    # If client declared a completely mismatched MIME type from magic bytes, reject spoofing
    if declared_mime and detected_mime and declared_mime in ALLOWED_MIME_TYPES:
        # Allow cross-compatibility between video/mp4 and audio/mp4 if ISO BMFF
        is_mp4_family = declared_mime in {"video/mp4", "audio/mp4"} and detected_mime in {"video/mp4", "audio/mp4"}
        if not is_mp4_family and declared_mime != detected_mime:
            raise InvalidAssetError(
                f"MIME type mismatch: declared '{declared_mime}' but file header indicates '{detected_mime}'."
            )

    return chosen_mime
