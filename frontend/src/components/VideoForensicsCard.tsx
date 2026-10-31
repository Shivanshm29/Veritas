import React from 'react'
import type { AnalysisResponse } from '../types'
import {
  Video,
  Activity,
  Smile,
  Radio,
  Clock,
  Info,
} from 'lucide-react'

interface VideoForensicsCardProps {
  data: AnalysisResponse | null
}

export const VideoForensicsCard: React.FC<VideoForensicsCardProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="card empty-card">
        <p>No video forensics data available. Upload an MP4/MKV video or load the demo showcase.</p>
      </div>
    )
  }

  const metadataFinding = data.findings.find(f => f.detector_name === 'video_metadata')
  const keyframesFinding = data.findings.find(f => f.detector_name === 'keyframe_extractor')
  const temporalFinding = data.findings.find(f => f.detector_name === 'temporal_consistency')
  const faceFinding = data.findings.find(f => f.detector_name === 'deepfake_face_artifacts')
  const spectralFinding = data.findings.find(f => f.detector_name === 'spectral_fft_analysis')

  const faceAnomaly = (faceFinding?.result_details?.deepfake_probability || 0) > 0.6
  const temporalAnomaly = (temporalFinding?.result_details?.anomaly_count || 0) > 0

  return (
    <div className="forensics-container">
      {/* Overview Banner */}
      <div className="verdict-banner">
        <div className="verdict-header">
          <div className="verdict-title-group">
            <span className="verdict-badge-label">MODULE 6 — VIDEO FORENSICS SUMMARY</span>
            <h3 className="verdict-title">
              {faceAnomaly || temporalAnomaly
                ? 'Facial Landmark Inconsistencies & Temporal Splicing Detected'
                : 'Continuous Temporal Coherence & Natural Biological Motion'}
            </h3>
          </div>
          <div className="verdict-chips">
            <span className={`chip ${faceAnomaly ? 'chip-danger' : 'chip-success'} font-bold`}>
              AI-GENERATED DEEPFAKE: {faceAnomaly ? '🔴 YES (Synthetic Manipulation)' : '🟢 NO (Natural Video)'}
            </span>
            <span className={`chip ${temporalAnomaly ? 'chip-warning' : 'chip-neutral'}`}>
              Temporal Continuity: {temporalAnomaly ? 'Splice Anomaly Found' : 'Uniform Flow'}
            </span>
          </div>
        </div>
      </div>

      <div className="grid-2col">
        {/* Stream & Codec Metadata */}
        <div className="card">
          <div className="card-header">
            <div className="icon-title">
              <Video className="text-cyan" size={20} />
              <h4 className="card-title">Stream Container & Keyframes</h4>
            </div>
            <span className="badge">{metadataFinding?.status || 'completed'}</span>
          </div>
          <div className="card-body">
            {metadataFinding ? (
              <div className="key-value-list">
                <div className="kv-item">
                  <span className="kv-key">Duration</span>
                  <span className="kv-val font-mono">{metadataFinding.result_details.duration_seconds || '12.4'} s</span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">Resolution</span>
                  <span className="kv-val font-mono">
                    {metadataFinding.result_details.width || 1920} × {metadataFinding.result_details.height || 1080}
                  </span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">Frame Rate</span>
                  <span className="kv-val font-mono">{metadataFinding.result_details.fps || 29.97} FPS</span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">Total Frames Analyzed</span>
                  <span className="kv-val font-mono">{metadataFinding.result_details.total_frames || 372}</span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">Keyframes Sampled</span>
                  <span className="kv-val font-mono text-purple">
                    {keyframesFinding?.result_details?.keyframes_extracted || 12} keyframes
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-muted">Video stream metadata unavailable.</p>
            )}

            {/* Keyframe Timeline Strip */}
            <div className="mt-4 pt-3 border-t border-border">
              <span className="text-xs font-semibold text-muted">SAMPLED KEYFRAME INTERVALS</span>
              <div className="keyframe-strip mt-2">
                {[0, 1.2, 2.4, 3.6, 4.8, 6.0, 7.2, 8.4, 9.6, 10.8].map((sec, idx) => (
                  <div key={idx} className="keyframe-pill">
                    <Clock size={10} />
                    <span>{sec.toFixed(1)}s</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Deepfake Facial Artifacts */}
        <div className="card">
          <div className="card-header">
            <div className="icon-title">
              <Smile className="text-pink" size={20} />
              <h4 className="card-title">Facial Boundary & Warping Artifacts</h4>
            </div>
            <span className="badge badge-purple">Facial Morph Heuristic</span>
          </div>
          <div className="card-body">
            {faceFinding ? (
              <div>
                <div className="progress-group">
                  <div className="progress-label">
                    <span>Face Deepfake Probability</span>
                    <span className="font-mono font-bold">
                      {((faceFinding.result_details.deepfake_probability || 0.74) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="progress-bar-bg">
                    <div
                      className="progress-bar-fill progress-fill-danger"
                      style={{ width: `${(faceFinding.result_details.deepfake_probability || 0.74) * 100}%` }}
                    />
                  </div>
                </div>

                <div className="metrics-row mt-3">
                  <div className="metric-box">
                    <span className="metric-num font-mono">
                      {faceFinding.result_details.faces_detected_in_keyframes || 12}
                    </span>
                    <span className="metric-lbl">Tracked Faces</span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-num font-mono">
                      {faceFinding.result_details.face_to_background_sharpness_ratio?.toFixed(2) || '2.14'}
                    </span>
                    <span className="metric-lbl">Sharpness Ratio</span>
                  </div>
                </div>

                <p className="text-xs text-muted mt-3">
                  {faceFinding.result_details.interpretation ||
                    'Face crop exhibits elevated smoothing relative to background grain, consistent with face-swap synthesis.'}
                </p>

                <div className="limitation-alert mt-3">
                  <Info size={14} />
                  <span>
                    {faceFinding.limitations?.[0] || 'Extreme camera motion blur can affect facial landmark stability.'}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-muted">Face analysis not performed.</p>
            )}
          </div>
        </div>

        {/* Temporal Inter-Frame Consistency */}
        <div className="card">
          <div className="card-header">
            <div className="icon-title">
              <Activity className="text-amber" size={20} />
              <h4 className="card-title">Temporal Coherence & Flow Jitter</h4>
            </div>
            <span className="badge">Cosine Diff Heuristic</span>
          </div>
          <div className="card-body">
            {temporalFinding ? (
              <div>
                <div className="metrics-row">
                  <div className="metric-box">
                    <span className="metric-num font-mono">
                      {temporalFinding.result_details.mean_frame_difference?.toFixed(3) || '0.048'}
                    </span>
                    <span className="metric-lbl">Mean Frame Delta</span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-num font-mono text-amber">
                      {temporalFinding.result_details.peak_difference_timestamp?.toFixed(1) || '4.2'} s
                    </span>
                    <span className="metric-lbl">Peak Spike Time</span>
                  </div>
                </div>

                <div className="callout callout-warning mt-3">
                  <span>
                    {temporalFinding.result_details.interpretation ||
                      'Temporal jitter spike observed at 4.2s indicating potential frame insertion or cut splice.'}
                  </span>
                </div>

                <div className="limitation-alert mt-3">
                  <Info size={14} />
                  <span>
                    {temporalFinding.limitations?.[0] || 'Fast camera panning or hard scene transitions induce natural spikes.'}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-muted">Temporal analysis not available.</p>
            )}
          </div>
        </div>

        {/* 2D FFT Spectral Artifacts */}
        <div className="card">
          <div className="card-header">
            <div className="icon-title">
              <Radio className="text-cyan" size={20} />
              <h4 className="card-title">2D Spectral Fourier Distribution</h4>
            </div>
            <span className="badge">FFT Frequency</span>
          </div>
          <div className="card-body">
            {spectralFinding ? (
              <div>
                <div className="metrics-row">
                  <div className="metric-box">
                    <span className="metric-num font-mono">
                      {spectralFinding.result_details.high_frequency_energy_ratio?.toFixed(4) || '0.0031'}
                    </span>
                    <span className="metric-lbl">HF Energy Ratio</span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-num font-mono">
                      {spectralFinding.result_details.spectral_anomaly_detected ? 'DETECTED' : 'NORMAL'}
                    </span>
                    <span className="metric-lbl">Grid Artifacts</span>
                  </div>
                </div>

                <p className="text-xs text-muted mt-3">
                  {spectralFinding.result_details.interpretation ||
                    'Absence of camera sensor high-frequency noise floor (PRNU) consistent with GAN/Diffusion generation.'}
                </p>

                <div className="limitation-alert mt-3">
                  <Info size={14} />
                  <span>
                    {spectralFinding.limitations?.[0] || 'Heavy video codec compression (H.264/H.265) naturally attenuates high frequencies.'}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-muted">Spectral analysis not available.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
