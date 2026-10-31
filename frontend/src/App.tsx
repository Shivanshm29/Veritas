import { useState } from 'react'
import { Header } from './components/Header'
import { MediaUploader } from './components/MediaUploader'
import { ImageForensicsCard } from './components/ImageForensicsCard'
import { VideoForensicsCard } from './components/VideoForensicsCard'
import { AudioForensicsCard } from './components/AudioForensicsCard'
import { ProvenanceGraph } from './components/ProvenanceGraph'
import { ClaimAssessmentCard } from './components/ClaimAssessmentCard'
import { InvestigationReportModal } from './components/InvestigationReportModal'
import { analyzeMedia, getDemoInvestigation } from './services/api'
import type { AnalysisResponse, ClaimAssessment, ModalityType, ProvenanceData } from './types'
import {
  Image as ImageIcon,
  Video,
  Music,
  Share2,
  FileCheck2,
} from 'lucide-react'

export function App() {
  const [investigationId, setInvestigationId] = useState<string>('inv-live-preview')
  const [investigationStatus, setInvestigationStatus] = useState<string>('READY')
  const [activeTab, setActiveTab] = useState<'image' | 'video' | 'audio' | 'provenance' | 'claims'>('image')
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false)
  const [isReportOpen, setIsReportOpen] = useState<boolean>(false)

  // Investigation state
  const [imageAnalysis, setImageAnalysis] = useState<AnalysisResponse | null>(null)
  const [videoAnalysis, setVideoAnalysis] = useState<AnalysisResponse | null>(null)
  const [audioAnalysis, setAudioAnalysis] = useState<AnalysisResponse | null>(null)
  const [provenance, setProvenance] = useState<ProvenanceData | null>(null)
  const [claims, setClaims] = useState<ClaimAssessment[]>([])

  // Handler: Load Demo Showcase
  const handleLoadDemo = () => {
    const demo = getDemoInvestigation()
    setImageAnalysis(demo.imageAnalysis)
    setVideoAnalysis(demo.videoAnalysis)
    setAudioAnalysis(demo.audioAnalysis)
    setProvenance(demo.provenance)
    setClaims(demo.claims)
    setInvestigationId(demo.imageAnalysis.analysis_id)
    setInvestigationStatus('COMPLETED')
  }

  // Handler: Real Backend Analysis
  const handleAnalyze = async (modality: ModalityType, file: File) => {
    if (modality === 'claim') return
    setIsAnalyzing(true)
    setInvestigationStatus('ANALYZING')

    try {
      const response = await analyzeMedia(modality, file)
      setInvestigationId(response.analysis_id)
      setInvestigationStatus('COMPLETED')

      if (modality === 'image') {
        setImageAnalysis(response)
        setActiveTab('image')
      } else if (modality === 'video') {
        setVideoAnalysis(response)
        setActiveTab('video')
      } else if (modality === 'audio') {
        setAudioAnalysis(response)
        setActiveTab('audio')
      }
    } catch (err: any) {
      console.error(err)
      setInvestigationStatus('FAILED')
      throw err
    } finally {
      setIsAnalyzing(false)
    }
  }

  // Handler: Export Raw JSON Dossier
  const handleExportJson = () => {
    const exportData = {
      investigation_id: investigationId,
      status: investigationStatus,
      exported_at: new Date().toISOString(),
      modules: {
        module_5_image: imageAnalysis,
        module_6_video: videoAnalysis,
        module_7_audio: audioAnalysis,
        module_8_provenance: provenance,
        module_3_4_claims: claims,
      },
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `pramaan_case_${investigationId}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="app-layout">
      {/* Top Header */}
      <Header
        investigationId={investigationId}
        status={investigationStatus}
        onLoadDemo={handleLoadDemo}
        onExportReport={() => setIsReportOpen(true)}
        onExportJson={handleExportJson}
      />

      <main className="main-content">
        {/* Ingestion & Upload Hub */}
        <section className="mb-6">
          <MediaUploader onAnalyze={handleAnalyze} isAnalyzing={isAnalyzing} />
        </section>

        {/* Tab Navigation Controls */}
        <div className="section-tabs">
          <button
            className={`sec-tab ${activeTab === 'image' ? 'active' : ''}`}
            onClick={() => setActiveTab('image')}
          >
            <ImageIcon size={18} />
            <span>Image Forensics</span>
            {imageAnalysis && <span className="tab-dot" />}
          </button>

          <button
            className={`sec-tab ${activeTab === 'video' ? 'active' : ''}`}
            onClick={() => setActiveTab('video')}
          >
            <Video size={18} />
            <span>Video Forensics</span>
            {videoAnalysis && <span className="tab-dot" />}
          </button>

          <button
            className={`sec-tab ${activeTab === 'audio' ? 'active' : ''}`}
            onClick={() => setActiveTab('audio')}
          >
            <Music size={18} />
            <span>Audio Forensics</span>
            {audioAnalysis && <span className="tab-dot" />}
          </button>

          <button
            className={`sec-tab ${activeTab === 'provenance' ? 'active' : ''}`}
            onClick={() => setActiveTab('provenance')}
          >
            <Share2 size={18} />
            <span>Provenance &amp; Graph</span>
            {provenance && <span className="tab-dot" />}
          </button>

          <button
            className={`sec-tab ${activeTab === 'claims' ? 'active' : ''}`}
            onClick={() => setActiveTab('claims')}
          >
            <FileCheck2 size={18} />
            <span>Claim Verification</span>
            {claims.length > 0 && <span className="tab-dot" />}
          </button>
        </div>

        {/* Main Tab Panels */}
        <div className="tab-panel-container mt-6">
          {activeTab === 'image' && <ImageForensicsCard data={imageAnalysis} />}
          {activeTab === 'video' && <VideoForensicsCard data={videoAnalysis} />}
          {activeTab === 'audio' && <AudioForensicsCard data={audioAnalysis} />}
          {activeTab === 'provenance' && <ProvenanceGraph data={provenance} />}
          {activeTab === 'claims' && <ClaimAssessmentCard claims={claims} />}
        </div>
      </main>

      {/* Investigation Printable Report Modal */}
      <InvestigationReportModal
        isOpen={isReportOpen}
        onClose={() => setIsReportOpen(false)}
        investigationId={investigationId}
        imageAnalysis={imageAnalysis}
        videoAnalysis={videoAnalysis}
        audioAnalysis={audioAnalysis}
        provenance={provenance}
        claims={claims}
      />
    </div>
  )
}

export default App
