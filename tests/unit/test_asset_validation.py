"""
Unit tests for asset validation service (filename sanitization, MIME detection, header inspection).
"""

import pytest
from backend.app.core.errors import InvalidAssetError, InvalidMimeTypeError, EmptyFileError
from backend.app.services.validation import (
    sanitize_filename,
    detect_and_validate_mime,
    ALLOWED_MIME_TYPES,
)


def test_sanitize_filename_traversal():
    """Verifies path traversal sequences and drive letters are stripped."""
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename(r"..\..\windows\system32\cmd.exe") == "cmd.exe"
    assert sanitize_filename(r"C:\Users\admin\Documents\secret.png") == "secret.png"
    assert sanitize_filename("/var/log/syslog.log") == "syslog.log"


def test_sanitize_filename_cross_platform_matrix():
    """Verifies mixed, UNC, absolute, and relative traversal patterns across OS conventions."""
    assert sanitize_filename(r"folder/sub\file.jpg") == "file.jpg"
    assert sanitize_filename(r"\\network-share\volume\report.pdf") == "report.pdf"
    assert sanitize_filename("D:data.csv") == "data.csv"
    assert sanitize_filename("/etc/shadow") == "shadow"
    assert sanitize_filename(r"..\..\..\..\..\..\etc\hosts") == "hosts"
    assert sanitize_filename("simple_photo.png") == "simple_photo.png"
    assert sanitize_filename("..\\..\\..\\..\\") == "unnamed_asset"
    assert sanitize_filename("../../../../") == "unnamed_asset"


def test_sanitize_filename_null_byte_and_special_chars():
    """Verifies null bytes and invalid characters are sanitized."""
    assert sanitize_filename("test\x00file.jpg") == "testfile.jpg"
    assert sanitize_filename("my photo [1] (final)*?.png") == "my_photo_1_final_.png"
    assert sanitize_filename("") == "unnamed_asset"
    assert sanitize_filename(None) == "unnamed_asset"
    assert sanitize_filename("...") == "unnamed_asset"


def test_sanitize_filename_excessive_length():
    """Verifies excessive filename lengths are gracefully bounded."""
    long_name = "a" * 300 + ".jpeg"
    sanitized = sanitize_filename(long_name)
    assert len(sanitized) <= 200
    assert sanitized.endswith(".jpeg")


def test_detect_mime_jpeg():
    """Detects JPEG by signature b'\xFF\xD8\xFF'."""
    header = b"\xFF\xD8\xFF\xE0\x00\x10JFIF"
    mime = detect_and_validate_mime(header, "photo.jpg")
    assert mime == "image/jpeg"


def test_detect_mime_png():
    """Detects PNG by signature b'\x89PNG\r\n\x1a\n'."""
    header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    mime = detect_and_validate_mime(header, "photo.png")
    assert mime == "image/png"


def test_detect_mime_webp():
    """Detects WebP by RIFF and WEBP signature."""
    header = b"RIFF\x00\x00\x00\x00WEBPVP8 "
    mime = detect_and_validate_mime(header, "image.webp")
    assert mime == "image/webp"


def test_detect_mime_mp4():
    """Detects MP4 by ISO BMFF ftyp box."""
    header = b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00"
    mime = detect_and_validate_mime(header, "video.mp4")
    assert mime == "video/mp4"


def test_detect_mime_webm():
    """Detects WebM by EBML header."""
    header = b"\x1a\x45\xdf\xa3\x01\x00\x00\x00"
    mime = detect_and_validate_mime(header, "clip.webm")
    assert mime == "video/webm"


def test_detect_mime_wav():
    """Detects WAV by RIFF and WAVE signature."""
    header = b"RIFF\x00\x00\x00\x00WAVEfmt "
    mime = detect_and_validate_mime(header, "audio.wav")
    assert mime == "audio/wav"


def test_detect_mime_mp3():
    """Detects MP3 by ID3 header or sync frame."""
    header_id3 = b"ID3\x04\x00\x00\x00\x00\x00\x00"
    assert detect_and_validate_mime(header_id3, "song.mp3") == "audio/mpeg"

    header_sync = b"\xFF\xFB\x90\x64\x00\x00"
    assert detect_and_validate_mime(header_sync, "song.mp3") == "audio/mpeg"


def test_detect_mime_empty_stream_rejected():
    """Rejects 0-byte header."""
    with pytest.raises(EmptyFileError):
        detect_and_validate_mime(b"", "empty.bin")


def test_reject_executable_binary():
    """Rejects Windows PE (MZ) and Linux ELF binaries."""
    with pytest.raises(InvalidAssetError, match="Executable binary uploads"):
        detect_and_validate_mime(b"MZ\x90\x00\x03\x00", "program.exe")

    with pytest.raises(InvalidAssetError, match="Executable binary uploads"):
        detect_and_validate_mime(b"\x7fELF\x02\x01\x01", "binary.elf")


def test_reject_executable_script():
    """Rejects script payloads."""
    with pytest.raises(InvalidAssetError, match="Script execution uploads"):
        detect_and_validate_mime(b"#!/bin/bash\necho pwned", "script.sh")

    with pytest.raises(InvalidAssetError, match="Script execution uploads"):
        detect_and_validate_mime(b"<?php phpinfo(); ?>", "backdoor.php")


def test_reject_spoofed_header():
    """Rejects when client claims JPEG but sends PNG magic bytes."""
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    with pytest.raises(InvalidAssetError, match="MIME type mismatch"):
        detect_and_validate_mime(png_bytes, "spoofed.jpg", declared_mime="image/jpeg")


def test_reject_unsupported_mime():
    """Rejects random unsupported formats."""
    with pytest.raises(InvalidMimeTypeError):
        detect_and_validate_mime(b"PK\x03\x04\x14\x00", "archive.zip", declared_mime="application/zip")
