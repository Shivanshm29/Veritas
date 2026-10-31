import React from 'react'
import {
  FileText,
  Download,
  PlusCircle,
  Sparkles,
  ShieldAlert,
} from 'lucide-react'
import type { NavPage } from './Sidebar'

interface TopNavProps {
  activePage: NavPage
  investigationId: string
  investigationStatus: string
  onNavigate: (page: NavPage) => void
  onExportReport: () => void
  onExportJson: () => void
}

const PAGE_TITLES: Record<NavPage, { title: string; subtitle: string }> = {
  radar: {
    title: 'Live Social Feed Radar',
    subtitle: 'Mode B: Real-time public stream monitoring & automated early-warning virality tracking',
  },
  ingest: {
    title: 'New Investigation Ingestion',
    subtitle: 'Mode A: Paste social media URL via oEmbed or upload raw image, video, audio evidence',
  },
  image: {
    title: 'Image Forensics Laboratory',
    subtitle: 'Module 5: Metadata analysis, Error Level Analysis (ELA), and ORB keypoint copy-move localization',
  },
  video: {
    title: 'Video Forensics Laboratory',
    subtitle: 'Module 6: Uniform keyframe extraction, inter-frame temporal differencing, and 2D FFT spectral analysis',
  },
  audio: {
    title: 'Audio Forensics Laboratory',
    subtitle: 'Module 7: STFT spectrogram analysis, pitch (F0) continuity, and acoustic splice discontinuity detection',
  },
  provenance: {
    title: 'Media Provenance & Lineage DAG',
    subtitle: 'Module 8: Perceptual pHash matching against historical wire archives and derivation graph verification',
  },
  claims: {
    title: 'Claim Intelligence & Fact Verification',
    subtitle: 'Modules 3 & 4: Atomic proposition decomposition, multi-source retrieval, and NLI stance synthesis',
  },
}

export const TopNav: React.FC<TopNavProps> = ({
  activePage,
  investigationId,
  investigationStatus,
  onNavigate,
  onExportReport,
  onExportJson,
}) => {
  const current = PAGE_TITLES[activePage] || {
    title: 'Investigation Workspace',
    subtitle: 'Multimodal authenticity and evidence platform',
  }

  return (
    <header className="workspace-top-bar">
      <div>
        <h1 className="page-heading">{current.title}</h1>
        <p className="page-subheading">{current.subtitle}</p>
      </div>

      <div className="top-bar-actions">
        {activePage !== 'ingest' && (
          <button
            onClick={() => onNavigate('ingest')}
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem', padding: '0.45rem 0.85rem' }}
          >
            <PlusCircle size={15} />
            <span>New Audit</span>
          </button>
        )}

        <button
          onClick={onExportReport}
          className="btn btn-primary"
          style={{ fontSize: '0.85rem', padding: '0.45rem 0.95rem' }}
        >
          <FileText size={15} />
          <span>Report Dossier</span>
        </button>

        <button
          onClick={onExportJson}
          className="btn btn-secondary"
          style={{ fontSize: '0.85rem', padding: '0.45rem 0.85rem' }}
        >
          <Download size={15} />
          <span>JSON</span>
        </button>
      </div>
    </header>
  )
}
