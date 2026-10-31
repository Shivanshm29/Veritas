"""
Video Forensics Service Package.

Provides forensic analysis detectors for uploaded video files:
- Container and stream metadata extraction
- Temporal consistency & optical difference analysis
- Face artifact & boundary blending inconsistency detection
- 2D Spectral/Frequency domain anomaly analysis (AI generator artifacts)
- C2PA Content Credential verification
"""

from backend.app.services.video_forensics.analysis import analyze_video

__all__ = ["analyze_video"]
