import React from 'react'
import type { ClaimAssessment } from '../types'
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  ExternalLink,
  Quote,
  Search
} from 'lucide-react'

interface ClaimAssessmentCardProps {
  claims: ClaimAssessment[]
}

export const ClaimAssessmentCard: React.FC<ClaimAssessmentCardProps> = ({ claims }) => {
  if (!claims || claims.length === 0) {
    return (
      <div className="card empty-card">
        <p>No claims assessed in this session. Load the demo showcase to view fact verification verdicts.</p>
      </div>
    )
  }

  const getVerdictBadge = (verdict: ClaimAssessment['verdict']) => {
    switch (verdict) {
      case 'SUPPORTED':
        return (
          <span className="verdict-pill verdict-supported">
            <CheckCircle2 size={16} />
            <span>SUPPORTED</span>
          </span>
        )
      case 'REFUTED':
        return (
          <span className="verdict-pill verdict-refuted">
            <XCircle size={16} />
            <span>REFUTED</span>
          </span>
        )
      case 'MISLEADING':
        return (
          <span className="verdict-pill verdict-misleading">
            <AlertTriangle size={16} />
            <span>MISLEADING</span>
          </span>
        )
      case 'INSUFFICIENT_EVIDENCE':
      default:
        return (
          <span className="verdict-pill verdict-insufficient">
            <HelpCircle size={16} />
            <span>INSUFFICIENT EVIDENCE</span>
          </span>
        )
    }
  }

  return (
    <div className="claims-container">
      <div className="verdict-banner">
        <div className="verdict-header">
          <div className="verdict-title-group">
            <span className="verdict-badge-label">MODULE 4 & 9 — CLAIM VERIFICATION ASSESSMENTS</span>
            <h3 className="verdict-title">Evidence-Backed Multimodal Claim Intelligence</h3>
          </div>
          <div className="verdict-chips">
            <span className="chip chip-primary">{claims.length} Claims Evaluated</span>
            <span className="chip chip-neutral">Ground-Truth Fact Retrieval Active</span>
          </div>
        </div>
      </div>

      <div className="claims-grid mt-6">
        {claims.map((claim) => (
          <div key={claim.claim_id} className="claim-card card">
            <div className="claim-card-top">
              <div className="claim-id-badge font-mono text-xs">
                CLAIM ID: {claim.claim_id}
              </div>
              {getVerdictBadge(claim.verdict)}
            </div>

            <div className="claim-statement-box mt-3">
              <Quote size={20} className="quote-icon" />
              <p className="claim-text">{claim.claim_text}</p>
            </div>

            <div className="claim-explanation mt-4">
              <h5 className="section-subtitle">Investigative Synthesis:</h5>
              <p className="explanation-text text-sm text-muted">{claim.explanation}</p>
            </div>

            <div className="claim-confidence mt-3 flex items-center justify-between text-xs">
              <span className="text-muted">Evidence Calibration Confidence:</span>
              <span className="font-mono font-bold text-foreground">
                {(claim.confidence_score * 100).toFixed(0)}%
              </span>
            </div>

            {/* Citations List */}
            <div className="claim-sources mt-4 pt-4 border-t border-border">
              <h5 className="section-subtitle flex items-center gap-2">
                <Search size={14} className="text-cyan" />
                <span>Retrieved Ground-Truth Sources &amp; Stances ({claim.sources.length})</span>
              </h5>

              <div className="sources-list mt-2">
                {claim.sources.map((src, i) => (
                  <div key={i} className="source-item">
                    <div className="source-info">
                      <a
                        href={src.url}
                        target="_blank"
                        rel="noreferrer"
                        className="source-title text-sm hover:underline flex items-center gap-1"
                      >
                        <span>{src.title}</span>
                        <ExternalLink size={12} className="text-muted" />
                      </a>
                      <span className="source-domain text-xs text-muted font-mono">{src.domain}</span>
                    </div>

                    <span
                      className={`source-stance-chip ${src.stance === 'SUPPORTS'
                          ? 'stance-supports'
                          : src.stance === 'REFUTES'
                            ? 'stance-refutes'
                            : 'stance-neutral'
                        }`}
                    >
                      {src.stance}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
