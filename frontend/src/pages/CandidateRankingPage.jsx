import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { 
  Users, ArrowLeft, Download, Filter, 
  ChevronRight, Brain, User, Mail, Calendar, 
  MapPin, CheckCircle, XCircle, Clock
} from 'lucide-react';
import toast from 'react-hot-toast';
import ScoreBadge from '../components/ScoreBadge';

export default function CandidateRankingPage() {
  const { jobId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, suitable, shortlisted
  const navigate = useNavigate();

  useEffect(() => {
    fetchCandidates();
  }, [jobId]);

  const fetchCandidates = async () => {
    try {
      const res = await api.get(`/applications/job/${jobId}`);
      setData(res.data);
    } catch (err) {
      toast.error('Failed to load candidate rankings.');
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (appId, status) => {
    try {
      await api.put(`/applications/${appId}/status`, { status });
      toast.success(`Candidate marked as ${status}.`);
      fetchCandidates();
    } catch (err) {
      toast.error('Failed to update status.');
    }
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
      <div className="section-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <button className="btn btn-icon btn-secondary" onClick={() => navigate('/jobs')}>
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 className="section-title">Candidate Rankings</h1>
            <p className="section-subtitle">Ranked evaluation for <b>{data?.job?.title}</b></p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary" onClick={() => navigate('/analytics')}>
            Skill Clusters <Brain size={16} />
          </button>
          <button className="btn btn-primary">
            Export Report <Download size={16} />
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="card" style={{ marginBottom: 24, padding: '16px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: 12 }}>
            <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <Filter size={16} /> Filter by:
            </span>
            <button 
              className={`btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter('all')}
            >
              All Applicants ({data?.applications?.length || 0})
            </button>
            <button 
              className={`btn btn-sm ${filter === 'suitable' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter('suitable')}
            >
              AI Suitable
            </button>
            <button 
              className={`btn btn-sm ${filter === 'shortlisted' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter('shortlisted')}
            >
              Shortlisted
            </button>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Latest AI Model Version: <span style={{ color: 'var(--accent-light)' }}>v1.0.4</span>
          </div>
        </div>
      </div>

      {/* Candidate List */}
      <div style={rankingGridStyle}>
        {filteredApps.length > 0 ? (
          filteredApps.map((app, index) => (
            <div key={app.id} className="card animate-fade-up" style={{ animationDelay: `${index * 0.05}s` }}>
              <div style={cardLayout}>
                {/* Ranking Num */}
                <div style={rankBadgeStyle}>
                  #{index + 1}
                </div>

                <div style={mainInfoSection}>
                  <div style={userInfoHeader}>
                    <div style={userAvatarStyle}>
                      <User size={24} color="var(--accent-light)" />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '1.25rem', marginBottom: 2 }}>{app.candidate_name}</h3>
                      <div style={emailMeta}>
                        <Mail size={12} /> {app.candidate_email}
                      </div>
                    </div>
                  </div>

                  <div style={skillsContainer}>
                    {app.extracted_skills.length > 0 ? (
                      app.extracted_skills.slice(0, 8).map((skill, i) => (
                        <span key={i} className="skill-tag">{skill}</span>
                      ))
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>No skills extracted</span>
                    )}
                    {app.extracted_skills.length > 8 && (
                      <span className="skill-tag">+{app.extracted_skills.length - 8} more</span>
                    )}
                  </div>

                  <div style={metricsRow}>
                    <div style={metricItem}>
                      <Clock size={14} /> <span><b>{app.experience_years}</b> yrs Exp</span>
                    </div>
                    <div style={metricItem}>
                      <Calendar size={14} /> <span>Applied {new Date(app.applied_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                {/* AI Scores Section */}
                <div style={aiSection}>
                  <div style={aiLabel}>AI EVALUATION</div>
                  <ScoreBadge prediction={app.prediction} prob={app.prediction_prob} rankScore={app.rank_score} />
                </div>

                {/* Actions */}
                <div style={actionSection}>
                  <div style={statusLabel}>Status: <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{app.status}</span></div>
                  <div style={actionButtonGroup}>
                    <button 
                      className="btn btn-secondary btn-sm" 
                      onClick={() => updateStatus(app.id, 'shortlisted')}
                      disabled={app.status === 'shortlisted'}
                    >
                      <CheckCircle size={14} /> Shortlist
                    </button>
                    <button 
                      className="btn btn-secondary btn-sm"
                      onClick={() => updateStatus(app.id, 'rejected')}
                      disabled={app.status === 'rejected'}
                    >
                      <XCircle size={14} /> Reject
                    </button>
                    <button className="btn btn-primary btn-sm btn-icon">
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="card">
            <div className="empty-state">
              <Users size={48} style={{ opacity: 0.1, marginBottom: 16 }} />
              <h3>No candidates match this filter</h3>
              <p>Try changing your filter settings or checking back later.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const rankingGridStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '16px',
};

const cardLayout = {
  display: 'flex',
  alignItems: 'center',
  gap: '24px',
};

const rankBadgeStyle = {
  fontSize: '1.5rem',
  fontWeight: 800,
  color: 'rgba(255,255,255,0.1)',
  fontFamily: 'Space Grotesk, sans-serif',
  minWidth: '40px',
  textAlign: 'center',
};

const mainInfoSection = {
  flex: 1,
};

const userInfoHeader = {
  display: 'flex',
  alignItems: 'center',
  gap: '16px',
  marginBottom: '12px',
};

const userAvatarStyle = {
  width: 48, height: 48,
  borderRadius: 12,
  background: 'rgba(124, 58, 237, 0.1)',
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  border: '1px solid rgba(124, 58, 237, 0.2)',
};

const emailMeta = {
  fontSize: '0.8rem',
  color: 'var(--text-muted)',
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
};

const skillsContainer = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: '6px',
  marginBottom: '16px',
};

const metricsRow = {
  display: 'flex',
  gap: '20px',
};

const metricItem = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  fontSize: '0.8rem',
  color: 'var(--text-secondary)',
};

const aiSection = {
  width: '180px',
  borderLeft: '1px solid var(--border)',
  borderRight: '1px solid var(--border)',
  padding: '0 24px',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
};

const aiLabel = {
  fontSize: '0.65rem',
  fontWeight: 700,
  color: 'var(--text-muted)',
  letterSpacing: '0.1em',
  marginBottom: '8px',
};

const actionSection = {
  width: '220px',
  paddingLeft: '8px',
  display: 'flex',
  flexDirection: 'column',
  gap: '12px',
};

const statusLabel = {
  fontSize: '0.75rem',
  color: 'var(--text-muted)',
};

const actionButtonGroup = {
  display: 'flex',
  gap: '8px',
};
