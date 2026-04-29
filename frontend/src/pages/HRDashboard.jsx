import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { 
  Users, Briefcase, CheckCircle2, AlertCircle, 
  BarChart3, Clock, ArrowRight, Brain, TrendingUp, RefreshCw
} from 'lucide-react';
import toast from 'react-hot-toast';
import ScoreBadge from '../components/ScoreBadge';

export default function HRDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const navigate = useNavigate();

  const fetchStats = useCallback(async (isBackground = false) => {
    if (!isBackground) setRefreshing(true);
    try {
      const res = await api.get('/analytics/dashboard');
      setStats(res.data.stats);
    } catch (err) {
      if (!isBackground) toast.error('Failed to load dashboard statistics.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();

    // 1. Polling: Refresh every 60 seconds
    const interval = setInterval(() => {
      fetchStats(true);
    }, 60000);

    // 2. Focus Refresh: Update when user returns to tab
    const handleFocus = () => {
      fetchStats(true);
    };
    window.addEventListener('focus', handleFocus);
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') fetchStats(true);
    });

    return () => {
      clearInterval(interval);
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleFocus);
    };
  }, [fetchStats]);

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="spinner" />
        <p>Analyzing recruitment data...</p>
      </div>
    );
  }

  const statCards = [
    { label: 'Active Jobs', value: stats?.total_jobs || 0, icon: Briefcase, color: 'var(--accent-2)' },
    { label: 'Total Applications', value: stats?.total_applications || 0, icon: Users, color: 'var(--accent-light)' },
    { label: 'Suitable Candidates', value: stats?.suitable_count || 0, icon: CheckCircle2, color: 'var(--success)' },
    { label: 'Candidates Flagged', value: stats?.not_suitable_count || 0, icon: AlertCircle, color: 'var(--danger)' },
  ];

  return (
    <div className="animate-fade">
      <div className="section-header">
        <div>
          <h1 className="section-title">HR Overview</h1>
          <p className="section-subtitle">Real-time candidate evaluation & platform metrics</p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button 
            className={`btn btn-secondary ${refreshing ? 'loading' : ''}`} 
            onClick={() => fetchStats()}
            disabled={refreshing}
            title="Refresh statistics"
          >
            <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/jobs')}>
            Manage Jobs <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        {statCards.map((stat, i) => (
          <div key={i} className="stat-card" style={{ animationDelay: `${i * 0.1}s` }}>
            <div className="stat-icon" style={{ color: stat.color }}>
              <stat.icon size={24} />
            </div>
            <div className="stat-value">{stat.value}</div>
            <div className="stat-label">{stat.label}</div>
          </div>
        ))}
      </div>

      <div style={dashboardGridStyle}>
        {/* Recent Applications Table */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header">
            <h3 className="card-title">
              <Clock size={18} style={{ verticalAlign: 'middle', marginRight: 8, color: 'var(--accent)' }} />
              Recent Applications
            </h3>
            <span className="badge badge-purple">{stats?.recent_applications?.length || 0} New</span>
          </div>
          
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Applied For</th>
                  <th>AI Prediction</th>
                  <th>Applied At</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {stats?.recent_applications && stats.recent_applications.length > 0 ? (
                  stats.recent_applications.map((app) => (
                    <tr key={app.id}>
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{app.candidate_name}</div>
                      </td>
                      <td>
                        <div style={{ fontSize: '0.82rem' }}>{app.job_title}</div>
                      </td>
                      <td>
                        <ScoreBadge prediction={app.prediction} rankScore={app.rank_score} />
                      </td>
                      <td>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          {new Date(app.applied_at).toLocaleDateString()}
                        </div>
                      </td>
                      <td>
                        <button 
                          className="btn btn-secondary btn-sm"
                          onClick={() => navigate(`/jobs/${app.job_id}/candidates`)}
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', padding: '40px' }}>
                      <div className="empty-state">
                        <Clock size={32} style={{ opacity: 0.3 }} />
                        <p>No applications received yet.</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* AI Insight Card */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <Brain size={18} style={{ verticalAlign: 'middle', marginRight: 8, color: 'var(--accent-2)' }} />
              AI Platform Health
            </h3>
          </div>
          
          <div style={aiInsightStyle}>
            <div style={metricRowStyle}>
              <div style={metricLabelStyle}>
                <TrendingUp size={14} style={{ marginRight: 6 }} /> Match Precision
              </div>
              <div style={metricValueStyle}>92%</div>
            </div>
            <div className="progress-bar" style={{ marginBottom: 20 }}>
              <div className="progress-fill" style={{ width: '92%', background: 'var(--accent-2)' }} />
            </div>

            <div style={metricRowStyle}>
              <div style={metricLabelStyle}>Average Match Score</div>
              <div style={metricValueStyle}>{Math.round((stats?.avg_rank_score || 0) * 100)}%</div>
            </div>
            <div className="progress-bar" style={{ marginBottom: 24 }}>
              <div className="progress-fill" style={{ width: `${(stats?.avg_rank_score || 0) * 100}%` }} />
            </div>

            <div style={aiPromoCardStyle}>
              <div style={aiPromoTitleStyle}>Proactive Skill Clustering</div>
              <p style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.6)', margin: '8px 0 12px' }}>
                Our K-Means engine has identified 3 distinct skill clusters in your current talent pool.
              </p>
              <button className="btn btn-primary btn-sm btn-full" onClick={() => navigate('/analytics')}>
                View AI Analytics <BarChart3 size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const dashboardGridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(3, 1fr)',
  gap: '24px',
};

const aiInsightStyle = {
  padding: '4px 0',
};

const metricRowStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '8px',
};

const metricLabelStyle = {
  fontSize: '0.85rem',
  color: 'var(--text-secondary)',
  display: 'flex',
  alignItems: 'center',
};

const metricValueStyle = {
  fontWeight: 700,
  color: 'var(--text-primary)',
};

const aiPromoCardStyle = {
  background: 'rgba(124, 58, 237, 0.1)',
  border: '1px solid var(--border-accent)',
  borderRadius: 'var(--radius-md)',
  padding: '16px',
  marginTop: '8px',
};

const aiPromoTitleStyle = {
  fontSize: '0.9rem',
  fontWeight: 700,
  color: 'var(--accent-light)',
};
