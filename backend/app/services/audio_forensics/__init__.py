"""
Audio Forensics Service Package.

Provides forensic analysis detectors for uploaded audio files:
- Container and audio stream metadata extraction
- Spectrogram frequency cutoff & energy distribution analysis
- Pitch (F0) & voice modulation continuity (AI voice cloning indicator)
- Silence & splice discontinuity detection
- C2PA Content Credential verification
"""

from backend.app.services.audio_forensics.analysis import analyze_audio

__all__ = ["analyze_audio"]
