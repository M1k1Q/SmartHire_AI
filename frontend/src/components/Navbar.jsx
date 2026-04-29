// components/Navbar.jsx — Top navigation bar
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogOut, User, Bell } from 'lucide-react';
import toast from 'react-hot-toast';

const styles = {
  navbar: {
    position: 'fixed',
    top: 0,
    left: 'var(--sidebar-w)',
    right: 0,
    height: 'var(--navbar-h)',
    background: 'rgba(6,8,24,0.85)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    borderBottom: '1px solid var(--border)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 32px',
    zIndex: 100,
  },
  left: { display: 'flex', alignItems: 'center', gap: 12 },
  greeting: { fontSize: '0.9rem', color: 'var(--text-secondary)' },
  name: { color: 'var(--text-primary)', fontWeight: 600 },
  right: { display: 'flex', alignItems: 'center', gap: 12 },
  avatar: {
    width: 38, height: 38,
    borderRadius: '50%',
    background: 'var(--gradient-main)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: '0.85rem', fontWeight: 700, color: '#fff',
    cursor: 'pointer',
    flexShrink: 0,
  },
  userInfo: { textAlign: 'right' },
  userName: { fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' },
  userRole: {
    fontSize: '0.72rem', fontWeight: 600,
    padding: '2px 8px', borderRadius: 'var(--radius-full)',
    background: 'var(--accent-glow)', color: 'var(--accent-light)',
    textTransform: 'uppercase', letterSpacing: '0.05em',
  },
  logoutBtn: {
    display: 'flex', alignItems: 'center', gap: 6,
    padding: '8px 14px',
    background: 'rgba(239,68,68,0.1)',
    border: '1px solid rgba(239,68,68,0.25)',
    borderRadius: 'var(--radius-md)',
    color: '#ef4444',
    fontSize: '0.8rem', fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
};

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully.');
  };

  const initials = user?.name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'U';

  return (
    <header style={styles.navbar}>
      <div style={styles.left}>
        <span style={styles.greeting}>
          Welcome back, <span style={styles.name}>{user?.name?.split(' ')[0]}</span>
        </span>
      </div>

      <div style={styles.right}>
        <div style={styles.userInfo}>
          <div style={styles.userName}>{user?.name}</div>
          <span style={styles.userRole}>{user?.role}</span>
        </div>
        <div style={styles.avatar}>{initials}</div>
        <button style={styles.logoutBtn} onClick={handleLogout}
          onMouseEnter={e => e.currentTarget.style.background = 'rgba(239,68,68,0.2)'}
          onMouseLeave={e => e.currentTarget.style.background = 'rgba(239,68,68,0.1)'}
        >
          <LogOut size={14} /> Logout
        </button>
      </div>
    </header>
  );
}
