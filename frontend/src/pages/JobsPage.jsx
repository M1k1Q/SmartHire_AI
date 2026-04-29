import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { 
  Briefcase, Plus, Search, Trash2, Edit3, 
  ExternalLink, X, MapPin, DollarSign, Calendar
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

export default function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    required_skills: '',
  });
  const navigate = useNavigate();

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const res = await api.get('/jobs');
      setJobs(res.data.jobs);
    } catch (err) {
      toast.error('Failed to load job postings.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        required_skills: formData.required_skills.split(',').map(s => s.trim()).filter(s => s),
      };
      await api.post('/jobs', payload);
      toast.success('Job posting created successfully!');
      setShowModal(false);
      setFormData({ title: '', description: '', required_skills: '' });
      fetchJobs();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create job.');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this job posting?')) return;
    try {
      await api.delete(`/jobs/${id}`);
      toast.success('Job deleted.');
      fetchJobs();
    } catch (err) {
      toast.error('Failed to delete job.');
    }
  };

  const filteredJobs = jobs.filter(job => 
    job.title.toLowerCase().includes(search.toLowerCase()) ||
    job.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="animate-fade">
      <div className="section-header">
        <div>
          <h1 className="section-title">Job Postings</h1>
          <p className="section-subtitle">Manage your active listings and find the best global talent</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={18} /> Create New Job
        </button>
      </div>

      {/* Toolbar */}
      <div className="card" style={{ marginBottom: '24px', padding: '16px' }}>
        <div style={toolbarStyle}>
          <div style={searchWrapperStyle}>
            <Search size={18} style={searchIconStyle} />
            <input 
              type="text" 
              className="form-control" 
              placeholder="Search by title or description..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '44px' }}
            />
          </div>
          <div className="badge badge-info">{filteredJobs.length} Jobs Found</div>
        </div>
      </div>

      {/* Jobs Grid */}
      <div style={jobsGridStyle}>
        {loading ? (
          <div className="loading-overlay" style={{ gridColumn: '1 / -1' }}>
            <div className="spinner" />
          </div>
        ) : filteredJobs.length > 0 ? (
          filteredJobs.map((job) => (
            <div key={job.id} className="card animate-fade-up">
              <div style={jobHeaderStyle}>
                <div style={jobIconStyle}>
                  <Briefcase size={20} color="var(--accent-light)" />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.1rem', marginBottom: '2px' }}>{job.title}</h3>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', gap: 12 }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <Calendar size={12} /> {new Date(job.created_at).toLocaleDateString()}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <Calendar size={12} /> Remote
                    </span>
                  </div>
                </div>
              </div>

              <p style={jobDescStyle}>{job.description.length > 120 ? job.description.substring(0, 120) + '...' : job.description}</p>

              <div style={tagCloudStyle}>
                {job.required_skills.slice(0, 5).map((skill, idx) => (
                  <span key={idx} className="skill-tag">{skill}</span>
                ))}
                {job.required_skills.length > 5 && (
                  <span className="skill-tag">+{job.required_skills.length - 5} more</span>
                )}
              </div>

              <div style={jobFooterStyle}>
                <button 
                  className="btn btn-primary btn-sm"
                  onClick={() => navigate(`/jobs/${job.id}/candidates`)}
                >
                  View Rankings <ExternalLink size={14} />
                </button>
                <div style={actionsStyle}>
                  <button className="btn btn-icon btn-secondary" title="Edit">
                    <Edit3 size={16} />
                  </button>
                  <button className="btn btn-icon btn-danger" title="Delete" onClick={() => handleDelete(job.id)}>
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
            <Briefcase size={48} className="empty-state-icon" style={{ opacity: 0.2 }} />
            <h3>No jobs found</h3>
            <p>Ready to hire? Create your first job posting above.</p>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showModal && (
        <div style={modalOverlayStyle}>
          <div className="card animate-fade-up" style={modalContentStyle}>
            <div className="card-header" style={{ marginBottom: 24 }}>
              <h3 className="card-title">Launch New Job Posting</h3>
              <button className="btn btn-icon btn-secondary" onClick={() => setShowModal(false)}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label className="form-label">Job Title</label>
                <input 
                  className="form-control" 
                  placeholder="e.g. Senior Full-Stack Engineer" 
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea 
                  className="form-control" 
                  placeholder="Describe the role, responsibilities, and team..." 
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Required Skills (comma separated)</label>
                <input 
                  className="form-control" 
                  placeholder="Python, React, AWS, Docker..." 
                  value={formData.required_skills}
                  onChange={(e) => setFormData({ ...formData, required_skills: e.target.value })}
                  required
                />
              </div>

              <div style={{ display: 'flex', gap: 12, marginTop: 32 }}>
                <button type="button" className="btn btn-secondary btn-full" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-full">
                  Create Job Posting
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

const toolbarStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: '16px',
};

const searchWrapperStyle = {
  position: 'relative',
  flex: 1,
};

const searchIconStyle = {
  position: 'absolute',
  left: '16px',
  top: '50%',
  transform: 'translateY(-50%)',
  color: 'var(--text-muted)',
};

const jobsGridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
  gap: '24px',
};

const jobHeaderStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '14px',
  marginBottom: '16px',
};

const jobIconStyle = {
  width: 44,
  height: 44,
  background: 'rgba(124, 58, 237, 0.1)',
  borderRadius: '10px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  border: '1px solid rgba(124, 58, 237, 0.2)',
};

const jobDescStyle = {
  fontSize: '0.875rem',
  color: 'var(--text-secondary)',
  lineHeight: 1.6,
  marginBottom: '20px',
  height: '4.8em',
  overflow: 'hidden',
};

const tagCloudStyle = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: '8px',
  marginBottom: '24px',
};

const jobFooterStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  paddingTop: '20px',
  borderTop: '1px solid var(--border)',
};

const actionsStyle = {
  display: 'flex',
  gap: '8px',
};

const modalOverlayStyle = {
  position: 'fixed',
  top: 0, left: 0, right: 0, bottom: 0,
  background: 'rgba(0,0,0,0.8)',
  backdropFilter: 'blur(8px)',
  zIndex: 1000,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '24px',
};

const modalContentStyle = {
  width: '100%',
  maxWidth: '560px',
  maxHeight: '90vh',
  overflowY: 'auto',
  padding: '32px',
};
