import { useState } from 'react'
import { Sidebar, type NavPage } from './components/Sidebar'
import { TopNav } from './components/TopNav'
import { MediaUploader } from './components/MediaUploader'
import { ImageForensicsCard } from './components/ImageForensicsCard'
import { VideoForensicsCard } from './components/VideoForensicsCard'
import { AudioForensicsCard } from './components/AudioForensicsCard'
import { ProvenanceGraph } from './components/ProvenanceGraph'
import { ClaimAssessmentCard } from './components/ClaimAssessmentCard'
import { InvestigationReportModal } from './components/InvestigationReportModal'
import { LiveFeedRadar } from './components/LiveFeedRadar'
import { analyzeMedia, auditUrl, getDemoInvestigation } from './services/api'
import type {
  AnalysisResponse,
  ClaimAssessment,
  ModalityType,
  ProvenanceData,
  UnifiedPipelineResponse,
} from './types'
import {
  Image as ImageIcon,
  Video,
  Music,
  PlusCircle,
  Sparkles,
} from 'lucide-react'

// Reusable Empty State for Forensic Lab Pages
interface EmptyPageProps {
  icon: React.ReactNode
  title: string
  desc: string
  onGoIngest: () => void
  onLoadDemo: () => void
}

function EmptyPageCard({ icon, title, desc, onGoIngest, onLoadDemo }: EmptyPageProps) {
  return (
    <div className="empty-page-card">
      <div className="empty-icon-box">{icon}</div>
      <h3 className="empty-title">{title}</h3>
      <p className="empty-desc">{desc}</p>
      <div className="empty-actions-row">
        <button onClick={onGoIngest} className="btn btn-primary">
          <PlusCircle size={16} />
          <span>Start New Ingestion</span>
        </button>
        <button onClick={onLoadDemo} className="btn btn-secondary">
          <Sparkles size={16} />
          <span>Load Demo Showcase</span>
        </button>
      </div>
    </div>
  )
}

export function App() {
  const [investigationId, setInvestigationId] = useState<string>('inv-live-preview')
  const [investigationStatus, setInvestigationStatus] = useState<string>('READY')
  const [activePage, setActivePage] = useState<NavPage>('radar')
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
    setActivePage('image')
  }

  // Helper: Apply Unified Pipeline Result (Mode A or Mode B)
  const applyPipelineResult = (res: UnifiedPipelineResponse) => {
    setInvestigationId(res.investigation_id)
    setInvestigationStatus('COMPLETED')

    if (res.forensic_findings) {
      setImageAnalysis(res.forensic_findings)
    }

    if (res.claim_assessments && res.claim_assessments.length > 0) {
      setClaims(res.claim_assessments)
    }

    if (res.provenance && res.provenance.dag) {
      setProvenance({
        investigation_id: res.investigation_id,
        is_dag: res.provenance.dag.is_valid_dag,
        cycle_detected: !res.provenance.dag.is_valid_dag,
        nodes: res.provenance.dag.nodes || [],
        edges: (res.provenance.dag.edges || []).map((e: any) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          relationship_type: e.relationship || 'DERIVED_FROM',
          confidence: 0.95,
          basis: e.basis || 'Perceptual hashing & derivation',
        })),
        timeline: [
          {
            timestamp: new Date().toISOString(),
            event: 'Ingestion & Triage',
            entity_id: res.investigation_id,
            entity_type: 'INVESTIGATION',
            description: `Automated ${res.mode} verification executed.`,
          },
        ],
      })
    }

    // Automatically navigate to the most relevant findings page
    if (res.claim_assessments && res.claim_assessments.length > 0) {
      setActivePage('claims')
    } else if (res.forensic_findings) {
      setActivePage('image')
    } else {
      setActivePage('provenance')
    }
  }

  // Handler: Mode A URL Audit (oEmbed)
  const handleAuditUrl = async (url: string) => {
    setIsAnalyzing(true)
    setInvestigationStatus('ANALYZING')
    try {
      const response = await auditUrl(url)
      applyPipelineResult(response)
    } catch (err: any) {
      console.error(err)
      setInvestigationStatus('FAILED')
      throw err
    } finally {
      setIsAnalyzing(false)
    }
  }

  // Handler: Direct File Upload
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
        setActivePage('image')
      } else if (modality === 'video') {
        setVideoAnalysis(response)
        setActivePage('video')
      } else if (modality === 'audio') {
        setAudioAnalysis(response)
        setActivePage('audio')
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
    <div className="dashboard-container">
      {/* ── Left Sidebar Navigation ── */}
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
        investigationId={investigationId}
        investigationStatus={investigationStatus}
        hasImage={Boolean(imageAnalysis)}
        hasVideo={Boolean(videoAnalysis)}
        hasAudio={Boolean(audioAnalysis)}
        hasProvenance={Boolean(provenance)}
        claimCount={claims.length}
        onLoadDemo={handleLoadDemo}
        onExportReport={() => setIsReportOpen(true)}
        onExportJson={handleExportJson}
      />

      {/* ── Right Workspace (Dedicated Page View) ── */}
      <main className="app-workspace">
        <TopNav
          activePage={activePage}
          investigationId={investigationId}
          investigationStatus={investigationStatus}
          onNavigate={setActivePage}
          onExportReport={() => setIsReportOpen(true)}
          onExportJson={handleExportJson}
        />

        <div className="workspace-content">
          {/* Mode B: Live Feed Radar */}
          {activePage === 'radar' && (
            <LiveFeedRadar
              onAuditComplete={applyPipelineResult}
              isAuditing={isAnalyzing}
            />
          )}

          {/* Mode A & File Ingestion Gateway */}
          {activePage === 'ingest' && (
            <MediaUploader
              onAnalyze={handleAnalyze}
              onAuditUrl={handleAuditUrl}
              isAnalyzing={isAnalyzing}
            />
          )}

          {/* Image Forensics Lab */}
          {activePage === 'image' && (
            imageAnalysis ? (
              <ImageForensicsCard data={imageAnalysis} />
            ) : (
              <EmptyPageCard
                icon={<ImageIcon size={32} className="text-purple" />}
                title="Image Forensics Laboratory"
                desc="No image has been analyzed yet in this case. Paste a tweet/post URL using Mode A or upload a JPEG/PNG file in the Ingestion Hub to generate Error Level Analysis heatmaps and ORB copy-move detection masks."
                onGoIngest={() => setActivePage('ingest')}
                onLoadDemo={handleLoadDemo}
              />
            )
          )}

          {/* Video Forensics Lab */}
          {activePage === 'video' && (
            videoAnalysis ? (
              <VideoForensicsCard data={videoAnalysis} />
            ) : (
              <EmptyPageCard
                icon={<Video size={32} className="text-amber" />}
                title="Video Forensics Laboratory"
                desc="No video asset has been analyzed yet. Upload an MP4 or WebM video file to extract keyframes, inspect inter-frame temporal differencing, and analyze 2D spectral FFT energy distributions."
                onGoIngest={() => setActivePage('ingest')}
                onLoadDemo={handleLoadDemo}
              />
            )
          )}

          {/* Audio Forensics Lab */}
          {activePage === 'audio' && (
            audioAnalysis ? (
              <AudioForensicsCard data={audioAnalysis} />
            ) : (
              <EmptyPageCard
                icon={<Music size={32} className="text-pink" />}
                title="Audio Forensics Laboratory"
                desc="No audio asset has been analyzed yet. Upload a WAV audio stream to generate STFT spectrogram heatmaps, inspect pitch (F0) autocorrelation continuity, and detect acoustic splice discontinuities."
                onGoIngest={() => setActivePage('ingest')}
                onLoadDemo={handleLoadDemo}
              />
            )
          )}

          {/* Media Provenance DAG */}
          {activePage === 'provenance' && (
            <ProvenanceGraph data={provenance} />
          )}

          {/* Fact-Verification & Claims Dossier */}
          {activePage === 'claims' && (
            <ClaimAssessmentCard claims={claims} />
          )}
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
