from pathlib import Path
from typing import Any

import cv2
import numpy as np


def detect_copy_move(
    image_path: str | Path, output_dir: str | Path
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    mask_path = output_dir / "copy_move_mask.png"
    heatmap_path = output_dir / "copy_move_heatmap.png"

    encoded = np.fromfile(str(image_path), dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("OpenCV could not decode the uploaded image")

    height, width = image.shape[:2]
    max_dimension = 1600
    resize_scale = min(1.0, max_dimension / max(height, width))
    if resize_scale < 1.0:
        image = cv2.resize(
            image,
            (round(width * resize_scale), round(height * resize_scale)),
            interpolation=cv2.INTER_AREA,
        )

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    detector = cv2.ORB_create(nfeatures=5000)
    keypoints, descriptors = detector.detectAndCompute(gray, None)
    mask = np.zeros(gray.shape, dtype=np.uint8)
    matched_pairs: list[tuple[int, int]] = []
    inlier_count = 0

    if descriptors is not None and len(keypoints) >= 2:
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        neighbor_matches = matcher.knnMatch(descriptors, descriptors, k=2)
        minimum_shift = max(20, round(min(gray.shape) * 0.03))
        for neighbors in neighbor_matches:
            non_self_matches = [
                match for match in neighbors if match.trainIdx != match.queryIdx
            ]
            if not non_self_matches:
                continue
            candidate = non_self_matches[0]
            if candidate.distance > 48:
                continue
            first = np.asarray(keypoints[candidate.queryIdx].pt)
            second = np.asarray(keypoints[candidate.trainIdx].pt)
            if np.linalg.norm(first - second) >= minimum_shift:
                matched_pairs.append((candidate.queryIdx, candidate.trainIdx))

        if len(matched_pairs) >= 8:
            source_points = np.float32(
                [keypoints[first].pt for first, _ in matched_pairs]
            )
            target_points = np.float32(
                [keypoints[second].pt for _, second in matched_pairs]
            )
            _, inliers = cv2.findHomography(
                source_points, target_points, cv2.RANSAC, 4.0
            )
            if inliers is not None:
                inlier_count = int(inliers.sum())
                for is_inlier, (first, second) in zip(inliers.ravel(), matched_pairs):
                    if not is_inlier:
                        continue
                    for point_index in (first, second):
                        x, y = map(round, keypoints[point_index].pt)
                        cv2.circle(mask, (x, y), 12, 255, thickness=-1)

    heatmap = cv2.applyColorMap(mask, cv2.COLORMAP_JET)
    overlay = image.copy()
    marked = mask > 0
    overlay[marked] = cv2.addWeighted(
        image[marked], 0.62, heatmap[marked], 0.38, 0
    )
    cv2.imwrite(str(mask_path), mask)
    cv2.imwrite(str(heatmap_path), overlay)

    return {
        "method": "ORB feature self-matching with RANSAC geometric verification",
        "keypoint_count": len(keypoints),
        "spatially_separated_match_count": len(matched_pairs),
        "geometrically_consistent_match_count": inlier_count,
        "candidate_detected": inlier_count >= 8,
        "interpretation": (
            "Repeated natural textures can produce false matches; a candidate is "
            "not a conclusive finding of copy-move manipulation."
        ),
        "artifact_paths": {
            "mask": str(mask_path.resolve()),
            "heatmap": str(heatmap_path.resolve()),
        },
    }
