import React, { useEffect, useState } from 'react'
import type { FeedItem, UnifiedPipelineResponse } from '../types'
import { auditFeedPost, getLiveFeed, triggerViralSpike } from '../services/api'
import {
  Radio,
  Zap,
  TrendingUp,
  ExternalLink,
  ShieldAlert,
  Loader2,
  RefreshCw,
  Flame,
  MessageSquare,
  Eye,
  Share2,
} from 'lucide-react'

interface LiveFeedRadarProps {
  onAuditComplete: (result: UnifiedPipelineResponse) => void
  isAuditing: boolean
}

export const LiveFeedRadar: React.FC<LiveFeedRadarProps> = ({ onAuditComplete, isAuditing }) => {
  const [feedItems, setFeedItems] = useState<FeedItem[]>([])
  const [selectedPlatform, setSelectedPlatform] = useState<string>('ALL')
  const [loading, setLoading] = useState<boolean>(true)
  const [auditingItemId, setAuditingItemId] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [spikeNotification, setSpikeNotification] = useState<string | null>(null)

  const loadFeed = async () => {
    setLoading(true)
    setErrorMsg(null)
    try {
      const items = await getLiveFeed(true)
      setFeedItems(items)
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch live social stream.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFeed()
  }, [])

  const handleAuditItem = async (item: FeedItem) => {
    setAuditingItemId(item.id)
    setErrorMsg(null)
    try {
      const result = await auditFeedPost(item.id, item)
      onAuditComplete(result)
    } catch (err: any) {
      setErrorMsg(`Audit failed on ${item.title}: ${err.message}`)
    } finally {
      setAuditingItemId(null)
    }
  }

  const handleSimulateSpike = async () => {
    try {
      const spike = await triggerViralSpike()
      setFeedItems((prev) => [spike, ...prev])
      setSpikeNotification(`High-velocity viral spike detected: "${spike.title.slice(0, 60)}..."`)
      setTimeout(() => setSpikeNotification(null), 8000)
    } catch (err: any) {
      setErrorMsg('Failed to inject viral spike.')
    }
  }

  const filteredItems = selectedPlatform === 'ALL'
    ? feedItems
    : feedItems.filter((item) => item.platform.toLowerCase().includes(selectedPlatform.toLowerCase()))

  return (
    <div className="forensics-container">
      {/* Radar Status Header */}
      <div className="verdict-banner" style={{ background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.95))' }}>
        <div className="verdict-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
              <span className="live-pulse" style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '50%', background: '#22c55e', boxShadow: '0 0 10px #22c55e' }}></span>
              <span className="verdict-badge-label" style={{ color: '#22c55e', fontWeight: 700 }}>
                MODE B: LIVE SOCIAL FEED RADAR & EARLY WARNING
              </span>
            </div>
            <h3 className="verdict-title" style={{ fontSize: '1.25rem', margin: 0 }}>
              Continuous Viral Stream & Misinformation Surveillance
            </h3>
            <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginTop: '0.3rem' }}>
              Monitoring public social feeds, calculating virality velocity, and triaging emerging deepfake narratives before manual escalation.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              onClick={handleSimulateSpike}
              className="action-btn"
              style={{
                background: 'linear-gradient(135deg, #ef4444, #dc2626)',
                color: '#fff',
                border: 'none',
                padding: '0.55rem 1rem',
                borderRadius: '6px',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                cursor: 'pointer',
              }}
              title="Simulates an urgent high-velocity breaking deepfake claim for judges and live demonstration."
            >
              <Flame size={16} />
              <span>Simulate Viral Spike (Demo)</span>
            </button>

            <button
              onClick={loadFeed}
              disabled={loading}
              className="action-btn"
              style={{
                background: 'rgba(51, 65, 85, 0.8)',
                color: '#e2e8f0',
                border: '1px solid #475569',
                padding: '0.55rem 0.9rem',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                cursor: 'pointer',
              }}
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </div>

      {/* Spike Alert Notification */}
      {spikeNotification && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid #ef4444',
          borderRadius: '8px',
          padding: '0.85rem 1.2rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          color: '#fca5a5',
          animation: 'pulse 2s infinite',
        }}>
          <ShieldAlert size={22} color="#ef4444" />
          <div style={{ flex: 1 }}>
            <strong style={{ color: '#fff' }}>EARLY WARNING VELOCITY SPIKE: </strong>
            {spikeNotification}
          </div>
        </div>
      )}

      {/* Platform Filter Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
        {['ALL', 'Twitter', 'Reddit', 'Telegram', 'YouTube'].map((plat) => (
          <button
            key={plat}
            onClick={() => setSelectedPlatform(plat)}
            style={{
              background: selectedPlatform === plat ? '#3b82f6' : 'rgba(30, 41, 59, 0.7)',
              color: selectedPlatform === plat ? '#fff' : '#94a3b8',
              border: selectedPlatform === plat ? '1px solid #3b82f6' : '1px solid #334155',
              padding: '0.4rem 0.9rem',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            {plat === 'ALL' ? 'All Platforms' : plat}
          </button>
        ))}
      </div>

      {/* Feed Stream Cards */}
      {loading ? (
        <div className="card empty-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '200px' }}>
          <Loader2 className="animate-spin" size={28} color="#3b82f6" />
          <span style={{ marginLeft: '0.75rem', color: '#94a3b8' }}>Ingesting live public streams and virality telemetry...</span>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="card empty-card">
          <p>No active feed items detected matching this filter.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filteredItems.map((item) => (
            <div
              key={item.id}
              className="card"
              style={{
                border: item.is_viral_spike ? '1px solid rgba(239, 68, 68, 0.6)' : '1px solid #334155',
                background: item.is_viral_spike ? 'linear-gradient(180deg, rgba(30, 41, 59, 0.9), rgba(69, 10, 10, 0.25))' : 'rgba(30, 41, 59, 0.8)',
                padding: '1.25rem',
                borderRadius: '8px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <span style={{
                    background: '#1e293b',
                    border: '1px solid #475569',
                    padding: '0.2rem 0.6rem',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    color: '#60a5fa',
                  }}>
                    {item.platform}
                  </span>
                  <span style={{ color: '#cbd5e1', fontWeight: 600, fontSize: '0.9rem' }}>{item.author}</span>
                  {item.author_handle && (
                    <span style={{ color: '#64748b', fontSize: '0.8rem' }}>{item.author_handle}</span>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  {item.is_viral_spike && (
                    <span style={{
                      background: 'rgba(239, 68, 68, 0.2)',
                      border: '1px solid #ef4444',
                      color: '#f87171',
                      padding: '0.2rem 0.6rem',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.3rem',
                    }}>
                      <Zap size={12} />
                      VIRAL SPIKE
                    </span>
                  )}

                  <span style={{
                    color: item.shares_per_minute > 2500 ? '#f59e0b' : '#94a3b8',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.3rem',
                  }}>
                    <TrendingUp size={14} />
                    {item.shares_per_minute.toLocaleString()} shares/min
                  </span>
                </div>
              </div>

              {/* Title & Content */}
              <h4 style={{ fontSize: '1.05rem', color: '#f1f5f9', margin: '0 0 0.5rem 0', lineHeight: 1.4 }}>
                {item.title}
              </h4>
              <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.5, margin: '0 0 1rem 0' }}>
                {item.content}
              </p>

              {/* Media Thumbnail Preview if present */}
              {item.media_url && (
                <div style={{ marginBottom: '1rem', maxHeight: '220px', overflow: 'hidden', borderRadius: '6px', border: '1px solid #334155' }}>
                  <img
                    src={item.media_url}
                    alt={item.title}
                    style={{ width: '100%', maxHeight: '220px', objectFit: 'cover' }}
                    onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
                  />
                </div>
              )}

              {/* Footer Actions */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', paddingTop: '0.5rem', borderTop: '1px solid rgba(51, 65, 85, 0.6)' }}>
                <div style={{ display: 'flex', gap: '1.25rem', color: '#64748b', fontSize: '0.8rem' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <Eye size={14} />
                    {item.total_impressions.toLocaleString()} views
                  </span>
                  <a
                    href={item.source_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: '#60a5fa', textDecoration: 'none' }}
                  >
                    <span>View Permasource</span>
                    <ExternalLink size={12} />
                  </a>
                </div>

                <button
                  onClick={() => handleAuditItem(item)}
                  disabled={auditingItemId === item.id || isAuditing}
                  style={{
                    background: item.is_viral_spike ? 'linear-gradient(135deg, #2563eb, #1d4ed8)' : '#334155',
                    color: '#fff',
                    border: 'none',
                    padding: '0.45rem 1.1rem',
                    borderRadius: '6px',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    cursor: (auditingItemId === item.id || isAuditing) ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                  }}
                >
                  {auditingItemId === item.id ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      <span>Auditing Multi-Modal Pipeline...</span>
                    </>
                  ) : (
                    <>
                      <ShieldAlert size={14} />
                      <span>Audit & Verify Now</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
