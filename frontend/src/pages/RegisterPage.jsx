import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Brain, Mail, Lock, User, UserPlus, ArrowRight, Briefcase, GraduationCap } from 'lucide-react';
import toast from 'react-hot-toast';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'candidate',
  });
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const user = await register(formData.name, formData.email, formData.password, formData.role);
      toast.success(`Welcome, ${user.name}! Account created.`);
      navigate(user.role === 'hr' ? '/' : '/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={containerStyle}>
      <div className="animate-fade-up" style={cardStyle}>
        <div style={headerStyle}>
          <div style={logoIconStyle}>
            <Brain size={28} color="#fff" />
          </div>
          <h1 style={titleStyle}>Join SmartHire AI</h1>
          <p style={subtitleStyle}>Next-gen recruitment starts here</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <div style={inputWrapperStyle}>
              <User size={18} style={iconStyle} />
              <input
                name="name"
                type="text"
                className="form-control"
                placeholder="John Doe"
                value={formData.name}
                onChange={handleChange}
                required
                style={{ paddingLeft: '44px' }}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Email Address</label>
            <div style={inputWrapperStyle}>
              <Mail size={18} style={iconStyle} />
              <input
                name="email"
                type="email"
                className="form-control"
                placeholder="john@example.com"
                value={formData.email}
                onChange={handleChange}
                required
                style={{ paddingLeft: '44px' }}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div style={inputWrapperStyle}>
              <Lock size={18} style={iconStyle} />
              <input
                name="password"
                type="password"
                className="form-control"
                placeholder="••••••••"
                value={formData.password}
                onChange={handleChange}
                required
                style={{ paddingLeft: '44px' }}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">I am a...</label>
            <div style={roleGridStyle}>
              <div 
                style={{
                  ...roleCardStyle,
                  borderColor: formData.role === 'candidate' ? 'var(--accent)' : 'var(--border)',
                  background: formData.role === 'candidate' ? 'var(--accent-glow)' : 'transparent',
                }}
                onClick={() => setFormData({ ...formData, role: 'candidate' })}
              >
                <GraduationCap size={20} color={formData.role === 'candidate' ? 'var(--accent-light)' : 'var(--text-muted)'} />
                <span style={{ color: formData.role === 'candidate' ? 'var(--text-primary)' : 'var(--text-secondary)' }}>Candidate</span>
              </div>
              <div 
                style={{
                  ...roleCardStyle,
                  borderColor: formData.role === 'hr' ? 'var(--accent)' : 'var(--border)',
                  background: formData.role === 'hr' ? 'var(--accent-glow)' : 'transparent',
                }}
                onClick={() => setFormData({ ...formData, role: 'hr' })}
              >
                <Briefcase size={20} color={formData.role === 'hr' ? 'var(--accent-light)' : 'var(--text-muted)'} />
                <span style={{ color: formData.role === 'hr' ? 'var(--text-primary)' : 'var(--text-secondary)' }}>HR Manager</span>
              </div>
            </div>
          </div>

          <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading} style={{ marginTop: '12px' }}>
            {loading ? (
              <div className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }} />
            ) : (
              <>
                Create Account <UserPlus size={18} />
              </>
            )}
          </button>
        </form>

        <div style={footerStyle}>
          Already have an account? <Link to="/login" style={linkStyle}>Log in <ArrowRight size={14} /></Link>
        </div>
      </div>

      <div style={backgroundGlowStyle} />
    </div>
  );
}

const containerStyle = {
  minHeight: '100vh',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  background: 'var(--bg-primary)',
  padding: '24px',
  position: 'relative',
  overflow: 'hidden',
};

const cardStyle = {
  width: '100%',
  maxSize: '480px',
  maxWidth: '480px',
  background: 'rgba(13, 17, 23, 0.7)',
  backdropFilter: 'blur(16px)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-xl)',
  padding: '48px 40px',
  zIndex: 10,
  boxShadow: '0 24px 48px rgba(0,0,0,0.5)',
};

const headerStyle = {
  textAlign: 'center',
  marginBottom: '32px',
};

const logoIconStyle = {
  width: 56,
  height: 56,
  background: 'var(--gradient-main)',
  borderRadius: 16,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  margin: '0 auto 20px',
  boxShadow: 'var(--shadow-btn)',
};

const titleStyle = {
  fontSize: '1.75rem',
  marginBottom: '8px',
  background: 'var(--gradient-main)',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
};

const subtitleStyle = {
  color: 'var(--text-secondary)',
  fontSize: '0.9rem',
};

const inputWrapperStyle = {
  position: 'relative',
};

const iconStyle = {
  position: 'absolute',
  left: '16px',
  top: '50%',
  transform: 'translateY(-50%)',
  color: 'var(--text-muted)',
};

const roleGridStyle = {
  display: 'grid',
  gridTemplateColumns: '1fr 1fr',
  gap: '12px',
  marginTop: '4px',
};

const roleCardStyle = {
  padding: '12px',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-md)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '10px',
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  fontSize: '0.875rem',
  fontWeight: 600,
};

const footerStyle = {
  marginTop: '32px',
  textAlign: 'center',
  fontSize: '0.875rem',
  color: 'var(--text-secondary)',
};

const linkStyle = {
  color: 'var(--accent-light)',
  fontWeight: 600,
  display: 'inline-flex',
  alignItems: 'center',
  gap: '4px',
  marginLeft: '4px',
};

const backgroundGlowStyle = {
  position: 'absolute',
  width: '600px',
  height: '600px',
  borderRadius: '50%',
  background: 'radial-gradient(circle, var(--accent-glow) 0%, transparent 70%)',
  bottom: '-10%',
  left: '-10%',
  zIndex: 1,
  opacity: 0.5,
};
