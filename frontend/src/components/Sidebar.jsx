// components/Sidebar.jsx — Left navigation sidebar
import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, Briefcase, Users, BarChart3,
  Brain, FileText, ChevronRight
} from 'lucide-react';

const HR_LINKS = [
  { path: '/',           label: 'Dashboard',  icon: LayoutDashboard },
  { path: '/jobs',       label: 'Job Postings', icon: Briefcase },
  { path: '/analytics',  label: 'Analytics & AI', icon: BarChart3 },
];

const CANDIDATE_LINKS = [
  { path: '/dashboard', label: 'My Dashboard', icon: LayoutDashboard },
];

export default function Sidebar() {
  const { user } = useAuth();
  const location = useLocation();
  const links = user?.role === 'hr' ? HR_LINKS : CANDIDATE_LINKS;

  return (
    <aside style={sidebarStyle}>
      {/* Logo */}
      <div style={logoContainer}>
        <div style={logoIcon}>
          <Brain size={22} color="#fff" />
        </div>
        <div>
          <div style={logoText}>SmartHire</div>
          <div style={logoSub}>AI Platform</div>
        </div>
      </div>

      <div style={divider} />

      {/* Role badge */}
      <div style={roleBadge}>
        <div style={roleIndicator} />
        <span style={{ fontSize: '0.75rem', color: 'var(--accent-light)', fontWeight: 600 }}>
          {user?.role === 'hr' ? 'HR Administrator' : 'Candidate'}
        </span>
      </div>

      {/* Navigation Links */}
      <nav style={{ padding: '8px 12px', flex: 1 }}>
        <div style={navLabel}>NAVIGATION</div>
        {links.map(({ path, label, icon: Icon }) => {
          const isActive = location.pathname === path;
          return (
            <NavLink
              key={path} to={path}
              style={{
                ...navLink,
                background: isActive ? 'rgba(124,58,237,0.18)' : 'transparent',
                color: isActive ? 'var(--accent-light)' : 'var(--text-secondary)',
                borderLeft: isActive ? '3px solid var(--accent)' : '3px solid transparent',
              }}
            >
              <Icon size={17} />
              <span>{label}</span>
              {isActive && <ChevronRight size={14} style={{ marginLeft: 'auto', opacity: 0.7 }} />}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={sidebarFooter}>
        <div style={footerText}>SmartHire AI v1.0</div>
        <div style={{ ...footerText, fontSize: '0.7rem', opacity: 0.5, marginTop: 2 }}>
          Powered by scikit-learn
        </div>
      </div>
    </aside>
  );
}

const sidebarStyle = {
  position: 'fixed', left: 0, top: 0, bottom: 0,
  width: 'var(--sidebar-w)',
  background: 'rgba(6,8,24,0.97)',
  borderRight: '1px solid var(--border)',
  display: 'flex', flexDirection: 'column',
  zIndex: 200,
  backdropFilter: 'blur(20px)',
};
const logoContainer = {
  display: 'flex', alignItems: 'center', gap: 12,
  padding: '22px 20px 18px',
};
const logoIcon = {
  width: 40, height: 40,
  background: 'var(--gradient-main)',
  borderRadius: 10,
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  boxShadow: 'var(--shadow-btn)',
  flexShrink: 0,
};
const logoText  = { fontSize: '1.1rem', fontWeight: 800, fontFamily: 'Space Grotesk,sans-serif', color: 'var(--text-primary)' };
const logoSub   = { fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 1 };
const divider   = { height: 1, background: 'var(--border)', margin: '0 16px' };
const roleBadge = { display: 'flex', alignItems: 'center', gap: 8, padding: '12px 20px' };
const roleIndicator = { width: 7, height: 7, borderRadius: '50%', background: 'var(--accent)', boxShadow: '0 0 8px var(--accent)' };
const navLabel  = { fontSize: '0.67rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.08em', padding: '12px 8px 8px' };
const navLink   = {
  display: 'flex', alignItems: 'center', gap: 10,
  padding: '10px 12px', borderRadius: 'var(--radius-md)',
  margin: '2px 0', fontSize: '0.875rem', fontWeight: 500,
  transition: 'all 0.2s', textDecoration: 'none',
};
const sidebarFooter = { padding: '16px 20px', borderTop: '1px solid var(--border)' };
const footerText    = { fontSize: '0.75rem', color: 'var(--text-muted)' };
