import React, { useState } from 'react'
import { UploadCloud, Image as ImageIcon, Video, Music, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import type { ModalityType } from '../types'

interface MediaUploaderProps {
  onAnalyze: (modality: ModalityType, file: File) => Promise<void>
  isAnalyzing: boolean
}

export const MediaUploader: React.FC<MediaUploaderProps> = ({ onAnalyze, isAnalyzing }) => {
  const [activeTab, setActiveTab] = useState<ModalityType>('image')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const allowedFormats: Record<ModalityType, string> = {
    image: '.jpg, .jpeg, .png, .webp, .bmp, .tiff',
    video: '.mp4, .mov, .avi, .mkv, .webm',
    audio: '.wav, .mp3, .ogg, .flac, .m4a',
    claim: '.txt, .json'
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

  const handleSubmit = async () => {
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

  return (
    <div className="card uploader-card">
      <div className="card-header">
        <h2 className="card-title">New Investigation Ingestion</h2>
        <span className="card-hint">Module 1 & 5–7 Verification Entry Point</span>
      </div>

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
          onClick={handleSubmit}
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
    </div>
  )
}
