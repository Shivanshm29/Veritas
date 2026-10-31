export type ModalityType = 'image' | 'video' | 'audio' | 'claim'

export interface Finding {
  detector_name: string
  status: 'completed' | 'partial' | 'unavailable' | 'error' | 'not_found'
  result_details: Record<string, any>
  artifact_paths: Record<string, string>
  limitations: string[]
}

export interface AnalysisResponse {
  analysis_id: string
  timestamp: string
  status: 'completed' | 'partial' | 'error'
  artifact_paths: Record<string, string>
  findings: Finding[]
}

export interface HistoricalMatch {
  reference_id: string
  title: string
  source_url: string
  publisher?: string
  original_published_date?: string
  hamming_distance: number
  similarity_score: number
  match_grade: 'EXACT' | 'NEAR_DUPLICATE' | 'TENTATIVE_SIMILAR' | 'UNMATCHED'
  basis: string
  is_confirmed_origin: boolean
}

export interface ProvenanceNode {
  id: string
  type: string
  label: string
  timestamp?: string
  metadata?: Record<string, any>
}

export interface ProvenanceEdge {
  id: string
  source: string
  target: string
  relationship_type: string
  confidence: number
  basis: string
}

export interface ProvenanceTimelineEntry {
  timestamp: string
  event: string
  entity_id: string
  entity_type: string
  description: string
}

export interface ProvenanceData {
  investigation_id: string
  is_dag: boolean
  cycle_detected: boolean
  nodes: ProvenanceNode[]
  edges: ProvenanceEdge[]
  timeline: ProvenanceTimelineEntry[]
}

export interface ClaimAssessment {
  claim_id: string
  claim_text: string
  verdict: 'SUPPORTED' | 'REFUTED' | 'MISLEADING' | 'INSUFFICIENT_EVIDENCE'
  confidence_score: number
  explanation: string
  sources: Array<{
    title: string
    url: string
    domain: string
    stance: 'SUPPORTS' | 'REFUTES' | 'NEUTRAL'
  }>
}


export interface FeedItem {
  id: string
  platform: string
  author: string
  author_handle?: string
  title: string
  content: string
  media_url?: string
  media_type: 'image' | 'video' | 'audio' | 'text'
  virality_score: number
  shares_per_minute: number
  total_impressions: number
  is_viral_spike: boolean
  posted_at: string
  source_url: string
  html_embed?: string
}

export interface UnifiedPipelineResponse {
  investigation_id: string
  status: string
  mode: 'URL_AUDIT' | 'LIVE_FEED_RADAR'
  source_url?: string
  source_platform?: string
  post_metadata?: Record<string, any>
  claims: any[]
  claim_assessments: ClaimAssessment[]
  forensic_findings?: AnalysisResponse
  provenance?: {
    fingerprint?: Record<string, any>
    matches_found?: number
    matches?: HistoricalMatch[]
    dag?: {
      nodes: ProvenanceNode[]
      edges: ProvenanceEdge[]
      is_valid_dag: boolean
    }
  }
  verdict_summary: string
  execution_time_ms: number
}
