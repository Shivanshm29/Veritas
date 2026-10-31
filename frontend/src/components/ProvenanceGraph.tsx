import React from 'react'
import type { ProvenanceData, HistoricalMatch } from '../types'
import {
  Clock,
  ExternalLink,
  Share2,
  ArrowRight,
  Database
} from 'lucide-react'

interface ProvenanceGraphProps {
  data: ProvenanceData | null
  matches?: HistoricalMatch[]
}

export const ProvenanceGraph: React.FC<ProvenanceGraphProps> = ({ data, matches = [] }) => {
  if (!data) {
    return (
      <div className="card empty-card">
        <p>No provenance graph data available. Load the demo showcase to inspect the provenance DAG.</p>
      </div>
    )
  }

  // Pre-configured historical mock matches if none provided
  const historicalMatches: HistoricalMatch[] = matches.length > 0 ? matches : [
    {
      reference_id: "ref-2018-reuters-009",
      title: "G20 Bilateral Press Conference in Buenos Aires",
      source_url: "https://www.reuters.com/archive/2018/12/01/g20-summit-briefing",
      publisher: "Reuters Archives",
      original_published_date: "2018-12-01T14:30:00Z",
      hamming_distance: 3,
      similarity_score: 0.953,
      match_grade: "NEAR_DUPLICATE",
      basis: "pHash 64-bit DCT distance <= 5 and color moment coherence",
      is_confirmed_origin: true
    },
    {
      reference_id: "ref-2021-getty-4412",
      title: "UN Geneva Diplomatic Summit Podium Archive",
      source_url: "https://www.gettyimages.com/detail/news-photo/un-geneva-summit",
      publisher: "Getty Images Editorial",
      original_published_date: "2021-06-15T09:15:00Z",
      hamming_distance: 10,
      similarity_score: 0.843,
      match_grade: "TENTATIVE_SIMILAR",
      basis: "Perceptual hash match in exploratory threshold (Hamming 6-12)",
      is_confirmed_origin: false
    }
  ]

  return (
    <div className="forensics-container">
      {/* Overview Banner */}
      <div className="verdict-banner">
        <div className="verdict-header">
          <div className="verdict-title-group">
            <span className="verdict-badge-label">MODULE 8 — PROVENANCE & HISTORICAL MEDIA MATCHING</span>
            <h3 className="verdict-title">
              Historical Reference Discovered: Out-of-Context Misattribution
            </h3>
          </div>
          <div className="verdict-chips">
            <span className="chip chip-success">
              DAG Directed Acyclic: {data.is_dag ? 'Valid (No Cycles)' : 'Cycle Detected'}
            </span>
            <span className="chip chip-primary">
              Historical Matches: {historicalMatches.length} Found
            </span>
          </div>
        </div>
      </div>

      {/* Historical Media Matches Section */}
      <div className="card mb-6">
        <div className="card-header">
          <div className="icon-title">
            <Database className="text-cyan" size={20} />
            <h4 className="card-title">Archival Reference Database Search (pHash Hamming &lt; 12)</h4>
          </div>
          <span className="badge badge-purple">Historical Prior Art</span>
        </div>
        <div className="card-body">
          <p className="text-sm text-muted mb-4">
            Perceptual fingerprints (pHash, dHash, aHash) were queried against the archival reference database.
            Confirmed origins are strictly separated from tentative similarity matches.
          </p>

          <div className="reference-list">
            {historicalMatches.map((match, idx) => (
              <div
                key={idx}
                className={`reference-card ${match.is_confirmed_origin ? 'reference-confirmed' : 'reference-tentative'}`}
              >
                <div className="ref-top">
                  <div className="ref-badge-group">
                    <span
                      className={`chip ${match.match_grade === 'EXACT' || match.match_grade === 'NEAR_DUPLICATE'
                        ? 'chip-danger'
                        : 'chip-warning'
                        }`}
                    >
                      {match.match_grade}
                    </span>
                    {match.is_confirmed_origin && (
                      <span className="chip chip-purple">CONFIRMED ORIGIN</span>
                    )}
                  </div>
                  <span className="font-mono text-xs text-muted">
                    Hamming Dist: <strong className="text-foreground">{match.hamming_distance}</strong> / 64 ({(match.similarity_score * 100).toFixed(1)}% match)
                  </span>
                </div>

                <h5 className="ref-title mt-2 font-semibold text-foreground">{match.title}</h5>

                <div className="ref-meta mt-2 flex flex-wrap gap-4 text-xs text-muted">
                  <span>Publisher: <strong className="text-foreground">{match.publisher || 'Unknown'}</strong></span>
                  <span>Date: <strong className="text-foreground">
                    {match.original_published_date ? new Date(match.original_published_date).toLocaleDateString() : 'N/A'}
                  </strong></span>
                </div>

                <div className="ref-basis mt-3 p-2 bg-secondary rounded text-xs">
                  <strong>Verification Basis: </strong>
                  <span>{match.basis}</span>
                </div>

                <div className="ref-footer mt-3 flex justify-between items-center text-xs">
                  <span className="text-muted">Ref ID: {match.reference_id}</span>
                  <a
                    href={match.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-cyan hover:underline"
                  >
                    <span>View Archival Record</span>
                    <ExternalLink size={12} />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid-2col">
        {/* Visual DAG Graph Representation */}
        <div className="card">
          <div className="card-header">
            <div className="icon-title">
              <Share2 className="text-pink" size={20} />
              <h4 className="card-title">Provenance Graph (DAG Lineage)</h4>
            </div>
            <span className="badge">DFS Validated</span>
          </div>
          <div className="card-body">
            <div className="dag-container">
              {data.nodes.map((node, i) => {
                const outgoingEdges = data.edges.filter(e => e.source === node.id)
                return (
                  <div key={node.id} className="dag-node-wrapper">
                    <div className="dag-node">
                      <div className="dag-node-header">
                        <span className="node-type">{node.type}</span>
                        {node.timestamp && (
                          <span className="node-time">
                            {new Date(node.timestamp).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      <div className="node-label font-medium">{node.label}</div>
                      <div className="node-id font-mono text-xs text-muted truncate">{node.id}</div>
                    </div>

                    {outgoingEdges.length > 0 && (
                      <div className="dag-edge-connector">
                        {outgoingEdges.map(edge => (
                          <div key={edge.id} className="edge-item">
                            <ArrowRight size={14} className="text-cyan" />
                            <span className="edge-label">{edge.relationship_type}</span>
                            <span className="edge-conf font-mono">({(edge.confidence * 100).toFixed(0)}%)</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Provenance Chronological Timeline */}
        <div className="card">
          <div className="card-header">
            <div className="icon-title">
              <Clock className="text-amber" size={20} />
              <h4 className="card-title">Chronological Investigation Timeline</h4>
            </div>
            <span className="badge">{data.timeline.length} Events</span>
          </div>
          <div className="card-body">
            <div className="timeline-container">
              {data.timeline.map((entry, idx) => (
                <div key={idx} className="timeline-row">
                  <div className="timeline-marker">
                    <div className="timeline-dot" />
                    {idx < data.timeline.length - 1 && <div className="timeline-line" />}
                  </div>
                  <div className="timeline-content">
                    <div className="timeline-time font-mono">
                      {new Date(entry.timestamp).toLocaleString()}
                    </div>
                    <div className="timeline-event-name font-semibold">{entry.event}</div>
                    <p className="timeline-desc text-xs text-muted mt-1">{entry.description}</p>
                    <div className="timeline-tag font-mono mt-1">
                      {entry.entity_type}: {entry.entity_id}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
