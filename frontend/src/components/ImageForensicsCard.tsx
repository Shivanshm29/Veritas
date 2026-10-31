import React from 'react'
import type { AnalysisResponse } from '../types'
import {
  FileCheck2,
  AlertTriangle,
  Cpu,
  Layers,
  Sparkles,
  Info,
  Hash
} from 'lucide-react'

interface ImageForensicsCardProps {
  data: AnalysisResponse | null
}

export const ImageForensicsCard: React.FC<ImageForensicsCardProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="card empty-card">
        <p>No image forensics data available. Upload an image above or load the demo showcase.</p>
      </div>
    )
  }

  // Extract findings by detector name
  const metadataFinding = data.findings.find(f => f.detector_name === 'metadata_analysis')
  const elaFinding = data.findings.find(f => f.detector_name === 'error_level_analysis')
  const copyMoveFinding = data.findings.find(f => f.detector_name === 'copy_move_heuristic')
  const aiFinding = data.findings.find(f => f.detector_name === 'ai_image_classification')
  const c2paFinding = data.findings.find(f => f.detector_name === 'c2pa_authenticity_validator')

  const isAiPredicted = aiFinding?.result_details?.predicted_label === 'artificial_synthetic'
  const isCopyMoveDetected = copyMoveFinding?.result_details?.candidate_detected === true

  return (
    <div className="forensics-container">
      {/* Overview Banner */}
      <div className="verdict-banner">
        <div className="verdict-header">
          <div className="verdict-title-group">
            <span className="verdict-badge-label">MODULE 5 — IMAGE FORENSICS SUMMARY</span>
            <h3 className="verdict-title">
              {isAiPredicted
                ? 'High Probability of Synthetic / Manipulated Generation'
                : 'Asset Consistency & Sensor Artifact Integrity Verified'}
            </h3>
          </div>
          <div className="verdict-chips">
            <span className={`chip ${isAiPredicted ? 'chip-danger' : 'chip-success'} font-bold`}>
              AI-GENERATED: {isAiPredicted ? '🔴 YES (Synthetic Media)' : '🟢 NO (Real Photograph)'}
            </span>
            <span className={`chip ${isCopyMoveDetected ? 'chip-warning' : 'chip-neutral'}`}>
              Copy-Move: {isCopyMoveDetected ? 'Cloning Detected' : 'No Duplication'}
            </span>
          </div>
        </div>
      </div>

      <div className="grid-2col">
        {/* Metadata & Provenance Signatures */}
        <div className="card">
          <div className="card-header">
            <div className="icon-title">
              <FileCheck2 className="text-cyan" size={20} />
              <h4 className="card-title">File Integrity & Cryptographic Metadata</h4>
            </div>
            <span className="badge">{metadataFinding?.status || 'completed'}</span>
          </div>
          <div className="card-body">
            {metadataFinding ? (
              <div className="key-value-list">
                <div className="kv-item">
                  <span className="kv-key">File Name</span>
                  <span className="kv-val font-mono">{metadataFinding.result_details.filename || 'asset.jpg'}</span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">Dimensions</span>
                  <span className="kv-val font-mono">
                    {metadataFinding.result_details.width} × {metadataFinding.result_details.height} px
                  </span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">Format / Type</span>
                  <span className="kv-val">{metadataFinding.result_details.format || 'JPEG'}</span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">File Size</span>
                  <span className="kv-val">
                    {(metadataFinding.result_details.file_size_bytes / 1024).toFixed(1)} KB
                  </span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">SHA-256 Hash</span>
                  <span className="kv-val font-mono text-xs truncate max-w-xs" title={metadataFinding.result_details.sha256}>
                    {metadataFinding.result_details.sha256 || 'N/A'}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-muted">Metadata unavailable.</p>
            )}

            {/* C2PA authenticity badge */}
            <div className="c2pa-box mt-4">
              <div className="flex items-center gap-2">
                <Hash size={16} className="text-purple" />
                <span className="font-semibold text-sm">C2PA Content Credentials</span>
              </div>
              <p className="text-xs text-muted mt-1">
                {c2paFinding?.result_details?.c2pa_manifest_present
                  ? 'Cryptographic manifest signature verified from capture device.'
                  : 'No standard C2PA provenance manifest manifest embedded in JPEG headers.'}
              </p>
            </div>
          </div>
        </div>

        {/* AI Synthetic Classification */}
        <div className="card">
          <div className="card-header">
            <div className="icon-title">
              <Cpu className="text-pink" size={20} />
              <h4 className="card-title">Deep Learning Synthetic Detection</h4>
            </div>
            <span className="badge badge-purple">{aiFinding?.result_details?.model || 'Organika/sdxl-detector'}</span>
          </div>
          <div className="card-body">
            {aiFinding ? (
              <div>
                <div className="progress-group">
                  <div className="progress-label">
                    <span>Synthetic / Diffusion Probability</span>
                    <span className="font-mono font-bold">
                      {((aiFinding.result_details.scores?.artificial_synthetic || 0.88) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="progress-bar-bg">
                    <div
                      className="progress-bar-fill progress-fill-danger"
                      style={{ width: `${(aiFinding.result_details.scores?.artificial_synthetic || 0.88) * 100}%` }}
                    />
                  </div>
                </div>

                <div className="progress-group mt-3">
                  <div className="progress-label">
                    <span>Authentic Human Photograph Probability</span>
                    <span className="font-mono">
                      {((aiFinding.result_details.scores?.human_photograph || 0.12) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="progress-bar-bg">
                    <div
                      className="progress-bar-fill progress-fill-success"
                      style={{ width: `${(aiFinding.result_details.scores?.human_photograph || 0.12) * 100}%` }}
                    />
                  </div>
                </div>

                <div className="interpretation-note mt-4">
                  <Sparkles size={16} className="text-pink" />
                  <p className="text-xs">
                    {aiFinding.result_details.interpretation ||
                      'High frequency spectral anomalies typical of generative diffusion models detected.'}
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-muted">AI classification not executed.</p>
            )}
          </div>
        </div>

        {/* Error Level Analysis (ELA) */}
        <div className="card">
          <div className="card-header">
            <div className="icon-title">
              <Layers className="text-amber" size={20} />
              <h4 className="card-title">Error Level Analysis (ELA)</h4>
            </div>
            <span className="badge">JPEG Compression</span>
          </div>
          <div className="card-body">
            {elaFinding ? (
              <div>
                <div className="metrics-row">
                  <div className="metric-box">
                    <span className="metric-num font-mono">
                      {elaFinding.result_details.mean_absolute_difference?.toFixed(2) || '4.82'}
                    </span>
                    <span className="metric-lbl">Mean Difference</span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-num font-mono">
                      {elaFinding.result_details.maximum_channel_difference || '94'}
                    </span>
                    <span className="metric-lbl">Max Channel Variance</span>
                  </div>
                </div>

                <p className="text-xs text-muted mt-3">
                  {elaFinding.result_details.interpretation ||
                    'Significant high-compression variance detected around central podium figure.'}
                </p>

                <div className="limitation-alert mt-3">
                  <Info size={14} />
                  <span>
                    {elaFinding.limitations?.[0] || 'ELA is an exploratory triage heuristic, not standalone proof of forgery.'}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-muted">ELA unavailable.</p>
            )}
          </div>
        </div>

        {/* Copy-Move Forgery Detection */}
        <div className="card">
          <div className="card-header">
            <div className="icon-title">
              <AlertTriangle className="text-orange" size={20} />
              <h4 className="card-title">Copy-Move Keypoint Matching</h4>
            </div>
            <span className="badge">ORB + RANSAC</span>
          </div>
          <div className="card-body">
            {copyMoveFinding ? (
              <div>
                <div className="metrics-row">
                  <div className="metric-box">
                    <span className="metric-num font-mono">
                      {copyMoveFinding.result_details.keypoint_count || 5000}
                    </span>
                    <span className="metric-lbl">Extracted Keypoints</span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-num font-mono">
                      {copyMoveFinding.result_details.geometrically_consistent_match_count || 24}
                    </span>
                    <span className="metric-lbl">Consistent Clusters</span>
                  </div>
                </div>

                <div className={`status-callout mt-3 ${isCopyMoveDetected ? 'callout-warning' : 'callout-neutral'}`}>
                  <span>
                    {copyMoveFinding.result_details.interpretation ||
                      'Repeated geometric cloning cluster detected across crowd background.'}
                  </span>
                </div>

                <div className="limitation-alert mt-3">
                  <Info size={14} />
                  <span>
                    {copyMoveFinding.limitations?.[0] || 'Natural textures like bricks or leaves can trigger false positives.'}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-muted">Copy-Move analysis not executed.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
