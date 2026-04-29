// components/BiasReport.jsx — Fairness and bias analysis panel
import React from 'react';
import { Shield, AlertTriangle, CheckCircle } from 'lucide-react';
import { RadialBarChart, RadialBar, ResponsiveContainer, Tooltip } from 'recharts';

export default function BiasReport({ report }) {
  if (!report || report.error) {
    return (
      <div className="empty-state" style={{ padding: 32 }}>
        <Shield size={36} style={{ color: 'var(--text-muted)' }} />
        <h3>No bias data available yet</h3>
        <p>Submit more applications to generate a fairness report.</p>
      </div>
    );
  }

  const suitable    = report.suitable_count || 0;
  const notSuitable = report.not_suitable_count || 0;
  const total       = report.total_applications || 0;
  const suitableRate = Math.round((report.suitable_rate || 0) * 100);
  const stats       = report.score_statistics || {};
  const flags       = report.bias_flags || [];

  const radialData = [
    { name: 'Suitable',     value: suitable,    fill: 'var(--success)' },
    { name: 'Not Suitable', value: notSuitable, fill: 'var(--danger)' },
  ];

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 8,
          background: 'rgba(124,58,237,0.2)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Shield size={18} color="var(--accent-light)" />
        </div>
        <div>
          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Fairness & Bias Analysis</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Based on {total} applications
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
        {[
          { label: 'Total Applications', value: total, color: 'var(--accent-light)' },
          { label: 'Suitable Rate',      value: `${suitableRate}%`, color: 'var(--success)' },
          { label: 'Avg Match Score',    value: `${Math.round((stats.mean || 0) * 100)}%`, color: 'var(--accent-2)' },
          { label: 'Score Std Dev',      value: stats.std?.toFixed(3) || '0', color: 'var(--warning)' },
        ].map(({ label, value, color }) => (
          <div key={label} style={{
            background: 'rgba(255,255,255,0.04)', borderRadius: 10,
            padding: '14px 16px', border: '1px solid var(--border)',
          }}>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color, marginBottom: 2 }}>{value}</div>
            <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)' }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Score distribution */}
      {stats.min !== undefined && (
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 10 }}>
            Score Distribution
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {[
              { label: 'Min',    val: stats.min },
              { label: 'Q25',    val: stats.q25 },
              { label: 'Median', val: stats.median },
              { label: 'Q75',    val: stats.q75 },
              { label: 'Max',    val: stats.max },
            ].map(({ label, val }) => (
              <div key={label} style={{
                textAlign: 'center', padding: '8px 12px',
                background: 'rgba(124,58,237,0.1)',
                border: '1px solid var(--border-accent)',
                borderRadius: 8,
              }}>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--accent-light)' }}>
                  {(val * 100).toFixed(0)}%
                </div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fairness flags */}
      <div>
        <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>
          Fairness Flags
        </div>
        {flags.map((flag, i) => {
          const isOk = flag.startsWith('✅');
          return (
            <div key={i} style={{
              display: 'flex', alignItems: 'flex-start', gap: 8,
              padding: '10px 14px', borderRadius: 8, marginBottom: 6,
              background: isOk ? 'var(--success-bg)' : 'var(--warning-bg)',
              border: `1px solid ${isOk ? 'rgba(16,185,129,0.3)' : 'rgba(245,158,11,0.3)'}`,
              fontSize: '0.8rem', color: isOk ? 'var(--success)' : 'var(--warning)',
            }}>
              {isOk ? <CheckCircle size={14} style={{ flexShrink: 0, marginTop: 2 }} />
                     : <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: 2 }} />}
              {flag.replace(/^[✅⚠️]\s*/, '')}
            </div>
          );
        })}
      </div>

      {/* Fairness note */}
      <div style={{
        marginTop: 16, padding: '12px 14px',
        background: 'rgba(6,182,212,0.08)', border: '1px solid rgba(6,182,212,0.2)',
        borderRadius: 8, fontSize: '0.78rem', color: 'var(--accent-2)',
        lineHeight: 1.6,
      }}>
        🛡️ {report.fairness_note}
      </div>
    </div>
  );
}
