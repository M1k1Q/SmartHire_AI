import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import {
  Users, ArrowLeft, Download, Filter,
  ChevronRight, Brain, User, Mail, Calendar,
  CheckCircle, XCircle, Clock, Trash2, X,
  Briefcase, Star, Cpu, FileText
} from 'lucide-react';
import toast from 'react-hot-toast';
import ScoreBadge from '../components/ScoreBadge';

/* ─── Candidate Detail Modal ─────────────────────────────── */
function CandidateModal({ app, index, onClose, onUpdateStatus }) {
  if (!app) return null;

  const isSuitable = app.prediction === 'Suitable';
  const confPct = app.prediction_prob ? Math.round(app.prediction_prob * 100) : null;
  const scorePct = app.rank_score ? Math.round(app.rank_score * 100) : null;
  
  const statusConfig = {
    shortlisted: { color: 'var(--success)', icon: <CheckCircle size={14} />, bg: 'var(--success-bg)' },
    rejected:    { color: 'var(--danger)',  icon: <XCircle size={14} />, bg: 'var(--danger-bg)' },
    pending:     { color: 'var(--warning)', icon: <Clock size={14} />,   bg: 'var(--warning-bg)' },
  };
  
  const currentStatus = statusConfig[app.status] || statusConfig.pending;

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div style={modalStyle} onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div style={modalHeaderStyle}>
          <div style={{ display:'flex', alignItems:'center', gap:20 }}>
            <div style={modalAvatarStyle}>
              <User size={36} color="var(--accent-light)" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                <span style={rankBadgeSmall}>RANK #{index + 1}</span>
                <span style={{ 
                  ...statusBadgeSmall, 
                  color: currentStatus.color, 
                  background: currentStatus.bg,
                  borderColor: currentStatus.color + '44'
                }}>
                  {currentStatus.icon} {app.status.toUpperCase()}
                </span>
              </div>
              <h2 style={{ fontSize:'1.75rem', margin:0, color: 'var(--text-primary)' }}>{app.candidate_name}</h2>
              <div style={{ fontSize:'0.9rem', color:'var(--text-secondary)', display:'flex', alignItems:'center', gap:8, marginTop:6 }}>
                <Mail size={14} style={{ opacity: 0.7 }}/> {app.candidate_email}
              </div>
            </div>
          </div>
          <button style={closeButtonStyle} onClick={onClose} title="Close">
            <X size={22}/>
          </button>
        </div>

        {/* Body */}
        <div style={modalBodyStyle}>
          <div style={modalContentGrid}>
            
            {/* Left Column: AI & Stats */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              
              <section style={modalSectionCard}>
                <div style={modalSectionHeader}>
                  <Cpu size={16} color="var(--accent-light)"/>
                  <span>AI EVALUATION & MATCHING</span>
                </div>
                <div style={{ padding: '16px 0' }}>
                  <ScoreBadge prediction={app.prediction} prob={app.prediction_prob} rankScore={app.rank_score} />
                </div>
                
                <div style={scoreMetricBox}>
                  <div style={{ display:'flex', justifyContent:'space-between', marginBottom: 8 }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Overall Match Score</span>
                    <span style={{ fontSize: '1rem', fontWeight: 700, color: isSuitable ? 'var(--success)' : 'var(--accent-light)' }}>{scorePct}%</span>
                  </div>
                  <div style={progressBarLarge}>
                    <div style={{ 
                      ...progressFillLarge, 
                      width: `${scorePct}%`,
                      background: isSuitable ? 'var(--success)' : 'var(--gradient-main)'
                    }} />
                  </div>
                </div>
              </section>

              <section style={modalSectionCard}>
                <div style={modalSectionHeader}>
                  <Briefcase size={16} color="var(--accent-light)"/>
                  <span>PROFESSIONAL SUMMARY</span>
                </div>
                <div style={statsGridSmall}>
                  <div style={statItemSmall}>
                    <span style={statLabelSmall}>EXPERIENCE</span>
                    <span style={statValueSmall}>{app.experience_years ?? '0'} Years</span>
                  </div>
                  <div style={statItemSmall}>
                    <span style={statLabelSmall}>APPLIED ON</span>
                    <span style={statValueSmall}>{new Date(app.applied_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                  </div>
                  <div style={statItemSmall}>
                    <span style={statLabelSmall}>AI PREDICTION</span>
                    <span style={{ ...statValueSmall, color: isSuitable ? 'var(--success)' : 'var(--danger)' }}>
                      {app.prediction || 'Unclassified'}
                    </span>
                  </div>
                  <div style={statItemSmall}>
                    <span style={statLabelSmall}>CLUSTER</span>
                    <span style={statValueSmall}>
                      {app.cluster_id !== undefined && app.cluster_id !== -1 ? `Type #${app.cluster_id}` : 'N/A'}
                    </span>
                  </div>
                </div>
              </section>

              {confPct !== null && (
                <div style={confidenceAlert}>
                  <Brain size={18} />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{confPct}% Model Confidence</div>
                    <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>High-fidelity NLP parsing verified this candidate.</div>
                  </div>
                </div>
              )}
            </div>

            {/* Right Column: NLP Skills & Content */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              
              <section style={modalSectionCard}>
                <div style={modalSectionHeader}>
                  <Star size={16} color="var(--warning)"/>
                  <span>NLP-EXTRACTED SKILLS & KEYWORDS</span>
                </div>
                <div style={skillsGridEnhanced}>
                  {app.extracted_skills && app.extracted_skills.length > 0 ? (
                    app.extracted_skills.map((skill, i) => (
                      <span key={i} style={skillChipLarge}>{skill}</span>
                    ))
                  ) : (
                    <div style={emptyStateSmall}>No specific skills extracted.</div>
                  )}
                </div>
              </section>

              {app.resume_text && (
                <section style={modalSectionCard}>
                  <div style={modalSectionHeader}>
                    <FileText size={16} color="var(--accent-2)"/>
                    <span>RESUME INSIGHTS</span>
                  </div>
                  <div style={resumePreviewBox}>
                    {app.resume_text.length > 500 ? app.resume_text.substring(0, 500) + '...' : app.resume_text}
                  </div>
                </section>
              )}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div style={modalFooterStyle}>
          <div style={{ display: 'flex', gap: 12 }}>
            <button 
              className="btn btn-secondary" 
              onClick={() => onUpdateStatus(app.id, 'rejected')}
              disabled={app.status === 'rejected'}
            >
              <XCircle size={16} /> Mark as Rejected
            </button>
            <button 
              className="btn btn-primary" 
              onClick={() => onUpdateStatus(app.id, 'shortlisted')}
              disabled={app.status === 'shortlisted'}
            >
              <CheckCircle size={16} /> Shortlist Candidate
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Main Page ──────────────────────────────────────────── */
export default function CandidateRankingPage() {
  const { jobId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [selectedApp, setSelectedApp] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const navigate = useNavigate();

  const fetchCandidates = useCallback(async () => {
    try {
      const res = await api.get(`/applications/job/${jobId}`);
      setData(res.data);
    } catch {
      toast.error('Failed to load candidate rankings.');
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => { fetchCandidates(); }, [fetchCandidates]);

  const updateStatus = async (appId, status) => {
    try {
      await api.put(`/applications/${appId}/status`, { status });
      toast.success(`Candidate marked as ${status}.`);
      // Update in local state so modal refreshes immediately
      setData(prev => ({
        ...prev,
        applications: prev.applications.map(a => a.id === appId ? { ...a, status } : a)
      }));
      if (selectedApp?.id === appId) setSelectedApp(a => ({ ...a, status }));
    } catch {
      toast.error('Failed to update status.');
    }
  };

  const deleteApplication = async (appId, e) => {
    e.stopPropagation(); // don't open modal
    if (!window.confirm('Remove this candidate from the list?')) return;
    setDeletingId(appId);
    try {
      await api.delete(`/applications/${appId}`);
      toast.success('Candidate removed.');
      setData(prev => ({
        ...prev,
        applications: prev.applications.filter(a => a.id !== appId)
      }));
      if (selectedApp?.id === appId) setSelectedApp(null);
    } catch {
      toast.error('Failed to remove candidate.');
    } finally {
      setDeletingId(null);
    }
  };

  const exportToCSV = () => {
    if (!data?.applications?.length) {
      toast.error('No data to export.');
      return;
    }

    const headers = ['Rank', 'Name', 'Email', 'Experience', 'AI Prediction', 'Match Score', 'Status', 'Skills'];
    const rows = data.applications.map((app, index) => [
      index + 1,
      app.candidate_name,
      app.candidate_email,
      `${app.experience_years} yrs`,
      app.prediction,
      `${Math.round(app.rank_score * 100)}%`,
      app.status,
      (app.extracted_skills || []).join('; ')
    ]);

    const csvContent = [
      headers.join(","),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(","))
    ].join("\n");

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `candidates_${data?.job?.title?.replace(/\s+/g, '_') || 'report'}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('Report exported as CSV!');
  };

  const openModal = (app, index) => {
    setSelectedApp(app);
    setSelectedIndex(index);
  };

  const filteredApps = (data?.applications || []).filter(app => {
    if (filter === 'suitable') return app.prediction === 'Suitable';
    if (filter === 'shortlisted') return app.status === 'shortlisted';
    return true;
  });

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="spinner" />
        <p>Ranking candidates using AI...</p>
      </div>
    );
  }

  return (
    <div className="animate-fade">
      {/* Modal */}
      {selectedApp && (
        <CandidateModal
          app={selectedApp}
          index={selectedIndex}
          onClose={() => setSelectedApp(null)}
          onUpdateStatus={updateStatus}
        />
      )}

      <div className="section-header">
        <div style={{ display:'flex', alignItems:'center', gap:16 }}>
          <button className="btn btn-icon btn-secondary" onClick={() => navigate('/jobs')}>
            <ArrowLeft size={18}/>
          </button>
          <div>
            <h1 className="section-title">Candidate Rankings</h1>
            <p className="section-subtitle">Ranked evaluation for <b>{data?.job?.title}</b></p>
          </div>
        </div>
        <div style={{ display:'flex', gap:10 }}>
          <button className="btn btn-secondary" onClick={() => navigate('/analytics')}>
            Skill Clusters <Brain size={16}/>
          </button>
          <button className="btn btn-primary" onClick={exportToCSV}>
            Export Report <Download size={16}/>
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="card" style={{ marginBottom:24, padding:'16px 24px' }}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
          <div style={{ display:'flex', gap:12 }}>
            <span style={{ fontSize:'0.875rem', color:'var(--text-muted)', display:'flex', alignItems:'center', gap:6 }}>
              <Filter size={16}/> Filter by:
            </span>
            {[['all', `All Applicants (${data?.applications?.length || 0})`], ['suitable', 'AI Suitable'], ['shortlisted', 'Shortlisted']].map(([val, label]) => (
              <button key={val} className={`btn btn-sm ${filter === val ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter(val)}>
                {label}
              </button>
            ))}
          </div>
          <div style={{ fontSize:'0.75rem', color:'var(--text-muted)' }}>
            Latest AI Model Version: <span style={{ color:'var(--accent-light)' }}>v1.0.4</span>
          </div>
        </div>
      </div>

      {/* Candidate List */}
      <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
        {filteredApps.length > 0 ? filteredApps.map((app, index) => (
          <div
            key={app.id}
            className="card animate-fade-up"
            style={{ animationDelay:`${index * 0.05}s`, cursor:'pointer', transition:'border-color 0.2s, box-shadow 0.2s', position:'relative' }}
            onClick={() => openModal(app, index)}
            onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(124,58,237,0.5)'; e.currentTarget.style.boxShadow = '0 0 0 2px rgba(124,58,237,0.15)'; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = ''; e.currentTarget.style.boxShadow = ''; }}
          >
            <div style={{ display:'flex', alignItems:'center', gap:24 }}>
              {/* Rank */}
              <div style={{ fontSize:'1.5rem', fontWeight:800, color:'rgba(255,255,255,0.1)', fontFamily:'Space Grotesk, sans-serif', minWidth:40, textAlign:'center' }}>
                #{index + 1}
              </div>

              {/* Main Info */}
              <div style={{ flex:1 }}>
                <div style={{ display:'flex', alignItems:'center', gap:16, marginBottom:12 }}>
                  <div style={{ width:48, height:48, borderRadius:12, background:'rgba(124,58,237,0.1)', display:'flex', alignItems:'center', justifyContent:'center', border:'1px solid rgba(124,58,237,0.2)' }}>
                    <User size={24} color="var(--accent-light)"/>
                  </div>
                  <div>
                    <h3 style={{ fontSize:'1.25rem', marginBottom:2 }}>{app.candidate_name}</h3>
                    <div style={{ fontSize:'0.8rem', color:'var(--text-muted)', display:'flex', alignItems:'center', gap:6 }}>
                      <Mail size={12}/> {app.candidate_email}
                    </div>
                  </div>
                </div>
                <div style={{ display:'flex', flexWrap:'wrap', gap:6, marginBottom:16 }}>
                  {app.extracted_skills.slice(0, 8).map((skill, i) => (
                    <span key={i} className="skill-tag">{skill}</span>
                  ))}
                  {app.extracted_skills.length > 8 && (
                    <span className="skill-tag">+{app.extracted_skills.length - 8} more</span>
                  )}
                  {app.extracted_skills.length === 0 && (
                    <span style={{ fontSize:'0.75rem', color:'var(--text-muted)' }}>No skills extracted</span>
                  )}
                </div>
                <div style={{ display:'flex', gap:20 }}>
                  <div style={{ display:'flex', alignItems:'center', gap:6, fontSize:'0.8rem', color:'var(--text-secondary)' }}>
                    <Clock size={14}/> <span><b>{app.experience_years}</b> yrs Exp</span>
                  </div>
                  <div style={{ display:'flex', alignItems:'center', gap:6, fontSize:'0.8rem', color:'var(--text-secondary)' }}>
                    <Calendar size={14}/> <span>Applied {new Date(app.applied_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              {/* AI Score */}
              <div style={{ width:180, borderLeft:'1px solid var(--border)', borderRight:'1px solid var(--border)', padding:'0 24px', display:'flex', flexDirection:'column', justifyContent:'center' }}>
                <div style={{ fontSize:'0.65rem', fontWeight:700, color:'var(--text-muted)', letterSpacing:'0.1em', marginBottom:8 }}>AI EVALUATION</div>
                <ScoreBadge prediction={app.prediction} prob={app.prediction_prob} rankScore={app.rank_score}/>
              </div>

              {/* Actions */}
              <div style={{ width:220, paddingLeft:8, display:'flex', flexDirection:'column', gap:12 }} onClick={e => e.stopPropagation()}>
                <div style={{ fontSize:'0.75rem', color:'var(--text-muted)' }}>
                  Status: <span style={{ color:'var(--text-primary)', fontWeight:600 }}>{app.status}</span>
                </div>
                <div style={{ display:'flex', gap:8, alignItems:'center' }}>
                  <button className="btn btn-secondary btn-sm" onClick={() => updateStatus(app.id, 'shortlisted')} disabled={app.status === 'shortlisted'}>
                    <CheckCircle size={14}/> Shortlist
                  </button>
                  <button className="btn btn-secondary btn-sm" onClick={() => updateStatus(app.id, 'rejected')} disabled={app.status === 'rejected'}>
                    <XCircle size={14}/> Reject
                  </button>
                  <button className="btn btn-primary btn-sm btn-icon" onClick={() => openModal(app, index)} title="View details">
                    <ChevronRight size={16}/>
                  </button>
                  <button
                    className="btn btn-sm btn-icon"
                    title="Remove candidate"
                    disabled={deletingId === app.id}
                    onClick={(e) => deleteApplication(app.id, e)}
                    style={{ background:'rgba(239,68,68,0.1)', border:'1px solid rgba(239,68,68,0.3)', color:'var(--danger)', borderRadius:'var(--radius)', padding:'6px 8px', cursor:'pointer', transition:'background 0.2s' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(239,68,68,0.25)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'rgba(239,68,68,0.1)'}
                  >
                    {deletingId === app.id ? <Clock size={14}/> : <Trash2 size={14}/>}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )) : (
          <div className="card">
            <div className="empty-state">
              <Users size={48} style={{ opacity:0.1, marginBottom:16 }}/>
              <h3>No candidates match this filter</h3>
              <p>Try changing your filter settings or checking back later.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Modal Styles ───────────────────────────────────────── */
const overlayStyle = {
  position:'fixed', inset:0, zIndex:1000,
  background:'rgba(0,0,0,0.75)', backdropFilter:'blur(8px)',
  display:'flex', alignItems:'center', justifyContent:'center',
  padding:24, animation:'fadeIn 0.2s ease',
};
const modalStyle = {
  background:'var(--bg-secondary)', border:'1px solid var(--border)',
  borderRadius:'var(--radius-xl)', width:'100%', maxWidth:1000,
  boxShadow:'0 24px 80px rgba(0,0,0,0.8)',
  animation:'slideUp 0.3s cubic-bezier(0.16,1,0.3,1)',
  overflow:'hidden',
  display: 'flex',
  flexDirection: 'column',
};
const modalHeaderStyle = {
  display:'flex', alignItems:'center', justifyContent:'space-between',
  padding:'32px 40px', borderBottom:'1px solid var(--border)',
  background:'rgba(255,255,255,0.02)',
};
const modalAvatarStyle = {
  width:72, height:72, borderRadius:20,
  background:'var(--gradient-card)',
  display:'flex', alignItems:'center', justifyContent:'center',
  border:'1px solid var(--border-accent)',
  boxShadow: '0 8px 16px rgba(0,0,0,0.2)',
};
const rankBadgeSmall = {
  fontSize: '0.7rem', fontWeight: 800, color: 'var(--text-muted)',
  background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: 4,
  letterSpacing: '0.1em'
};
const statusBadgeSmall = {
  fontSize: '0.7rem', fontWeight: 700, padding: '2px 8px', borderRadius: 4,
  display: 'flex', alignItems: 'center', gap: 4, border: '1px solid'
};
const closeButtonStyle = {
  background:'transparent', border:'none',
  borderRadius:'var(--radius-md)', padding:'10px', color:'var(--text-muted)',
  cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center',
  transition:'all 0.2s',
};
const modalBodyStyle = {
  padding:'32px 40px',
  overflowY:'auto',
  maxHeight:'calc(90vh - 180px)',
};
const modalContentGrid = {
  display: 'grid',
  gridTemplateColumns: '1.2fr 1.8fr',
  gap: '40px',
};
const modalSectionCard = {
  background:'rgba(255,255,255,0.03)',
  border:'1px solid var(--border)',
  borderRadius:'var(--radius-lg)',
  padding: '24px',
};
const modalSectionHeader = {
  fontSize:'0.75rem', fontWeight:700, color:'var(--text-secondary)',
  letterSpacing:'0.1em', marginBottom:20,
  display:'flex', alignItems:'center', gap:10,
  borderBottom: '1px solid var(--border)',
  paddingBottom: 12,
};
const scoreMetricBox = {
  marginTop: 16,
  padding: 16,
  background: 'rgba(0,0,0,0.2)',
  borderRadius: 'var(--radius-md)',
};
const progressBarLarge = {
  height: 10, background: 'rgba(255,255,255,0.05)', borderRadius: 5, overflow: 'hidden'
};
const progressFillLarge = {
  height: '100%', transition: 'width 1s ease-out'
};
const statsGridSmall = {
  display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px 10px'
};
const statItemSmall = { display: 'flex', flexDirection: 'column', gap: 4 };
const statLabelSmall = { fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 600 };
const statValueSmall = { fontSize: '1rem', color: 'var(--text-primary)', fontWeight: 600 };

const confidenceAlert = {
  display: 'flex', alignItems: 'center', gap: 12,
  padding: 16, borderRadius: 'var(--radius-md)',
  background: 'rgba(124,58,237,0.1)', border: '1px solid rgba(124,58,237,0.2)',
  color: 'var(--accent-light)'
};

const skillsGridEnhanced = {
  display: 'flex', flexWrap: 'wrap', gap: 10
};
const skillChipLarge = {
  padding: '6px 14px', background: 'rgba(255,255,255,0.05)',
  border: '1px solid var(--border)', borderRadius: 'var(--radius-full)',
  fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 500,
  transition: 'all 0.2s'
};
const resumePreviewBox = {
  fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.8,
  padding: 20, background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-md)',
  maxHeight: 250, overflowY: 'auto', border: '1px solid var(--border)',
  whiteSpace: 'pre-wrap', fontFamily: 'Inter, sans-serif'
};
const emptyStateSmall = {
  fontSize: '0.9rem', color: 'var(--text-muted)', fontStyle: 'italic'
};
const modalFooterStyle = {
  padding: '24px 40px',
  background: 'rgba(255,255,255,0.02)',
  borderTop: '1px solid var(--border)',
  display: 'flex', justifyContent: 'flex-end',
};
