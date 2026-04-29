// components/ClusterChart.jsx — t-SNE/PCA cluster scatter plot using Recharts
import React, { useState } from 'react';
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const CLUSTER_COLORS = ['#7c3aed', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  return (
    <div style={{
      background: 'rgba(6,8,24,0.95)', border: '1px solid var(--border)',
      borderRadius: 10, padding: '12px 16px', fontSize: '0.8rem',
      backdropFilter: 'blur(12px)', minWidth: 180,
    }}>
      <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
        {d?.candidate_name || 'Candidate'}
      </div>
      <div style={{ color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 4 }}>
        <span>Cluster: <b style={{ color: CLUSTER_COLORS[d?.cluster_id % CLUSTER_COLORS.length] }}>#{d?.cluster_id}</b></span>
        <span>Match Score: <b style={{ color: 'var(--accent-light)' }}>{Math.round((d?.rank_score || 0) * 100)}%</b></span>
        <span>Prediction: <b style={{ color: d?.prediction === 'Suitable' ? 'var(--success)' : 'var(--danger)' }}>{d?.prediction}</b></span>
      </div>
    </div>
  );
};

export default function ClusterChart({ data = [], nClusters = 0, silhouetteScore = 0 }) {
  const [hiddenClusters, setHiddenClusters] = useState(new Set());

  if (!data || data.length === 0) {
    return (
      <div className="empty-state" style={{ padding: 40 }}>
        <div className="empty-state-icon">📊</div>
        <h3>No cluster data available</h3>
        <p>Apply candidates to this job to see cluster visualization.</p>
      </div>
    );
  }

  // Group by cluster
  const clusters = {};
  data.forEach(point => {
    const key = point.cluster_id ?? 0;
    if (!clusters[key]) clusters[key] = [];
    clusters[key].push(point);
  });

  const toggleCluster = (clusterId) => {
    setHiddenClusters(prev => {
      const next = new Set(prev);
      next.has(clusterId) ? next.delete(clusterId) : next.add(clusterId);
      return next;
    });
  };

  return (
    <div>
      {/* Metadata row */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 20, flexWrap: 'wrap' }}>
        <div className="badge badge-purple">K = {nClusters} clusters</div>
        <div className="badge badge-info">
          Silhouette: {silhouetteScore.toFixed(3)}
        </div>
        <div className="badge" style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)', border: '1px solid var(--border)' }}>
          {data.length} candidates
        </div>
      </div>

      {/* Cluster toggles */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {Object.keys(clusters).map(cid => (
          <button key={cid} onClick={() => toggleCluster(parseInt(cid))} style={{
            padding: '4px 12px', borderRadius: 'var(--radius-full)',
            background: hiddenClusters.has(parseInt(cid)) ? 'rgba(255,255,255,0.03)' : `${CLUSTER_COLORS[parseInt(cid) % CLUSTER_COLORS.length]}22`,
            border: `1px solid ${CLUSTER_COLORS[parseInt(cid) % CLUSTER_COLORS.length]}55`,
            color: CLUSTER_COLORS[parseInt(cid) % CLUSTER_COLORS.length],
            fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer',
            opacity: hiddenClusters.has(parseInt(cid)) ? 0.4 : 1,
            transition: 'all 0.2s',
          }}>
            Cluster {cid} ({clusters[cid].length})
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={360}>
        <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="x" type="number" tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
            axisLine={false} tickLine={false} label={{ value: 'Component 1', position: 'insideBottom', offset: -2, fill: 'var(--text-muted)', fontSize: 11 }} />
          <YAxis dataKey="y" type="number" tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
            axisLine={false} tickLine={false} />
          <ZAxis range={[60, 60]} />
          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3', stroke: 'var(--border)' }} />
          {Object.entries(clusters).map(([cid, points]) => {
            if (hiddenClusters.has(parseInt(cid))) return null;
            const color = CLUSTER_COLORS[parseInt(cid) % CLUSTER_COLORS.length];
            return (
              <Scatter key={cid} name={`Cluster ${cid}`} data={points}
                fill={color} fillOpacity={0.75}
                stroke={color} strokeWidth={1.5}
              />
            );
          })}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
