import React from 'react'
import { ShieldCheck, FileText, Download, Sparkles } from 'lucide-react'

interface HeaderProps {
  investigationId: string
  status: string
  onLoadDemo: () => void
  onExportReport: () => void
  onExportJson: () => void
}

export const Header: React.FC<HeaderProps> = ({
  investigationId,
  status,
  onLoadDemo,
  onExportReport,
  onExportJson,
}) => {
  return (
    <header className="header-container">
      <div className="header-brand">
        <div className="brand-logo">
          <ShieldCheck className="brand-icon" size={28} />
        </div>
        <div>
          <div className="brand-title">
            <span>PRAMAAN</span>
            <span className="brand-badge">VERITAS CORE</span>
          </div>
          <p className="brand-subtitle">
            Provenance, Reliability & Authenticity Monitoring and Analysis Network
          </p>
        </div>
      </div>

      <div className="header-actions">
        <div className="investigation-pill">
          <span className="dot" />
          <span className="id-label">CASE:</span>
          <span className="id-val">{investigationId}</span>
          <span className="status-tag">{status}</span>
        </div>

        <button onClick={onLoadDemo} className="btn btn-secondary" title="Load full demo investigation with Image, Video, Audio & Provenance">
          <Sparkles size={16} />
          <span>Load Demo Showcase</span>
        </button>

        <button onClick={onExportReport} className="btn btn-primary" title="Generate printable investigation report">
          <FileText size={16} />
          <span>Report</span>
        </button>

        <button onClick={onExportJson} className="btn btn-secondary" title="Download raw JSON evidence dossier">
          <Download size={16} />
          <span>JSON</span>
        </button>
      </div>
    </header>
  )
}
