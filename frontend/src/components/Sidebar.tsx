import React from 'react'
import {
  ShieldCheck,
  Radio,
  PlusCircle,
  Image as ImageIcon,
  Video,
  Music,
  Share2,
  FileCheck2,
  Sparkles,
  FileText,
  Download,
  Activity,
  Layers,
  ChevronRight,
} from 'lucide-react'

export type NavPage =
  | 'radar'
  | 'ingest'
  | 'image'
  | 'video'
  | 'audio'
  | 'provenance'
  | 'claims'

interface SidebarProps {
  activePage: NavPage
  onNavigate: (page: NavPage) => void
  investigationId: string
  investigationStatus: string
  hasImage: boolean
  hasVideo: boolean
  hasAudio: boolean
  hasProvenance: boolean
  claimCount: number
  onLoadDemo: () => void
  onExportReport: () => void
  onExportJson: () => void
}

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  onNavigate,
  investigationId,
  investigationStatus,
  hasImage,
  hasVideo,
  hasAudio,
  hasProvenance,
  claimCount,
  onLoadDemo,
  onExportReport,
  onExportJson,
}) => {
  return (
    <aside className="sidebar-container">
      {/* Brand & Platform Header */}
      <div className="sidebar-brand">
        <div className="sidebar-logo">
          <ShieldCheck size={24} className="text-cyan" />
        </div>
        <div className="sidebar-brand-text">
          <div className="brand-title-row">
            <span className="brand-main">PRAMAAN</span>
            <span className="brand-chip">VERITAS</span>
          </div>
          <span className="brand-tagline">Multimodal Forensics & Provenance</span>
        </div>
      </div>

      {/* Active Case Context Card */}
      <div className="case-context-card">
        <div className="case-header">
          <div className="case-status-indicator">
            <span
              className="pulse-dot"
              style={{
                backgroundColor:
                  investigationStatus === 'COMPLETED'
                    ? '#10b981'
                    : investigationStatus === 'ANALYZING'
                    ? '#f59e0b'
                    : '#06b6d4',
              }}
            />
            <span className="case-status-text">{investigationStatus}</span>
          </div>
          <span className="case-badge">CASE ID</span>
        </div>
        <div className="case-id-display" title={investigationId}>
          {investigationId}
        </div>
      </div>

      {/* Navigation Sections */}
      <nav className="sidebar-nav">
        {/* Group 1: Surveillance & Intake */}
        <div className="nav-group-label">SURVEILLANCE &amp; INGESTION</div>

        <button
          className={`nav-item ${activePage === 'radar' ? 'active' : ''}`}
          onClick={() => onNavigate('radar')}
        >
          <div className="nav-icon-label">
            <Radio size={18} className="nav-icon text-emerald" />
            <span>Live Feed Radar</span>
          </div>
          <span className="live-chip">LIVE</span>
        </button>

        <button
          className={`nav-item ${activePage === 'ingest' ? 'active' : ''}`}
          onClick={() => onNavigate('ingest')}
        >
          <div className="nav-icon-label">
            <PlusCircle size={18} className="nav-icon text-cyan" />
            <span>New Investigation</span>
          </div>
          <span className="mode-chip">Mode A</span>
        </button>

        {/* Group 2: Forensic Analysis Labs */}
        <div className="nav-group-label">FORENSIC LABS</div>

        <button
          className={`nav-item ${activePage === 'image' ? 'active' : ''}`}
          onClick={() => onNavigate('image')}
        >
          <div className="nav-icon-label">
            <ImageIcon size={18} className="nav-icon text-purple" />
            <span>Image Forensics</span>
          </div>
          {hasImage && <span className="status-dot-active" title="Analysis available" />}
        </button>

        <button
          className={`nav-item ${activePage === 'video' ? 'active' : ''}`}
          onClick={() => onNavigate('video')}
        >
          <div className="nav-icon-label">
            <Video size={18} className="nav-icon text-amber" />
            <span>Video Forensics</span>
          </div>
          {hasVideo && <span className="status-dot-active" title="Analysis available" />}
        </button>

        <button
          className={`nav-item ${activePage === 'audio' ? 'active' : ''}`}
          onClick={() => onNavigate('audio')}
        >
          <div className="nav-icon-label">
            <Music size={18} className="nav-icon text-pink" />
            <span>Audio Forensics</span>
          </div>
          {hasAudio && <span className="status-dot-active" title="Analysis available" />}
        </button>

        {/* Group 3: Intelligence & Verification */}
        <div className="nav-group-label">EVIDENCE &amp; PROVENANCE</div>

        <button
          className={`nav-item ${activePage === 'provenance' ? 'active' : ''}`}
          onClick={() => onNavigate('provenance')}
        >
          <div className="nav-icon-label">
            <Share2 size={18} className="nav-icon text-cyan" />
            <span>Provenance DAG</span>
          </div>
          {hasProvenance && <span className="status-dot-active" title="Lineage built" />}
        </button>

        <button
          className={`nav-item ${activePage === 'claims' ? 'active' : ''}`}
          onClick={() => onNavigate('claims')}
        >
          <div className="nav-icon-label">
            <FileCheck2 size={18} className="nav-icon text-emerald" />
            <span>Claim Verification</span>
          </div>
          {claimCount > 0 ? (
            <span className="count-badge">{claimCount}</span>
          ) : null}
        </button>
      </nav>

      {/* Sidebar Quick Actions & Footer */}
      <div className="sidebar-footer">
        <button onClick={onLoadDemo} className="sidebar-action-btn btn-demo" title="Load full demo showcase with sample case data">
          <Sparkles size={16} />
          <span>Load Demo Showcase</span>
        </button>

        <div className="footer-button-row">
          <button onClick={onExportReport} className="sidebar-action-btn btn-report" title="Generate printable investigation report">
            <FileText size={15} />
            <span>Report</span>
          </button>

          <button onClick={onExportJson} className="sidebar-action-btn btn-json" title="Download raw JSON evidence dossier">
            <Download size={15} />
            <span>JSON</span>
          </button>
        </div>

        <div className="engine-health-status">
          <span className="health-dot" />
          <span>PRAMAAN Engine v0.1.0 • Ready</span>
        </div>
      </div>
    </aside>
  )
}
