import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Brain, Mail, Lock, LogIn, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const user = await login(email, password);
      toast.success(`Welcome back, ${user.name}!`);
      navigate(user.role === 'hr' ? '/' : '/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Login failed. Please check your credentials.');
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
          <h1 style={titleStyle}>SmartHire AI</h1>
          <p style={subtitleStyle}>Recruitment Intelligence Platform</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <div style={inputWrapperStyle}>
              <Mail size={18} style={iconStyle} />
              <input
                type="email"
                className="form-control"
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
                type="password"
                className="form-control"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{ paddingLeft: '44px' }}
              />
            </div>
          </div>

          <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading} style={{ marginTop: '12px' }}>
            {loading ? (
              <div className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }} />
            ) : (
              <>
                Sign In <LogIn size={18} />
              </>
            )}
          </button>
        </form>

        <div style={footerStyle}>
          Don't have an account? <Link to="/register" style={linkStyle}>Create one now <ArrowRight size={14} /></Link>
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
  maxSize: '440px',
  maxWidth: '440px',
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
  marginBottom: '40px',
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
  top: '-10%',
  right: '-10%',
  zIndex: 1,
  opacity: 0.5,
};
