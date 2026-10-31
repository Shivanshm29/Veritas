"""
Image Forensics Service Package.

Provides forensic analysis detectors for uploaded images:
- ELA (Error Level Analysis)
- Copy-Move detection via ORB + RANSAC
- Metadata extraction
- TruFor deep-learning forgery localisation
- AI-image classification
- C2PA content credential validation
"""

from backend.app.services.image_forensics.analysis import analyze_image

__all__ = ["analyze_image"]
