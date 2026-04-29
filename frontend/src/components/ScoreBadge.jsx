// components/ScoreBadge.jsx — AI prediction badge with confidence bar
import React from 'react';
import { CheckCircle, XCircle, Clock } from 'lucide-react';

export default function ScoreBadge({ prediction, prob, rankScore }) {
  const isSuitable    = prediction === 'Suitable';
  const isNotSuitable = prediction === 'Not Suitable';
  const isPending     = prediction === 'Pending' || !prediction;

  const color  = isSuitable ? 'var(--success)'  : isNotSuitable ? 'var(--danger)'  : 'var(--warning)';
  const bgCol  = isSuitable ? 'var(--success-bg)': isNotSuitable ? 'var(--danger-bg)': 'var(--warning-bg)';
  const border = isSuitable ? 'rgba(16,185,129,0.3)': isNotSuitable ? 'rgba(239,68,68,0.3)': 'rgba(245,158,11,0.3)';
  const Icon   = isSuitable ? CheckCircle : isNotSuitable ? XCircle : Clock;

  const confPct  = prob ? Math.round(prob * 100) : null;
  const scorePct = rankScore ? Math.round(rankScore * 100) : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minWidth: 160 }}>
      {/* Prediction Badge */}
      <div style={{
        display: 'inline-flex', alignItems: 'center', gap: 6,
        padding: '5px 12px', borderRadius: 'var(--radius-full)',
        background: bgCol, color: color,
        border: `1px solid ${border}`,
        fontSize: '0.78rem', fontWeight: 600,
        width: 'fit-content',
      }}>
        <Icon size={13} />
        {isPending ? 'Pending' : prediction}
      </div>

      {/* Confidence */}
      {confPct !== null && (
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          Confidence: <span style={{ color: color, fontWeight: 600 }}>{confPct}%</span>
        </div>
      )}

      {/* Rank Score Bar */}
      {scorePct !== null && (
        <div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 3 }}>
            Match Score: <strong style={{ color: 'var(--text-secondary)' }}>{scorePct}%</strong>
          </div>
          <div className="progress-bar" style={{ width: 140 }}>
            <div className="progress-fill" style={{ width: `${scorePct}%` }} />
          </div>
        </div>
      )}
    </div>
  );
}
