import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { 
  Briefcase, Send, Clock, Search, FileText, 
  MapPin, CheckCircle2, ChevronRight, X
} from 'lucide-react';
import toast from 'react-hot-toast';
import ResumeUploader from '../components/ResumeUploader';
import ScoreBadge from '../components/ScoreBadge';

export default function CandidateDashboard() {
  const [jobs, setJobs] = useState([]);
  const [myApps, setMyApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedJob, setSelectedJob] = useState(null);
  const [viewingJob, setViewingJob] = useState(null);
  const [resumeFile, setResumeFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [jobsRes, appsRes] = await Promise.all([
        api.get('/jobs'),
        api.get('/applications/my')
      ]);
      setJobs(jobsRes.data.jobs);
      setMyApps(appsRes.data.applications);
    } catch (err) {
      toast.error('Failed to load dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async (e) => {
    e.preventDefault();
    if (!resumeFile) {
      return toast.error('Please upload your resume.');
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('job_id', selectedJob.id);
    formData.append('resume', resumeFile);

    try {
      await api.post('/applications', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('Application submitted! AI is evaluating your profile.');
      setSelectedJob(null);
      setResumeFile(null);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.error || 'failed to submit application.');
    } finally {
      setUploading(false);
    }
  };

  const filteredJobs = jobs.filter(j => 
    j.title.toLowerCase().includes(search.toLowerCase()) ||
    j.description.toLowerCase().includes(search.toLowerCase())
  );

  if (loading && jobs.length === 0) {
    return (
      <div className="loading-overlay">
        <div className="spinner" />
        <p>Fetching opportunities...</p>
      </div>
    );
  }

  return (
    <div className="animate-fade">
      <div className="section-header">
        <div>
          <h1 className="section-title">Candidate Dashboard</h1>
          <p className="section-subtitle">Browse jobs and track your AI-powered application progress</p>
        </div>
      </div>

      <div style={layoutGridStyle}>

        <div style={{ gridColumn: 'span 2' }}>
          <div className="card" style={{ marginBottom: 24, padding: '16px 24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Search size={20} color="var(--text-muted)" />
              <input 
                className="form-control" 
                placeholder="Search jobs by role or keywords..." 
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ background: 'transparent', border: 'none', boxShadow: 'none' }}
              />
            </div>
          </div>

          <div style={jobsListStyle}>
            {filteredJobs.map((job) => {
              const hasApplied = myApps.some(app => app.job_id === job.id);
              return (
                <div 
                  key={job.id} 
                  className="card" 
                  style={{ ...jobCardStyle, cursor: 'pointer' }}
                  onClick={() => setViewingJob(job)}
                >
                  <div style={jobInfoStyle}>
                    <div style={jobIconStyle}>
                      <Briefcase size={22} color="var(--accent-light)" />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '1.2rem', marginBottom: 4 }}>{job.title}</h3>
                      <div style={jobMetaStyle}>
                        <span><MapPin size={12} /> Remote</span>
                        <span>•</span>
                        <span>{job.required_skills.length} skills matched</span>
                      </div>
                    </div>
                  </div>
                  
                  <p style={jobDescStyle}>{job.description.length > 160 ? job.description.substring(0, 160) + '...' : job.description}</p>
                  
                  <div style={jobFooterStyle}>
                    <div style={skillsWrapperStyle}>
                      {job.required_skills.slice(0, 3).map((s, i) => (
                        <span key={i} className="skill-tag">{s}</span>
                      ))}
                    </div>
                    {hasApplied ? (
                      <div className="badge badge-success">
                        <CheckCircle2 size={14} /> Applied
                      </div>
                    ) : (
                      <button 
                        className="btn btn-primary btn-sm" 
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedJob(job);
                        }}
                      >
                        Apply Now <ChevronRight size={14} />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>


        <div>
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">My Applications</h3>
            </div>
            <div style={appsColumnStyle}>
              {myApps.length > 0 ? (
                myApps.map(app => (
                  <div key={app.id} style={appMiniCardStyle}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                        {app.job_title}
                      </div>
                      <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>{app.status}</span>
                    </div>
                    <ScoreBadge prediction={app.prediction} rankScore={app.rank_score} />
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 10 }}>
                      Applied {new Date(app.applied_at).toLocaleDateString()}
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty-state" style={{ padding: '20px 0' }}>
                  <FileText size={32} style={{ opacity: 0.2 }} />
                  <p style={{ fontSize: '0.85rem' }}>No applications yet.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>


      {viewingJob && (
        <div style={modalOverlayStyle} onClick={() => setViewingJob(null)}>
          <div className="card animate-fade-up" style={{ ...modalContentStyle, maxWidth: '650px' }} onClick={e => e.stopPropagation()}>
            <div className="card-header" style={{ marginBottom: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={jobIconStyle}>
                  <Briefcase size={24} color="var(--accent-light)" />
                </div>
                <div>
                  <h2 style={{ fontSize: '1.5rem', margin: 0 }}>{viewingJob.title}</h2>
                  <div style={jobMetaStyle}>
                    <span><MapPin size={14} /> Remote</span>
                    <span>•</span>
                    <span>Posted {new Date(viewingJob.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
              <button className="btn btn-icon btn-secondary" onClick={() => setViewingJob(null)}>
                <X size={20} />
              </button>
            </div>

            <div style={{ padding: '0 8px' }}>
              <div style={{ marginBottom: 32 }}>
                <h4 style={{ color: 'var(--text-primary)', marginBottom: 12, fontSize: '1.1rem' }}>Job Description</h4>
                <div style={{ color: 'var(--text-secondary)', lineHeight: 1.8, fontSize: '0.95rem', whiteSpace: 'pre-wrap' }}>
                  {viewingJob.description}
                </div>
              </div>

              <div style={{ marginBottom: 32 }}>
                <h4 style={{ color: 'var(--text-primary)', marginBottom: 12, fontSize: '1.1rem' }}>Required Skills</h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                  {viewingJob.required_skills.map((skill, idx) => (
                    <span key={idx} className="skill-tag" style={{ padding: '6px 14px', fontSize: '0.85rem' }}>{skill}</span>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', gap: 12, marginTop: 40, borderTop: '1px solid var(--border)', paddingTop: 24 }}>
                <button className="btn btn-secondary btn-full" onClick={() => setViewingJob(null)}>
                  Close Window
                </button>
                {!myApps.some(app => app.job_id === viewingJob.id) && (
                  <button 
                    className="btn btn-primary btn-full" 
                    onClick={() => {
                      setSelectedJob(viewingJob);
                      setViewingJob(null);
                    }}
                  >
                    Apply Now
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}


      {selectedJob && (
        <div style={modalOverlayStyle}>
          <div className="card animate-fade-up" style={modalContentStyle}>
            <div className="card-header" style={{ marginBottom: 24 }}>
              <h3 className="card-title">Apply for {selectedJob.title}</h3>
              <button className="btn btn-icon btn-secondary" onClick={() => setSelectedJob(null)}>
                <X size={18} />
              </button>
            </div>
            
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: 24 }}>
              The AI will parse your resume to evaluate skills, extract experience, and calculate your fit for this role.
            </p>

            <form onSubmit={handleApply}>
              <div className="form-group">
                <label className="form-label">Upload Resume (PDF/DOCX)</label>
                <ResumeUploader onFileSelect={setResumeFile} disabled={uploading} />
              </div>

              <div style={{ display: 'flex', gap: 12, marginTop: 32 }}>
                <button type="button" className="btn btn-secondary btn-full" onClick={() => setSelectedJob(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-full" disabled={uploading || !resumeFile}>
                  {uploading ? 'Processing AI Pipeline...' : 'Submit Application'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

const layoutGridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(3, 1fr)',
  gap: '32px',
};

const jobsListStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '20px',
};

const jobCardStyle = {
  background: 'rgba(255, 255, 255, 0.03)',
  transition: 'transform 0.2s',
};

const jobInfoStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '16px',
  marginBottom: '16px',
};

const jobIconStyle = {
  width: 50, height: 50,
  background: 'rgba(124, 58, 237, 0.1)',
  borderRadius: 12,
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  border: '1px solid rgba(124, 58, 237, 0.2)',
};

const jobMetaStyle = {
  display: 'flex', gap: 12, alignItems: 'center',
  fontSize: '0.8rem', color: 'var(--text-muted)',
};

const jobDescStyle = {
  fontSize: '0.9rem', color: 'var(--text-secondary)',
  lineHeight: 1.6, marginBottom: 20,
};

const jobFooterStyle = {
  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
  paddingTop: 16, borderTop: '1px solid var(--border)',
};

const skillsWrapperStyle = {
  display: 'flex', gap: 8,
};

const appsColumnStyle = {
  display: 'flex', flexDirection: 'column', gap: '12px',
};

const appMiniCardStyle = {
  padding: '16px',
  background: 'rgba(255,255,255,0.02)',
  borderRadius: 'var(--radius-md)',
  border: '1px solid var(--border)',
};

const modalOverlayStyle = {
  position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
  background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(8px)',
  zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
  padding: 24,
};

const modalContentStyle = {
  width: '100%', maxWidth: '500px',
};
