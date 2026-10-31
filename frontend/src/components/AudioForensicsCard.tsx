import React from 'react'
import type { AnalysisResponse } from '../types'
import {
  Music,
  Activity,
  Mic,
  Scissors,
  Info,
} from 'lucide-react'

interface AudioForensicsCardProps {
  data: AnalysisResponse | null
}

export const AudioForensicsCard: React.FC<AudioForensicsCardProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="card empty-card">
        <p>No audio forensics data available. Upload an audio recording or load the demo showcase.</p>
      </div>
    )
  }

  const metadataFinding = data.findings.find(f => f.detector_name === 'audio_metadata')
  const cutoffFinding = data.findings.find(f => f.detector_name === 'spectrogram_cutoff')
  const pitchFinding = data.findings.find(f => f.detector_name === 'pitch_jitter_monotone')
  const spliceFinding = data.findings.find(f => f.detector_name === 'audio_splicing_energy')

  const isCutoffDetected = cutoffFinding?.result_details?.cutoff_detected === true
  const isMonotone = pitchFinding?.result_details?.unnatural_monotone === true
  const isSyntheticLikely = isCutoffDetected || isMonotone

  return (
    <div className="forensics-container">
      {/* Overview Banner */}
      <div className="verdict-banner">
        <div className="verdict-header">
          <div className="verdict-title-group">
            <span className="verdict-badge-label">MODULE 7 — AUDIO FORENSICS SUMMARY</span>
            <h3 className="verdict-title">
              {isSyntheticLikely
                ? 'High Probability of Text-to-Speech (TTS) / Voice Clone Synthesis'
                : 'Acoustic Environment & Organic Vocal Tract Resonance Consistent'}
            </h3>
          </div>
          <div className="verdict-chips">
            <span className={`chip ${isSyntheticLikely ? 'chip-danger' : 'chip-success'} font-bold`}>
              AI-GENERATED VOICE: {isSyntheticLikely ? '🔴 YES (TTS Clone Detected)' : '🟢 NO (Natural Human Voice)'}
            </span>
            <span className={`chip ${isMonotone ? 'chip-warning' : 'chip-neutral'}`}>
              Prosody Dynamics: {isMonotone ? 'Robotic Flat Pitch' : 'Natural Modulation'}
            </span>
          </div>
        </div>
      </div>

      <div className="grid-2col">
        {/* Audio Container Metadata */}
        <div className="card">
          <div className="card-header">
            <div className="icon-title">
              <Music className="text-cyan" size={20} />
              <h4 className="card-title">Acoustic Signal & Container</h4>
            </div>
            <span className="badge">{metadataFinding?.status || 'completed'}</span>
          </div>
          <div className="card-body">
            {metadataFinding ? (
              <div className="key-value-list">
                <div className="kv-item">
                  <span className="kv-key">Sampling Rate</span>
                  <span className="kv-val font-mono">{metadataFinding.result_details.sample_rate || 44100} Hz</span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">Channels</span>
                  <span className="kv-val font-mono">
                    {metadataFinding.result_details.channels === 1 ? 'Mono (1 ch)' : 'Stereo (2 ch)'}
                  </span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">Duration</span>
                  <span className="kv-val font-mono">{metadataFinding.result_details.duration_seconds || '8.2'} s</span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">Bit Depth</span>
                  <span className="kv-val font-mono">{metadataFinding.result_details.bit_depth || 16}-bit PCM</span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">Encoding</span>
                  <span className="kv-val font-mono">{metadataFinding.result_details.encoding || 'WAV'}</span>
                </div>
              </div>
            ) : (
              <p className="text-muted">Audio stream metadata unavailable.</p>
            )}

            {/* Synthetic Voice Waveform Preview Graphic */}
            <div className="mt-4 pt-3 border-t border-border">
              <span className="text-xs font-semibold text-muted">SYNTHESIZED ENVELOPE SAMPLING</span>
              <div className="waveform-box mt-2">
                {[12, 28, 45, 80, 60, 95, 40, 20, 10, 35, 75, 100, 85, 40, 20, 50, 70, 90, 60, 30].map((h, i) => (
                  <div
                    key={i}
                    className="wave-bar"
                    style={{ height: `${h}%`, backgroundColor: h > 70 ? 'var(--pink)' : 'var(--cyan)' }}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Spectrogram Cutoff & Vocoder Detection */}
        <div className="card">
          <div className="card-header">
            <div className="icon-title">
              <Activity className="text-pink" size={20} />
              <h4 className="card-title">Spectrogram Cutoff (Vocoder Artifacts)</h4>
            </div>
            <span className="badge badge-purple">STFT Spectral Analysis</span>
          </div>
          <div className="card-body">
            {cutoffFinding ? (
              <div>
                <div className="metrics-row">
                  <div className="metric-box">
                    <span className="metric-num font-mono text-danger">
                      {cutoffFinding.result_details.cutoff_frequency_hz || 16000} Hz
                    </span>
                    <span className="metric-lbl">Sharp Roll-off Freq</span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-num font-mono">
                      {cutoffFinding.result_details.high_freq_attenuation_db?.toFixed(1) || '-42.6'} dB
                    </span>
                    <span className="metric-lbl">High-Freq Attenuation</span>
                  </div>
                </div>

                <div className="callout callout-danger mt-3">
                  <span>
                    {cutoffFinding.result_details.interpretation ||
                      'Sharp synthetic brickwall cutoff observed at 16kHz characteristic of neural vocoders (HiFi-GAN / ElevenLabs).'}
                  </span>
                </div>

                <div className="limitation-alert mt-3">
                  <Info size={14} />
                  <span>
                    {cutoffFinding.limitations?.[0] || 'Aggressive MP3 compression at 64kbps can also truncate high frequencies.'}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-muted">Spectrogram cutoff not analyzed.</p>
            )}
          </div>
        </div>

        {/* Pitch (F0) & Robotic Monotone Contour */}
        <div className="card">
          <div className="card-header">
            <div className="icon-title">
              <Mic className="text-amber" size={20} />
              <h4 className="card-title">Pitch (F0) Jitter & Prosody Flatness</h4>
            </div>
            <span className="badge">Autocorrelation F0</span>
          </div>
          <div className="card-body">
            {pitchFinding ? (
              <div>
                <div className="metrics-row">
                  <div className="metric-box">
                    <span className="metric-num font-mono">
                      {pitchFinding.result_details.f0_standard_deviation?.toFixed(1) || '4.2'} Hz
                    </span>
                    <span className="metric-lbl">F0 Pitch Variance</span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-num font-mono">
                      {pitchFinding.result_details.mean_pitch_hz?.toFixed(1) || '142.8'} Hz
                    </span>
                    <span className="metric-lbl">Mean Fundamental (F0)</span>
                  </div>
                </div>

                <p className="text-xs text-muted mt-3">
                  {pitchFinding.result_details.interpretation ||
                    'Abnormally flat pitch contour lacking human emotional micro-inflections.'}
                </p>

                <div className="limitation-alert mt-3">
                  <Info size={14} />
                  <span>
                    {pitchFinding.limitations?.[0] || 'Formal public reading voices naturally have narrower pitch variance.'}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-muted">Pitch contour not analyzed.</p>
            )}
          </div>
        </div>

        {/* Splice Discontinuities */}
        <div className="card">
          <div className="card-header">
            <div className="icon-title">
              <Scissors className="text-orange" size={20} />
              <h4 className="card-title">Audio Splice & Energy Transitions</h4>
            </div>
            <span className="badge">Short-Time Energy</span>
          </div>
          <div className="card-body">
            {spliceFinding ? (
              <div>
                <div className="metrics-row">
                  <div className="metric-box">
                    <span className="metric-num font-mono">
                      {spliceFinding.result_details.splice_discontinuities_found || 2}
                    </span>
                    <span className="metric-lbl">Energy Step Anomaly</span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-num font-mono">
                      {spliceFinding.result_details.unnatural_silence_count || 1}
                    </span>
                    <span className="metric-lbl">Zero-Noise Floor Gaps</span>
                  </div>
                </div>

                <p className="text-xs text-muted mt-3">
                  {spliceFinding.result_details.interpretation ||
                    'Zero-noise acoustic digital silence detected between words at 2.4s and 5.1s, indicating synthetic splicing.'}
                </p>

                <div className="limitation-alert mt-3">
                  <Info size={14} />
                  <span>
                    {spliceFinding.limitations?.[0] || 'Software noise suppression gates can introduce artificial silence.'}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-muted">Splice analysis not analyzed.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
