import hashlib
from pathlib import Path
from typing import Any, Union

import cv2
import numpy as np
from PIL import Image


def hamming_distance(hex_hash1: str, hex_hash2: str) -> int:
    """Computes the bitwise Hamming distance between two hex hash strings."""
    try:
        val1 = int(hex_hash1, 16)
        val2 = int(hex_hash2, 16)
        return bin(val1 ^ val2).count("1")
    except (ValueError, TypeError):
        return 64


def compute_ahash(image: np.ndarray, hash_size: int = 8) -> str:
    """
    Average Hash (aHash):
    Resizes image to 8x8, converts to grayscale, and compares each pixel to average value.
    """
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image

    resized = cv2.resize(gray, (hash_size, hash_size), interpolation=cv2.INTER_AREA)
    avg = resized.mean()
    bits = (resized > avg).flatten()
    hex_str = "".join(f"{b:02x}" for b in np.packbits(bits))
    return hex_str


def compute_dhash(image: np.ndarray, hash_size: int = 8) -> str:
    """
    Difference Hash (dHash):
    Resizes to (hash_size+1, hash_size), compares adjacent horizontal pixels.
    Very robust against brightness and contrast scaling.
    """
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image

    resized = cv2.resize(gray, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
    diff = resized[:, 1:] > resized[:, :-1]
    hex_str = "".join(f"{b:02x}" for b in np.packbits(diff.flatten()))
    return hex_str


def compute_phash(image: np.ndarray, hash_size: int = 8, highfreq_factor: int = 4) -> str:
    """
    Perceptual Hash (pHash):
    Resizes to 32x32, applies 2D Discrete Cosine Transform (DCT),
    and compares the top-left low-frequency 8x8 coefficients to their median.
    Highly resistant to minor cropping, scaling, recompression, and color shifting.
    """
    img_size = hash_size * highfreq_factor
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image

    resized = cv2.resize(gray, (img_size, img_size), interpolation=cv2.INTER_AREA).astype(np.float32)
    dct = cv2.dct(resized)

    # Extract 8x8 low-frequency block (excluding [0,0] DC term)
    dct_low = dct[:hash_size, :hash_size]
    med = np.median(dct_low[1:, 1:])
    bits = (dct_low > med).flatten()
    hex_str = "".join(f"{b:02x}" for b in np.packbits(bits))
    return hex_str


def compute_color_fingerprint(image: np.ndarray) -> str:
    """Computes a compact 32-bit color moment fingerprint."""
    if image.ndim == 2:
        return "00000000"
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    h_mean, s_mean, v_mean = hsv.mean(axis=(0, 1))
    h_std, s_std, v_std = hsv.std(axis=(0, 1))
    packed = (
        (int(h_mean) & 0xFF) << 24
        | (int(s_mean) & 0xFF) << 16
        | (int(v_mean) & 0xFF) << 8
        | (int(h_std) & 0xFF)
    )
    return f"{packed:08x}"


def compute_image_fingerprint(image_input: Union[str, Path, bytes, np.ndarray]) -> dict[str, str]:
    """Generates the full perceptual fingerprint suite for an image."""
    if isinstance(image_input, (str, Path)):
        img = cv2.imread(str(image_input))
        if img is None:
            raise ValueError(f"Could not read image from {image_input}")
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    elif isinstance(image_input, bytes):
        nparr = np.frombuffer(image_input, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image bytes")
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    elif isinstance(image_input, np.ndarray):
        img_rgb = image_input if image_input.ndim == 3 else cv2.cvtColor(image_input, cv2.COLOR_GRAY2RGB)
    else:
        raise TypeError("Unsupported image input type")

    return {
        "phash": compute_phash(img_rgb),
        "dhash": compute_dhash(img_rgb),
        "ahash": compute_ahash(img_rgb),
        "color_fingerprint": compute_color_fingerprint(img_rgb),
    }


def compute_video_fingerprints(video_path: Union[str, Path], max_keyframes: int = 8) -> dict[str, Any]:
    """Extracts perceptual fingerprints across sampled video keyframes."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    sampled_hashes: list[str] = []
    first_frame_fingerprint = None

    if frame_count > 0:
        indices = np.linspace(0, frame_count - 1, min(max_keyframes, frame_count), dtype=int)
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if ret and frame is not None:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                ph = compute_phash(rgb)
                sampled_hashes.append(ph)
                if first_frame_fingerprint is None:
                    first_frame_fingerprint = compute_image_fingerprint(rgb)
    cap.release()

    if first_frame_fingerprint is None:
        raise ValueError("Could not extract any valid keyframes from video for fingerprinting")

    return {
        **first_frame_fingerprint,
        "frame_hashes": sampled_hashes,
    }
