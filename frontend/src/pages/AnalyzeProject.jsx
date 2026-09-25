import React, { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, LabelList } from 'recharts';
import { API_BASE_URL } from '../config';

const PRESETS = {
  healthy: {
    project_id: 'PROJ-HEALTHY',
    project_name: 'CompilePulse Healthy Sprint',
    week_number: 12, issue_count: 5, task_completion_rate: 90.0,
    unresolved_issue_percentage: 10.0, overdue_tasks_percentage: 5.0,
    defect_density: 2.0, critical_bug_count: 0, team_size: 8,
    schedule_progress_percentage: 85.0, stale_days_threshold_used: 14,
    issue_count_delta: -1.0, task_completion_rate_delta: 2.5,
    overdue_tasks_percentage_delta: -2.0, defect_density_delta: -0.5, team_size_delta: 0.0
  },
  warning: {
    project_id: 'PROJ-WARN',
    project_name: 'CompilePulse Moderate Warning',
    week_number: 16, issue_count: 18, task_completion_rate: 65.0,
    unresolved_issue_percentage: 35.0, overdue_tasks_percentage: 25.0,
    defect_density: 12.0, critical_bug_count: 1, team_size: 6,
    schedule_progress_percentage: 60.0, stale_days_threshold_used: 28,
    issue_count_delta: 3.0, task_completion_rate_delta: -3.0,
    overdue_tasks_percentage_delta: 5.0, defect_density_delta: 1.5, team_size_delta: -1.0
  },
  critical: {
    project_id: 'PROJ-101',
    project_name: 'CompilePulse Critical Core',
    week_number: 20, issue_count: 32, task_completion_rate: 42.9,
    unresolved_issue_percentage: 57.1, overdue_tasks_percentage: 57.1,
    defect_density: 28.6, critical_bug_count: 3, team_size: 4,
    schedule_progress_percentage: 42.9, stale_days_threshold_used: 39,
    issue_count_delta: 8.0, task_completion_rate_delta: -8.5,
    overdue_tasks_percentage_delta: 14.2, defect_density_delta: 4.2, team_size_delta: -2.0
  }
};

export default function AnalyzeProject() {
  const [formData, setFormData] = useState(PRESETS.critical);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [checkedActions, setCheckedActions] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === 'project_id' || name === 'project_name') {
      setFormData(prev => ({ ...prev, [name]: value }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value === '' ? '' : parseFloat(value) || 0
      }));
    }
  };

  const handlePreset = (presetKey) => {
    setFormData(PRESETS[presetKey]);
    setResult(null);
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setCheckedActions({});

    try {
      const response = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to connect to backend server');
    } finally {
      setLoading(false);
    }
  };

  const toggleActionCheck = (index) => {
    setCheckedActions(prev => ({ ...prev, [index]: !prev[index] }));
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
      {/* Left Column: Form Section */}
      <div className="lg:col-span-5">
        <div className="card-section m-0">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-bold text-white flex items-center gap-2 m-0">
              <span>⚙️</span> Input Project Metrics
            </h2>
            <span className="text-xs text-slate-400 font-mono">15 Features</span>
          </div>

          {/* Quick Presets */}
          <div className="preset-container">
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Quick Load Presets:
            </label>
            <div className="preset-grid">
              <button type="button" onClick={() => handlePreset('healthy')} className="btn-preset btn-preset-healthy">
                🟢 Healthy
              </button>
              <button type="button" onClick={() => handlePreset('warning')} className="btn-preset btn-preset-warning">
                🟡 Warning
              </button>
              <button type="button" onClick={() => handlePreset('critical')} className="btn-preset btn-preset-critical">
                🔴 Critical
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            {/* Project Identity */}
            <div className="mb-4 space-y-2">
              <div className="form-field">
                <label className="form-label">Project ID</label>
                <input type="text" name="project_id" value={formData.project_id || ''} onChange={handleChange} required className="form-input font-mono" placeholder="e.g. PROJ-101" />
              </div>
              <div className="form-field">
                <label className="form-label">Project Name</label>
                <input type="text" name="project_name" value={formData.project_name || ''} onChange={handleChange} required className="form-input" placeholder="e.g. Core Platform Upgrade" />
              </div>
            </div>

            {/* Section 1: Core Project Metrics */}
            <div>
              <h3 className="form-group-title title-core">
                1. Core Project Metrics
              </h3>
              <div className="form-grid">
                <div className="form-field">
                  <label className="form-label">Week Number</label>
                  <input type="number" step="any" name="week_number" value={formData.week_number} onChange={handleChange} required className="form-input" />
                </div>
                <div className="form-field">
                  <label className="form-label">Issue Count</label>
                  <input type="number" step="any" name="issue_count" value={formData.issue_count} onChange={handleChange} required className="form-input" />
                </div>
                <div className="form-field">
                  <label className="form-label">Task Comp Rate (%)</label>
                  <input type="number" step="any" name="task_completion_rate" value={formData.task_completion_rate} onChange={handleChange} required className="form-input" />
                </div>
                <div className="form-field">
                  <label className="form-label">Unresolved Issue %</label>
                  <input type="number" step="any" name="unresolved_issue_percentage" value={formData.unresolved_issue_percentage} onChange={handleChange} required className="form-input" />
                </div>
                <div className="form-field form-field-full">
                  <label className="form-label">Overdue Tasks %</label>
                  <input type="number" step="any" name="overdue_tasks_percentage" value={formData.overdue_tasks_percentage} onChange={handleChange} required className="form-input" />
                </div>
              </div>
            </div>

            {/* Section 2: Quality & Resources */}
            <div>
              <h3 className="form-group-title title-quality">
                2. Quality & Resources
              </h3>
              <div className="form-grid">
                <div className="form-field">
                  <label className="form-label">Defect Density</label>
                  <input type="number" step="any" name="defect_density" value={formData.defect_density} onChange={handleChange} required className="form-input" />
                </div>
                <div className="form-field">
                  <label className="form-label">Critical Bugs</label>
                  <input type="number" step="any" name="critical_bug_count" value={formData.critical_bug_count} onChange={handleChange} required className="form-input" />
                </div>
                <div className="form-field">
                  <label className="form-label">Team Size</label>
                  <input type="number" step="any" name="team_size" value={formData.team_size} onChange={handleChange} required className="form-input" />
                </div>
                <div className="form-field">
                  <label className="form-label">Schedule Progress %</label>
                  <input type="number" step="any" name="schedule_progress_percentage" value={formData.schedule_progress_percentage} onChange={handleChange} required className="form-input" />
                </div>
                <div className="form-field form-field-full">
                  <label className="form-label">Stale Days Threshold</label>
                  <input type="number" step="any" name="stale_days_threshold_used" value={formData.stale_days_threshold_used} onChange={handleChange} required className="form-input" />
                </div>
              </div>
            </div>

            {/* Section 3: Weekly Deltas */}
            <div>
              <h3 className="form-group-title title-deltas">
                3. Weekly Deltas
              </h3>
              <div className="form-grid">
                <div className="form-field">
                  <label className="form-label">Issue Count Δ</label>
                  <input type="number" step="any" name="issue_count_delta" value={formData.issue_count_delta} onChange={handleChange} required className="form-input" />
                </div>
                <div className="form-field">
                  <label className="form-label">Task Comp Rate Δ</label>
                  <input type="number" step="any" name="task_completion_rate_delta" value={formData.task_completion_rate_delta} onChange={handleChange} required className="form-input" />
                </div>
                <div className="form-field">
                  <label className="form-label">Overdue Tasks Δ %</label>
                  <input type="number" step="any" name="overdue_tasks_percentage_delta" value={formData.overdue_tasks_percentage_delta} onChange={handleChange} required className="form-input" />
                </div>
                <div className="form-field">
                  <label className="form-label">Defect Density Δ</label>
                  <input type="number" step="any" name="defect_density_delta" value={formData.defect_density_delta} onChange={handleChange} required className="form-input" />
                </div>
                <div className="form-field form-field-full">
                  <label className="form-label">Team Size Δ</label>
                  <input type="number" step="any" name="team_size_delta" value={formData.team_size_delta} onChange={handleChange} required className="form-input" />
                </div>
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-submit">
              {loading ? 'Analyzing Risk & Saving to DB...' : '🚀 Analyze Project Risk'}
            </button>
          </form>
        </div>
      </div>

      {/* Right Column: Prediction Results */}
      <div className="lg:col-span-7 space-y-6">
        {!loading && !result && !error && (
          <div className="card-section flex flex-col items-center justify-center min-h-[400px] text-center m-0">
            <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-3xl mb-4">🔍</div>
            <h3 className="text-xl font-bold text-slate-200 mb-2">Ready for Risk Analysis</h3>
            <p className="text-slate-400 text-sm max-w-md">
              Enter project parameters on the left or select a preset, then click <strong>"Analyze Project Risk"</strong> to compute prediction, SHAP factors, and save to SQLite.
            </p>
          </div>
        )}

        {error && (
          <div className="card-section border-rose-900/50 bg-rose-950/30 m-0">
            <h3 className="text-lg font-bold text-rose-300 mb-1">Backend Server Error</h3>
            <p className="text-rose-200/80 text-sm mb-2">{error}</p>
            <div className="text-xs text-slate-400">Ensure FastAPI backend is active on <code>http://localhost:8000</code>.</div>
          </div>
        )}

        {result && !loading && (
          <div className="space-y-6">
            
            {/* Risk Level Badge */}
            <div className="card-section flex items-center justify-between m-0">
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wider block font-semibold">Predicted Risk Level:</span>
                <div className="mt-2">
                  {result.predicted_risk_level === 'Low' && <span className="badge-pill badge-low">🟢 LOW RISK</span>}
                  {result.predicted_risk_level === 'Medium' && <span className="badge-pill badge-medium">🟡 MEDIUM RISK</span>}
                  {result.predicted_risk_level === 'High' && <span className="badge-pill badge-high">🔴 HIGH RISK</span>}
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-400 block font-semibold">Confidence:</span>
                <span className="text-2xl font-black text-white">{((result.probabilities[result.predicted_risk_level] || 0) * 100).toFixed(1)}%</span>
                {result.prediction_id && (
                  <span className="block text-[11px] font-mono text-sky-400 mt-1">Saved DB ID #{result.prediction_id}</span>
                )}
              </div>
            </div>

            {/* Class Probabilities Bar Chart */}
            <div className="card-section m-0">
              <h3 className="text-base font-bold text-slate-100 mb-3 flex items-center gap-2 m-0">
                <span>📊</span> Class Probabilities
              </h3>
              <div style={{ width: '100%', height: 180 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    layout="vertical"
                    data={[
                      { name: 'Low Risk', probability: parseFloat(((result.probabilities?.Low || 0) * 100).toFixed(1)), color: '#10B981' },
                      { name: 'Medium Risk', probability: parseFloat(((result.probabilities?.Medium || 0) * 100).toFixed(1)), color: '#F59E0B' },
                      { name: 'High Risk', probability: parseFloat(((result.probabilities?.High || 0) * 100).toFixed(1)), color: '#EF4444' }
                    ]}
                    margin={{ top: 10, right: 45, left: 15, bottom: 5 }}
                  >
                    <XAxis type="number" domain={[0, 100]} stroke="#94A3B8" fontSize={11} tickFormatter={(val) => `${val}%`} />
                    <YAxis type="category" dataKey="name" stroke="#CBD5E1" fontSize={12} width={95} tickLine={false} axisLine={false} />
                    <Tooltip
                      formatter={(val) => [`${val}%`, 'Probability']}
                      contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '0.5rem', color: '#F8FAFC' }}
                      itemStyle={{ color: '#38BDF8' }}
                    />
                    <Bar dataKey="probability" radius={[0, 6, 6, 0]} barSize={22}>
                      <LabelList dataKey="probability" position="right" formatter={(val) => `${val}%`} fill="#F8FAFC" fontSize={11} fontWeight={700} />
                      <Cell fill="#10B981" />
                      <Cell fill="#F59E0B" />
                      <Cell fill="#EF4444" />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* SHAP Explanation */}
            <div className="card-section m-0">
              <h3 className="text-base font-bold text-slate-100 mb-3 flex items-center gap-2 m-0">
                <span>💡</span> SHAP Root Cause Explanation
              </h3>
              <div className="explanation-box">
                💬 {result.explanation_sentence}
              </div>
              <div>
                <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block mb-2">
                  Top 5 SHAP Contributing Factors:
                </span>
                {result.top_5_shap_factors.map((factor, idx) => (
                  <div key={factor.feature} className="factor-item">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-slate-400">{idx + 1}.</span>
                      <span className="factor-name">{factor.feature}</span>
                      <span className="text-slate-400">({factor.value})</span>
                    </div>
                    <span className="factor-shap">+{factor.shap_impact.toFixed(4)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommended Action Plan Checklist */}
            {result.recommended_actions && result.recommended_actions.length > 0 && (
              <div className="card-section action-card m-0">
                <h3 className="action-title m-0">
                  <span>📋</span> Recommended Action Plan
                </h3>
                <div className="mt-3">
                  {result.recommended_actions.map((action, idx) => (
                    <label key={idx} onClick={() => toggleActionCheck(idx)} className={`action-item ${checkedActions[idx] ? 'action-item-checked' : ''}`}>
                      <input type="checkbox" checked={!!checkedActions[idx]} onChange={() => {}} className="action-checkbox" />
                      <span className="action-text">{action}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

          </div>
        )}
      </div>
    </div>
  );
}
