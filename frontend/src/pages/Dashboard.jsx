import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import { ShieldAlert, AlertTriangle, Clock, TrendingUp, Flame, CheckCircle, ArrowRight, RefreshCw } from 'lucide-react';
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
        // Fallback to /projects
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

  // Compute portfolio metrics
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
    { name: 'Low Risk', value: lowCount, color: '#34D399' },
    { name: 'Medium Risk', value: mediumCount, color: '#FBBF24' },
    { name: 'High Risk', value: highCount, color: '#F5544D' },
    ...(unanalyzedCount > 0 ? [{ name: 'Unanalyzed', value: unanalyzedCount, color: '#8B95AC' }] : [])
  ].filter(item => item.value > 0);

  // Filtered projects
  const filteredProjects = projects.filter(p => {
    if (filterLevel === 'ALL') return true;
    if (filterLevel === 'CRITICAL') return p.urgency_level === 'CRITICAL';
    if (filterLevel === 'HIGH_RISK') return p.risk_level === 'High';
    if (filterLevel === 'STALE') return p.weeks_stale >= 2.0;
    return true;
  });

  return (
    <div className="page-transition space-y-6">
      {/* Page Title & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title">Portfolio Overview & Risk Prioritization</h1>
          <p className="small-label mt-1">
            Real-time multi-factor urgency scoring (Risk Weight × Confidence + Escalation + Staleness)
          </p>
        </div>
        <button onClick={fetchPrioritizedProjects} className="btn-secondary flex items-center gap-2 self-start sm:self-auto">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Portfolio
        </button>
      </div>

      {/* KPI Cards Treatment */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card-kpi">
          <span className="small-label block mb-1">Total Monitored Projects</span>
          <span className="font-heading text-[32px] font-bold text-[#E8ECF4]">
            {loading ? '...' : totalProjects}
          </span>
        </div>

        <div className="card-kpi border-l-4 border-l-[#F5544D]">
          <div className="flex items-center justify-between mb-1">
            <span className="small-label">Critical Urgency Attention</span>
            <Flame className="w-4 h-4 text-[#F5544D]" />
          </div>
          <span className="font-heading text-[32px] font-bold text-[#F5544D]">
            {loading ? '...' : criticalUrgencyCount}
          </span>
        </div>

        <div className="card-kpi">
          <span className="small-label block mb-1">High Risk Projects</span>
          <span className="font-heading text-[32px] font-bold text-[#FF8A3D]">
            {loading ? '...' : highCount}
          </span>
        </div>

        <div className="card-kpi">
          <span className="small-label block mb-1">Low / Healthy Projects</span>
          <span className="font-heading text-[32px] font-bold text-[#34D399]">
            {loading ? '...' : lowCount}
          </span>
        </div>
      </div>

      {/* Main Grid: Chart + Prioritized Attention List */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Risk Distribution Chart */}
        <div className="lg:col-span-4 card-chart space-y-4">
          <h2 className="section-header">Risk Distribution</h2>

          {loading ? (
            <div className="flex items-center justify-center h-64 text-[#8B95AC] text-sm">
              Loading distribution chart...
            </div>
          ) : chartData.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-[#8B95AC] text-sm space-y-2 text-center">
              <span>No project predictions stored yet</span>
              <span className="text-xs">Submit an evaluation on Project Input page to generate signals</span>
            </div>
          ) : (
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={85}
                    paddingAngle={4}
                    dataKey="value"
                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    labelLine={false}
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#131B2E', borderColor: '#232E47', borderRadius: '6px', color: '#E8ECF4' }}
                    formatter={(val) => [`${val} Projects`, 'Count']}
                  />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ color: '#8B95AC', fontSize: '11px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          <div className="p-3 bg-[#131B2E] border border-[#232E47] rounded-[6px] text-xs space-y-1 text-[#8B95AC]">
            <span className="font-semibold text-[#E8ECF4] block">Urgency Scoring Formula:</span>
            <p className="text-[11px] font-mono leading-relaxed">
              Urgency = RiskWeight × (1 + Confidence) + Escalation(1.5) + Staleness(0.5/wk)
            </p>
          </div>
        </div>

        {/* Prioritized Attention List Table */}
        <div className="lg:col-span-8 card-content space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#232E47]">
            <div>
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-[#FF8A3D]" />
                <h2 className="section-header">Prioritized Attention List</h2>
              </div>
              <p className="small-label mt-0.5">Ranked by combined urgency score for immediate PM triage</p>
            </div>

            {/* Filter Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto text-[11px]">
              <button
                onClick={() => setFilterLevel('ALL')}
                className={`px-2.5 py-1 rounded-[4px] font-medium transition-colors ${filterLevel === 'ALL' ? 'bg-[#FF8A3D] text-[#0A0E17]' : 'bg-[#131B2E] text-[#8B95AC] hover:text-[#E8ECF4]'}`}
              >
                All ({projects.length})
              </button>
              <button
                onClick={() => setFilterLevel('CRITICAL')}
                className={`px-2.5 py-1 rounded-[4px] font-medium transition-colors ${filterLevel === 'CRITICAL' ? 'bg-[#F5544D] text-[#0A0E17]' : 'bg-[#131B2E] text-[#8B95AC] hover:text-[#E8ECF4]'}`}
              >
                Critical ({criticalUrgencyCount})
              </button>
              <button
                onClick={() => setFilterLevel('HIGH_RISK')}
                className={`px-2.5 py-1 rounded-[4px] font-medium transition-colors ${filterLevel === 'HIGH_RISK' ? 'bg-[#FF8A3D] text-[#0A0E17]' : 'bg-[#131B2E] text-[#8B95AC] hover:text-[#E8ECF4]'}`}
              >
                High Risk ({highCount})
              </button>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-[#131B2E] border border-[#F5544D] rounded-[6px] text-[#F5544D] text-xs">
              Error fetching portfolio: {error}
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center h-64 text-[#8B95AC] text-sm">
              Calculating project urgency scores...
            </div>
          ) : filteredProjects.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-[#8B95AC] text-sm space-y-2 text-center">
              <span className="body-text">No matching records found</span>
              <p className="small-label max-w-sm">
                Submit an analysis on the Project Input page to automatically create and persist project risk records.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#232E47] text-[#8B95AC] font-medium text-[11px] uppercase tracking-wider">
                    <th className="py-2.5 px-3">Rank</th>
                    <th className="py-2.5 px-3">Project</th>
                    <th className="py-2.5 px-3">Urgency Level</th>
                    <th className="py-2.5 px-3">Risk & Confidence</th>
                    <th className="py-2.5 px-3">Staleness</th>
                    <th className="py-2.5 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#232E47]">
                  {filteredProjects.map((p, idx) => {
                    const rank = idx + 1;
                    const risk = p.risk_level || (p.most_recent_prediction ? p.most_recent_prediction.risk_level : 'Unanalyzed');
                    const conf = p.calibrated_confidence ? (p.calibrated_confidence * 100).toFixed(1) : (p.most_recent_prediction ? (p.most_recent_prediction.risk_probability * 100).toFixed(1) : null);
                    const urgencyLvl = p.urgency_level || (risk === 'High' ? 'CRITICAL' : risk === 'Medium' ? 'HIGH' : 'MODERATE');
                    const urgencyScore = p.urgency_score || 0.0;
                    const weeksStale = p.weeks_stale !== undefined ? p.weeks_stale : 0.0;
                    const isEscalating = p.is_escalating || risk === 'High';

                    return (
                      <tr key={p.project_id} className={`hover:bg-[#1A243B] transition-colors ${rank <= 3 ? 'bg-[#131B2E]/40' : ''}`}>
                        {/* Rank Badge */}
                        <td className="py-3 px-3">
                          <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full font-mono text-[11px] font-bold ${
                            rank === 1 ? 'bg-[#F5544D] text-[#0A0E17]' :
                            rank === 2 ? 'bg-[#FF8A3D] text-[#0A0E17]' :
                            rank === 3 ? 'bg-[#FBBF24] text-[#0A0E17]' : 'bg-[#232E47] text-[#8B95AC]'
                          }`}>
                            #{rank}
                          </span>
                        </td>

                        {/* Project Info */}
                        <td className="py-3 px-3">
                          <div className="font-mono font-semibold text-[#E8ECF4] text-xs flex items-center gap-1.5">
                            {p.project_id}
                            {isEscalating && (
                              <span title="Escalating Risk Trajectory">
                                <Flame className="w-3.5 h-3.5 text-[#F5544D] animate-pulse inline" />
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-[#8B95AC] truncate max-w-[160px]">{p.project_name || 'CompilePulse Project'}</div>
                        </td>

                        {/* Urgency Badge */}
                        <td className="py-3 px-3">
                          <div className="flex flex-col gap-1">
                            {urgencyLvl === 'CRITICAL' && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] text-[10px] font-bold uppercase bg-[#F5544D]/15 text-[#F5544D] border border-[#F5544D]/30 w-max">
                                <AlertTriangle className="w-3 h-3" /> Critical ({urgencyScore})
                              </span>
                            )}
                            {urgencyLvl === 'HIGH' && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] text-[10px] font-bold uppercase bg-[#FF8A3D]/15 text-[#FF8A3D] border border-[#FF8A3D]/30 w-max">
                                High ({urgencyScore})
                              </span>
                            )}
                            {urgencyLvl === 'MODERATE' && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] text-[10px] font-bold uppercase bg-[#FBBF24]/15 text-[#FBBF24] border border-[#FBBF24]/30 w-max">
                                Moderate ({urgencyScore})
                              </span>
                            )}
                            {urgencyLvl === 'LOW' && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] text-[10px] font-bold uppercase bg-[#34D399]/15 text-[#34D399] border border-[#34D399]/30 w-max">
                                Low ({urgencyScore})
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Risk & Confidence */}
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-2">
                            {risk === 'Low' && <span className="badge-risk-low">Low</span>}
                            {risk === 'Medium' && <span className="badge-risk-medium">Medium</span>}
                            {risk === 'High' && <span className="badge-risk-high">High</span>}
                            {risk === 'Unanalyzed' && <span className="small-label">Unanalyzed</span>}
                            {conf && <span className="text-[11px] font-mono text-[#8B95AC]">({conf}%)</span>}
                          </div>
                        </td>

                        {/* Staleness Badge */}
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-1 text-[11px] font-mono text-[#8B95AC]">
                            <Clock className="w-3 h-3 text-[#8B95AC]" />
                            {weeksStale <= 0.5 ? (
                              <span className="text-[#34D399]">Fresh</span>
                            ) : weeksStale >= 2.0 ? (
                              <span className="text-[#FBBF24] font-semibold">{weeksStale} wks stale</span>
                            ) : (
                              <span>{weeksStale} wks ago</span>
                            )}
                          </div>
                        </td>

                        {/* Action Link */}
                        <td className="py-3 px-3 text-right">
                          <NavLink
                            to="/project-input"
                            state={{ prefillProjectId: p.project_id }}
                            className="inline-flex items-center gap-1 text-[11px] font-medium text-[#FF8A3D] hover:text-[#E8ECF4] transition-colors"
                          >
                            Re-analyze <ArrowRight className="w-3 h-3" />
                          </NavLink>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
