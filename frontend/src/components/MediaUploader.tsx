import React, { useState } from 'react'
import {
  UploadCloud,
  Image as ImageIcon,
  Video,
  Music,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Link2,
  Globe,
  Sparkles,
} from 'lucide-react'
import type { ModalityType } from '../types'

interface MediaUploaderProps {
  onAnalyze: (modality: ModalityType, file: File) => Promise<void>
  onAuditUrl?: (url: string) => Promise<void>
  isAnalyzing: boolean
}

export const MediaUploader: React.FC<MediaUploaderProps> = ({
  onAnalyze,
  onAuditUrl,
  isAnalyzing,
}) => {
  const [ingestionType, setIngestionType] = useState<'file' | 'url'>('file')
  const [activeTab, setActiveTab] = useState<ModalityType>('image')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [urlInput, setUrlInput] = useState<string>('')
  const [dragActive, setDragActive] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const allowedFormats: Record<ModalityType, string> = {
    image: '.jpg, .jpeg, .png, .webp, .bmp, .tiff',
    video: '.mp4, .mov, .avi, .mkv, .webm',
    audio: '.wav, .mp3, .ogg, .flac, .m4a',
    claim: '.txt, .json',
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    else if (e.type === 'dragleave') setDragActive(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0])
      setErrorMsg(null)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
      setErrorMsg(null)
    }
  }

  const handleFileSubmit = async () => {
    if (!selectedFile) {
      setErrorMsg('Please select a file to investigate.')
      return
    }
    setErrorMsg(null)
    try {
      await onAnalyze(activeTab, selectedFile)
    } catch (err: any) {
      setErrorMsg(err.message || 'Analysis request failed.')
    }
  }

  const handleUrlSubmit = async () => {
    if (!urlInput || !urlInput.trim().startsWith('http')) {
      setErrorMsg('Please enter a valid HTTP/HTTPS URL (e.g. from X, Reddit, or YouTube).')
      return
    }
    setErrorMsg(null)
    if (onAuditUrl) {
      try {
        await onAuditUrl(urlInput.trim())
      } catch (err: any) {
        setErrorMsg(err.message || 'URL audit request failed.')
      }
    }
  }

  return (
    <div className="card uploader-card">
      <div className="card-header">
        <div>
          <h2 className="card-title">Investigation Ingestion Gateway</h2>
          <span className="card-hint">Mode A (URL oEmbed) & Direct File Forensics (Modules 1–8)</span>
        </div>

        {/* Ingestion Mode Toggle */}
        <div style={{ display: 'flex', gap: '0.4rem', background: '#0f172a', padding: '0.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <button
            className={`tab-btn ${ingestionType === 'file' ? 'active' : ''}`}
            onClick={() => { setIngestionType('file'); setErrorMsg(null); }}
            style={{ padding: '0.35rem 0.8rem', fontSize: '0.8rem' }}
          >
            <UploadCloud size={15} />
            <span>Direct File Upload</span>
          </button>
          <button
            className={`tab-btn ${ingestionType === 'url' ? 'active' : ''}`}
            onClick={() => { setIngestionType('url'); setErrorMsg(null); }}
            style={{ padding: '0.35rem 0.8rem', fontSize: '0.8rem' }}
          >
            <Link2 size={15} />
            <span>Mode A: Social URL (oEmbed)</span>
          </button>
        </div>
      </div>

      {ingestionType === 'file' ? (
        <>
          <div className="modality-tabs">
            <button
              className={`tab-btn ${activeTab === 'image' ? 'active' : ''}`}
              onClick={() => { setActiveTab('image'); setSelectedFile(null); }}
            >
              <ImageIcon size={18} />
              <span>Image Forensics</span>
            </button>
            <button
              className={`tab-btn ${activeTab === 'video' ? 'active' : ''}`}
              onClick={() => { setActiveTab('video'); setSelectedFile(null); }}
            >
              <Video size={18} />
              <span>Video Forensics</span>
            </button>
            <button
              className={`tab-btn ${activeTab === 'audio' ? 'active' : ''}`}
              onClick={() => { setActiveTab('audio'); setSelectedFile(null); }}
            >
              <Music size={18} />
              <span>Audio Forensics</span>
            </button>
          </div>

          <div
            className={`dropzone ${dragActive ? 'drag-active' : ''} ${selectedFile ? 'has-file' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="file-upload"
              accept={allowedFormats[activeTab]}
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <label htmlFor="file-upload" className="dropzone-label">
              {selectedFile ? (
                <div className="file-selected-box">
                  <CheckCircle2 className="text-emerald" size={36} />
                  <div className="file-info">
                    <span className="file-name">{selectedFile.name}</span>
                    <span className="file-size">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                  <span className="change-hint">Click to change file</span>
                </div>
              ) : (
                <div className="dropzone-empty">
                  <UploadCloud className="upload-icon" size={44} />
                  <p className="dropzone-title">Drop your {activeTab.toUpperCase()} file here, or browse</p>
                  <p className="dropzone-sub">Supported formats: {allowedFormats[activeTab]}</p>
                </div>
              )}
            </label>
          </div>

          {errorMsg && (
            <div className="error-banner">
              <AlertCircle size={18} />
              <span>{errorMsg}</span>
            </div>
          )}

          <div className="uploader-footer">
            <button
              className="btn btn-primary submit-btn"
              disabled={!selectedFile || isAnalyzing}
              onClick={handleFileSubmit}
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="spinner" size={18} />
                  <span>Analyzing Artifacts & Neural Signals...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 size={18} />
                  <span>Run {activeTab.toUpperCase()} Forensic Pipeline</span>
                </>
              )}
            </button>
          </div>
        </>
      ) : (
        /* ── Mode A: URL Ingestion via oEmbed ── */
        <div style={{ padding: '1rem 0' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <label style={{ fontSize: '0.9rem', color: '#cbd5e1', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Globe size={16} color="#60a5fa" />
              <span>Paste Social Media Post, Tweet, or Direct Web Asset URL:</span>
            </label>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="url"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="https://x.com/user/status/... or https://reddit.com/r/... or YouTube link"
                style={{
                  flex: 1,
                  background: '#0f172a',
                  border: '1px solid #334155',
                  color: '#fff',
                  padding: '0.75rem 1rem',
                  borderRadius: '6px',
                  fontSize: '0.95rem',
                }}
              />
              <button
                className="btn btn-primary submit-btn"
                disabled={!urlInput.trim() || isAnalyzing}
                onClick={handleUrlSubmit}
                style={{ minWidth: '180px' }}
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="spinner" size={18} />
                    <span>Resolving oEmbed...</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    <span>Audit with oEmbed</span>
                  </>
                )}
              </button>
            </div>

            {/* Quick Demo Pre-fill Pills */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
              <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Quick Test Links:</span>
              <button
                type="button"
                onClick={() => setUrlInput('https://x.com/WHO/status/1635678901234567890')}
                style={{ background: '#1e293b', border: '1px solid #334155', color: '#94a3b8', borderRadius: '4px', fontSize: '0.75rem', padding: '0.2rem 0.6rem', cursor: 'pointer' }}
              >
                🐦 WHO Press Tweet
              </button>
              <button
                type="button"
                onClick={() => setUrlInput('https://www.youtube.com/watch?v=dQw4w9WgXcQ')}
                style={{ background: '#1e293b', border: '1px solid #334155', color: '#94a3b8', borderRadius: '4px', fontSize: '0.75rem', padding: '0.2rem 0.6rem', cursor: 'pointer' }}
              >
                📺 YouTube Broadcast
              </button>
              <button
                type="button"
                onClick={() => setUrlInput('https://www.reddit.com/r/worldnews/')}
                style={{ background: '#1e293b', border: '1px solid #334155', color: '#94a3b8', borderRadius: '4px', fontSize: '0.75rem', padding: '0.2rem 0.6rem', cursor: 'pointer' }}
              >
                🔴 Reddit News Thread
              </button>
            </div>
          </div>

          {errorMsg && (
            <div className="error-banner" style={{ marginTop: '1rem' }}>
              <AlertCircle size={18} />
              <span>{errorMsg}</span>
            </div>
          )}

          <div style={{ marginTop: '1.25rem', padding: '0.85rem', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '6px', border: '1px solid #334155', fontSize: '0.85rem', color: '#94a3b8' }}>
            <strong style={{ color: '#e2e8f0' }}>How Mode A Works:</strong> The engine queries standard zero-auth oEmbed endpoints (Twitter/X, YouTube, Reddit, TikTok) to extract post claims and thumbnail media. It then executes ELA and CopyMove visual forensics, passes claims to the fact-verification engine, and validates historical provenance DAGs.
          </div>
        </div>
      )}
    </div>
  )
}
