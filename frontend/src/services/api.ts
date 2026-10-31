import type { AnalysisResponse, ClaimAssessment, HistoricalMatch, ProvenanceData } from '../types'

const BASE_URL = '/api/v1'

export async function analyzeMedia(
  modality: 'image' | 'video' | 'audio',
  file: File
): Promise<AnalysisResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${BASE_URL}/${modality}/analyze`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Analysis failed (${response.status}): ${errorText}`)
  }

  return response.json()
}

export async function fetchHistoricalMatches(phash?: string): Promise<HistoricalMatch[]> {
  const url = phash
    ? `${BASE_URL}/provenance/match?phash=${encodeURIComponent(phash)}`
    : `${BASE_URL}/provenance/references`

  const response = await fetch(url, { method: phash ? 'POST' : 'GET' })
  if (!response.ok) return []

  const data = await response.json()
  return data.matches || data || []
}

// Demo data generator for immediate showcase and testing
export function getDemoInvestigation(): {
  imageAnalysis: AnalysisResponse
  videoAnalysis: AnalysisResponse
  audioAnalysis: AnalysisResponse
  provenance: ProvenanceData
  claims: ClaimAssessment[]
} {
  return {
    imageAnalysis: {
      analysis_id: "inv-img-9f82b1",
      timestamp: new Date().toISOString(),
      status: "completed",
      artifact_paths: {
        "error_level_analysis.heatmap": "artifacts/ela_heatmap.png",
        "copy_move.mask": "artifacts/copy_move_mask.png"
      },
      findings: [
        {
          detector_name: "metadata_analysis",
          status: "completed",
          result_details: {
            filename: "viral_diplomatic_briefing.jpg",
            width: 1920,
            height: 1080,
            format: "JPEG",
            sha256: "b4c2e1f98d023a1b4c9e8f0123456789abcdef0123456789abcdef0123456789",
            file_size_bytes: 482910
          },
          artifact_paths: {},
          limitations: ["EXIF metadata can be stripped during social media upload."]
        },
        {
          detector_name: "error_level_analysis",
          status: "completed",
          result_details: {
            method: "JPEG Recompression Error (ELA)",
            mean_absolute_difference: 4.82,
            maximum_channel_difference: 94,
            interpretation: "Significant high-compression variance detected around central podium figure."
          },
          artifact_paths: { heatmap: "artifacts/ela_heatmap.png" },
          limitations: ["ELA is a visual triage tool, not proof of forgery."]
        },
        {
          detector_name: "copy_move_heuristic",
          status: "completed",
          result_details: {
            method: "ORB Keypoint Self-Matching with RANSAC",
            keypoint_count: 5000,
            geometrically_consistent_match_count: 24,
            candidate_detected: true,
            interpretation: "Repeated geometric cloning cluster detected across crowd background."
          },
          artifact_paths: { mask: "artifacts/copy_move_mask.png" },
          limitations: ["Natural repeated architectural textures may trigger candidate matches."]
        },
        {
          detector_name: "ai_image_classification",
          status: "completed",
          result_details: {
            model: "Organika/sdxl-detector",
            scores: { "human_photograph": 0.12, "artificial_synthetic": 0.88 },
            predicted_label: "artificial_synthetic",
            artificial_class_score: 0.88
          },
          artifact_paths: {},
          limitations: ["Probabilistic indicator trained on diffusion architectures."]
        },
        {
          detector_name: "c2pa_credential_validation",
          status: "not_found",
          result_details: { details: "No cryptographic C2PA manifest found in container." },
          artifact_paths: {},
          limitations: ["Absence of C2PA manifest does not prove manipulation."]
        }
      ]
    },
    videoAnalysis: {
      analysis_id: "inv-vid-53a812",
      timestamp: new Date().toISOString(),
      status: "completed",
      artifact_paths: {
        "temporal_consistency.peak_heatmap": "artifacts/temporal_difference_heatmap.png",
        "spectral_frequency.fft_spectrum": "artifacts/fft_spectral_magnitude.png"
      },
      findings: [
        {
          detector_name: "video_metadata_analysis",
          status: "completed",
          result_details: {
            filename: "speech_broadcast_snippet.mp4",
            resolution: "1280x720",
            fps: 29.97,
            duration_seconds: 14.2,
            fourcc: "H264",
            total_frames: 426
          },
          artifact_paths: {},
          limitations: ["Container FourCC header can be spoofed."]
        },
        {
          detector_name: "keyframe_extraction",
          status: "completed",
          result_details: { extracted_frame_count: 16, sample_frequency: "Uniform 0.85s intervals" },
          artifact_paths: {},
          limitations: ["Single-frame transient edits may fall between keyframe intervals."]
        },
        {
          detector_name: "temporal_consistency_analysis",
          status: "completed",
          result_details: {
            mean_frame_difference: 28.4,
            difference_standard_deviation: 9.61,
            mean_histogram_correlation: 0.68,
            irregular_transition_count: 2,
            interpretation: "Abrupt temporal variance spikes at t=4.2s and t=9.1s indicating possible splicing."
          },
          artifact_paths: { peak_heatmap: "artifacts/temporal_difference_heatmap.png" },
          limitations: ["Sudden intentional camera pans also trigger temporal jumps."]
        },
        {
          detector_name: "deepfake_face_detection",
          status: "completed",
          result_details: {
            faces_detected: 14,
            mean_face_to_background_sharpness_ratio: 3.42,
            suspicious_sharpness_mismatch: true,
            interpretation: "Detected facial region displays abnormal sharpness boundary relative to background neck/collar."
          },
          artifact_paths: {},
          limitations: ["Lens optical depth-of-field can mimic sharpness differences."]
        },
        {
          detector_name: "spectral_frequency_analysis",
          status: "completed",
          result_details: {
            method: "2D Fast Fourier Transform (FFT) Power Spectrum",
            mean_high_frequency_ratio: 0.184,
            interpretation: "Characteristic high-frequency spectral attenuation indicative of generative video vocoder."
          },
          artifact_paths: { spectrum: "artifacts/fft_spectral_magnitude.png" },
          limitations: ["Aggressive streaming bitrate compression naturally suppresses high frequencies."]
        }
      ]
    },
    audioAnalysis: {
      analysis_id: "inv-aud-11c904",
      timestamp: new Date().toISOString(),
      status: "completed",
      artifact_paths: {
        "spectrogram.heatmap": "artifacts/audio_spectrogram.png",
        "splice.energy_contour": "artifacts/energy_contour.png"
      },
      findings: [
        {
          detector_name: "audio_metadata_analysis",
          status: "completed",
          result_details: {
            filename: "intercepted_phone_call.wav",
            sample_rate_hz: 22050,
            channel_layout: "mono",
            bit_depth: 16,
            duration_seconds: 8.4,
            is_common_tts_sample_rate: true
          },
          artifact_paths: {},
          limitations: ["22.05kHz is common for both neural TTS synthesis and low-bandwidth radio codecs."]
        },
        {
          detector_name: "spectrogram_frequency_analysis",
          status: "completed",
          result_details: {
            cutoff_threshold_hz: 8000,
            high_frequency_energy_ratio: 0.00018,
            has_unnatural_high_frequency_cutoff: true,
            interpretation: "Sharp vertical frequency cutoff at 8000 Hz with 0.0 energy above shelf — strong indicator of TTS vocoder band-limiting."
          },
          artifact_paths: { heatmap: "artifacts/audio_spectrogram.png" },
          limitations: ["Landline telephone bandwidth filters also truncate frequencies above 3.4kHz."]
        },
        {
          detector_name: "pitch_and_modulation_analysis",
          status: "completed",
          result_details: {
            mean_pitch_hz: 142.6,
            pitch_standard_deviation: 2.1,
            is_unnaturally_monotone: true,
            interpretation: "Abnormally flat pitch standard deviation (<4 Hz) suggests synthesized robotic voice cloning."
          },
          artifact_paths: {},
          limitations: ["Monotone real human speakers can produce flat F0 contours."]
        },
        {
          detector_name: "splice_and_silence_detection",
          status: "completed",
          result_details: {
            digital_zero_ratio: 0.092,
            has_synthetic_digital_silence: true,
            splice_candidate_count: 3,
            interpretation: "3 spliced transition points detected with interspersed absolute digital silence (0.0 flatlines)."
          },
          artifact_paths: { contour: "artifacts/energy_contour.png" },
          limitations: ["Aggressive noise gates can insert zero frames between words."]
        }
      ]
    },
    provenance: {
      investigation_id: "inv-master-2026",
      is_dag: true,
      cycle_detected: false,
      nodes: [
        { id: "ast_orig_01", type: "ASSET", label: "Broadcast Video (MP4)", metadata: { sha256: "7a8b...1c2" } },
        { id: "ast_keyframe_04", type: "DERIVATION", label: "Keyframe #04 (03.4s)", metadata: { type: "VIDEO_KEYFRAME" } },
        { id: "ast_audio_track", type: "DERIVATION", label: "Extracted Audio Track", metadata: { type: "VIDEO_AUDIO_EXTRACTION" } },
        { id: "ref_ap_news_2020", type: "SOURCE_DOCUMENT", label: "AP News Archival Photo (2020)", metadata: { origin: "Associated Press" } },
        { id: "fnd_image_ela", type: "FORENSIC_FINDING", label: "ELA Compression Anomaly", metadata: { method: "ELA" } },
        { id: "clm_press_claim", type: "CLAIM", label: "Claim: 'Official Resigned Today'", metadata: { verdict: "REFUTED" } }
      ],
      edges: [
        { id: "e1", source: "ast_orig_01", target: "ast_keyframe_04", relationship_type: "DERIVED_FROM", confidence: 1.0, basis: "Deterministic frame extraction at t=3.4s" },
        { id: "e2", source: "ast_orig_01", target: "ast_audio_track", relationship_type: "DERIVED_FROM", confidence: 1.0, basis: "Demuxed audio stream" },
        { id: "e3", source: "ast_keyframe_04", target: "ref_ap_news_2020", relationship_type: "SHARES_PERCEPTUAL_HASH", confidence: 0.94, basis: "Near-duplicate pHash match (Hamming dist 2/64) to 2020 press photo" },
        { id: "e4", source: "ast_keyframe_04", target: "fnd_image_ela", relationship_type: "EVALUATED_BY", confidence: 1.0, basis: "Error Level Analysis inspection" },
        { id: "e5", source: "ast_orig_01", target: "clm_press_claim", relationship_type: "EXTRACTED_FROM", confidence: 0.98, basis: "OCR text banner extraction" }
      ],
      timeline: [
        { timestamp: "2020-11-21T14:30:00Z", event: "Archival Media Publication", entity_id: "ref_ap_news_2020", entity_type: "SOURCE_DOCUMENT", description: "Original uncropped photo published by Associated Press press pool." },
        { timestamp: "2026-10-31T09:00:00Z", event: "Viral Asset Upload", entity_id: "ast_orig_01", entity_type: "ASSET", description: "Target video ingested into PRAMAAN investigation portal." },
        { timestamp: "2026-10-31T09:00:05Z", event: "Multimodal Derivation", entity_id: "ast_keyframe_04", entity_type: "DERIVATION", description: "Extracted 16 keyframes and demuxed audio channel." },
        { timestamp: "2026-10-31T09:00:12Z", event: "Perceptual Match Found", entity_id: "ref_ap_news_2020", entity_type: "SOURCE_DOCUMENT", description: "pHash search identified historical match from 2020 (Hamming dist 2)." }
      ]
    },
    claims: [
      {
        claim_id: "clm-01",
        claim_text: "Prime Minister unexpectedly resigned from office during morning briefing.",
        verdict: "REFUTED",
        confidence_score: 0.96,
        explanation: "Multiple official government gazettes, Reuters wire reports, and verified press pool schedules confirm the official was presiding over parliamentary sessions all morning. No resignation tendered.",
        sources: [
          { title: "Official PMO Daily Bulletin", url: "https://pmo.gov.in/bulletin-2026-10-31", domain: "pmo.gov.in", stance: "REFUTES" },
          { title: "Reuters Wire: Parliament Schedule Update", url: "https://reuters.com/world/parliament-live", domain: "reuters.com", stance: "REFUTES" }
        ]
      },
      {
        claim_id: "clm-02",
        claim_text: "Video footage was recorded live during today's press summit.",
        verdict: "MISLEADING",
        confidence_score: 0.92,
        explanation: "Provenance perceptual hashing proved the visual footage is a cropped re-broadcast of a November 2020 G20 summit briefing, accompanied by an AI voice clone audio track.",
        sources: [
          { title: "AP Archive 2020 G20 Video Library", url: "https://apnews.com/archive/g20-summit-2020", domain: "apnews.com", stance: "REFUTES" }
        ]
      }
    ]
  }
}
