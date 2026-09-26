import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { Flame, RefreshCw, ArrowRight, ShieldAlert, FolderGit2, CheckCircle2, AlertTriangle } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function Dashboard() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterLevel, setFilterLevel] = useState('ALL');

  useEffect(() => {
    fetchPrioritizedProjects();
  }, []);

  const fetchPrioritizedProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/projects/prioritized`);
      if (!res.ok) {
        const fallbackRes = await fetch(`${API_BASE_URL}/projects`);
        if (!fallbackRes.ok) throw new Error(`Server returned status ${fallbackRes.status}`);
        const fallbackData = await fallbackRes.json();
        setProjects(fallbackData);
      } else {
        const data = await res.json();
        setProjects(data.prioritized_attention_list || []);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch project portfolio data');
    } finally {
      setLoading(false);
    }
  };

  const totalProjects = projects.length;
  let lowCount = 0;
  let mediumCount = 0;
  let highCount = 0;
  let unanalyzedCount = 0;
  let criticalUrgencyCount = 0;

  projects.forEach((p) => {
    const risk = p.risk_level || (p.most_recent_prediction ? p.most_recent_prediction.risk_level : null);
    if (risk === 'Low') lowCount++;
    else if (risk === 'Medium') mediumCount++;
    else if (risk === 'High') highCount++;
    else unanalyzedCount++;

    if (p.urgency_level === 'CRITICAL' || p.urgency_score >= 6.0) {
      criticalUrgencyCount++;
    }
  });

  const chartData = [
    { name: 'Low Risk', value: lowCount, color: '#10B981' },
    { name: 'Medium Risk', value: mediumCount, color: '#F59E0B' },
    { name: 'High Risk', value: highCount, color: '#F43F5E' },
    ...(unanalyzedCount > 0 ? [{ name: 'Unanalyzed', value: unanalyzedCount, color: '#64748B' }] : [])
  ].filter(item => item.value > 0);

  const filteredProjects = projects.filter(p => {
    if (filterLevel === 'ALL') return true;
    if (filterLevel === 'CRITICAL') return p.urgency_level === 'CRITICAL';
    if (filterLevel === 'HIGH_RISK') return p.risk_level === 'High';
    if (filterLevel === 'STALE') return p.weeks_stale >= 2.0;
    return true;
  });

  return (
    <div className="page-transition space-y-6">
      
      {/* Hero Header Banner with Gradient Accent */}
      <div className="bg-gradient-to-r from-[#0F172A] via-[#1E293B] to-[#0F172A] p-6 rounded-2xl border border-[#1E293B] shadow-2xl text-white flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5 font-heading">
            <ShieldAlert className="w-6 h-6 text-cyan-400" />
            Portfolio Overview & Risk Prioritization
          </h1>
          <p className="text-xs text-slate-300 font-medium mt-1">
            Real-time multi-factor urgency scoring (Risk Weight × Confidence + Escalation + Staleness)
          </p>
        </div>
        <button
          onClick={fetchPrioritizedProjects}
          className="btn-secondary self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${loading ? 'animate-spin' : ''}`} />
          Refresh Portfolio
        </button>
      </div>

      {/* Glassmorphic Multi-Color KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        
        {/* Monitored Projects Card - Cyan Accent */}
        <div className="glass-card p-5 border-l-4 border-l-cyan-500 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">
              Monitored Projects
            </span>
            <FolderGit2 className="w-4 h-4 text-cyan-400" />
          </div>
          <span className="text-3xl font-bold text-white font-mono">
            {loading ? '...' : totalProjects}
          </span>
        </div>

        {/* Critical Urgency Card - Rose Red Accent */}
        <div className="glass-card p-5 border-l-4 border-l-rose-500 space-y-1 shadow-[0_0_20px_rgba(244,63,94,0.1)]">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider">
              Critical Urgency
            </span>
            <Flame className="w-4 h-4 text-rose-500 animate-pulse" />
          </div>
          <span className="text-3xl font-bold text-rose-400 font-mono">
            {loading ? '...' : criticalUrgencyCount}
          </span>
        </div>

        {/* High Risk Card - Amber Gold Accent */}
        <div className="glass-card p-5 border-l-4 border-l-amber-500 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
              High Risk Projects
            </span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <span className="text-3xl font-bold text-amber-400 font-mono">
            {loading ? '...' : highCount}
          </span>
        </div>

        {/* Healthy Projects Card - Emerald Green Accent */}
        <div className="glass-card p-5 border-l-4 border-l-emerald-500 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
              Healthy Projects
            </span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <span className="text-3xl font-bold text-emerald-400 font-mono">
            {loading ? '...' : lowCount}
          </span>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Risk Distribution Chart */}
        <div className="lg:col-span-4 glass-card p-5 space-y-4">
          <h2 className="text-base font-semibold text-white border-b border-[#1E293B] pb-3 font-heading flex items-center justify-between">
            <span>Risk Distribution</span>
            <span className="text-xs font-mono text-cyan-400 font-normal">Active Breakdown</span>
          </h2>

          {loading ? (
            <div className="flex items-center justify-center h-56 text-slate-400 text-xs font-medium">
              Loading distribution chart...
            </div>
          ) : chartData.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-56 text-slate-400 text-xs space-y-2 text-center">
              <span>No project predictions stored yet</span>
              <NavLink to="/input" className="text-cyan-400 font-semibold hover:underline">
                Evaluate your first project →
              </NavLink>
            </div>
          ) : (
            <div className="h-56 w-full flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={48}
                    outerRadius={76}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0B101D', borderColor: '#1E2842', borderRadius: '10px', color: '#FFFFFF', fontSize: '12px' }}
                    itemStyle={{ color: '#FFFFFF', fontWeight: 600 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Chart Legend Pills */}
          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-[#1E293B] text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.5)]"></span>
              <span className="text-slate-300 font-medium">Healthy ({lowCount})</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.5)]"></span>
              <span className="text-slate-300 font-medium">Medium ({mediumCount})</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.5)]"></span>
              <span className="text-slate-300 font-medium">High Risk ({highCount})</span>
            </div>
            {unanalyzedCount > 0 && (
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-500"></span>
                <span className="text-slate-300 font-medium">Unanalyzed ({unanalyzedCount})</span>
              </div>
            )}
          </div>
        </div>

        {/* Prioritized Attention List */}
        <div className="lg:col-span-8 glass-card space-y-4 overflow-hidden p-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#1E293B] pb-3">
            <h2 className="text-base font-semibold text-white font-heading">
              Prioritized Attention List
            </h2>

            {/* Filter Pills with Distinct Active Colors */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <button
                onClick={() => setFilterLevel('ALL')}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                  filterLevel === 'ALL'
                    ? 'bg-cyan-600 text-white shadow-[0_0_10px_rgba(6,182,212,0.4)]'
                    : 'bg-[#090D16] text-slate-400 hover:text-white border border-[#1E293B]'
                }`}
              >
                All ({totalProjects})
              </button>
              <button
                onClick={() => setFilterLevel('CRITICAL')}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                  filterLevel === 'CRITICAL'
                    ? 'bg-rose-600 text-white shadow-[0_0_10px_rgba(244,63,94,0.4)]'
                    : 'bg-[#090D16] text-slate-400 hover:text-white border border-[#1E293B]'
                }`}
              >
                Critical Urgency
              </button>
              <button
                onClick={() => setFilterLevel('HIGH_RISK')}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                  filterLevel === 'HIGH_RISK'
                    ? 'bg-amber-600 text-white shadow-[0_0_10px_rgba(245,158,11,0.4)]'
                    : 'bg-[#090D16] text-slate-400 hover:text-white border border-[#1E293B]'
                }`}
              >
                High Risk
              </button>
            </div>
          </div>

          {/* Table View */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-200">
              <thead className="bg-[#090D16] text-slate-400 font-semibold uppercase tracking-wider border-b border-[#1E293B]">
                <tr>
                  <th className="py-2.5 px-3">Project</th>
                  <th className="py-2.5 px-3">Risk Level</th>
                  <th className="py-2.5 px-3 font-mono">Urgency Score</th>
                  <th className="py-2.5 px-3 font-mono">Last Evaluated</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E293B]/60">
                {filteredProjects.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-400">
                      No projects match the selected filter.
                    </td>
                  </tr>
                ) : (
                  filteredProjects.map((p) => {
                    const risk = p.risk_level || (p.most_recent_prediction ? p.most_recent_prediction.risk_level : 'Unanalyzed');
                    return (
                      <tr key={p.project_id} className="hover:bg-[#1E293B]/40 transition">
                        <td className="py-3 px-3">
                          <div className="font-semibold text-white">{p.project_name}</div>
                          <div className="font-mono text-[11px] text-cyan-400">{p.project_id}</div>
                        </td>
                        <td className="py-3 px-3">
                          {risk === 'Low' && (
                            <span className="badge-risk-low">Healthy</span>
                          )}
                          {risk === 'Medium' && (
                            <span className="badge-risk-medium">Medium Risk</span>
                          )}
                          {risk === 'High' && (
                            <span className="badge-risk-high">High Risk</span>
                          )}
                          {risk === 'Unanalyzed' && (
                            <span className="bg-[#090D16] text-slate-400 border border-[#1E293B] font-medium px-2.5 py-0.5 rounded-lg text-[11px]">
                              Unanalyzed
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-3 font-mono text-white font-bold">
                          {p.urgency_score ? p.urgency_score.toFixed(1) : '—'}
                        </td>
                        <td className="py-3 px-3 font-mono text-slate-400">
                          {p.created_date ? new Date(p.created_date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : '—'}
                        </td>
                        <td className="py-3 px-3 text-right">
                          <NavLink
                            to="/input"
                            className="btn-secondary text-[11px] py-1.5 px-3 no-underline inline-flex items-center gap-1"
                          >
                            Evaluate <ArrowRight className="w-3 h-3 text-cyan-400" />
                          </NavLink>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>

    </div>
  );
}

