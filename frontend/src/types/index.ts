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
