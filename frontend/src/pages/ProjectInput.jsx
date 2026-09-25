import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAnalysis } from '../context/AnalysisContext';
import { API_BASE_URL } from '../config';

const PRESETS = {
  healthy: {
    project_id: 'PROJ-2609001',
    project_name: 'CompilePulse Healthy Sprint',
    week_number: 12, issue_count: 5, task_completion_rate: 90.0,
    unresolved_issue_percentage: 10.0, overdue_tasks_percentage: 5.0,
    defect_density: 2.0, critical_bug_count: 0, team_size: 8,
    schedule_progress_percentage: 85.0, stale_days_threshold_used: 14,
    issue_count_delta: -1.0, task_completion_rate_delta: 2.5,
    overdue_tasks_percentage_delta: -2.0, defect_density_delta: -0.5, team_size_delta: 0.0
  },
  warning: {
    project_id: 'PROJ-2609002',
    project_name: 'CompilePulse Moderate Warning',
    week_number: 16, issue_count: 18, task_completion_rate: 65.0,
    unresolved_issue_percentage: 35.0, overdue_tasks_percentage: 25.0,
    defect_density: 12.0, critical_bug_count: 1, team_size: 6,
    schedule_progress_percentage: 60.0, stale_days_threshold_used: 28,
    issue_count_delta: 3.0, task_completion_rate_delta: -3.0,
    overdue_tasks_percentage_delta: 5.0, defect_density_delta: 1.5, team_size_delta: -1.0
  },
  critical: {
    project_id: 'PROJ-2609003',
    project_name: 'CompilePulse Critical Core',
    week_number: 20, issue_count: 32, task_completion_rate: 42.9,
    unresolved_issue_percentage: 57.1, overdue_tasks_percentage: 57.1,
    defect_density: 28.6, critical_bug_count: 3, team_size: 4,
    schedule_progress_percentage: 42.9, stale_days_threshold_used: 39,
    issue_count_delta: 8.0, task_completion_rate_delta: -8.5,
    overdue_tasks_percentage_delta: 14.2, defect_density_delta: 4.2, team_size_delta: -2.0
  }
};

export default function ProjectInput() {
  const [formData, setFormData] = useState(PRESETS.critical);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { setPredictionData } = useAnalysis();
  const navigate = useNavigate();

  React.useEffect(() => {
    fetchNextProjectId();
  }, []);

  const fetchNextProjectId = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/generate_project_id`);
      if (res.ok) {
        const data = await res.json();
        if (data.project_id) {
          setFormData(prev => ({ ...prev, project_id: data.project_id }));
        }
      }
    } catch (err) {
      console.warn('Using default formatted project_id fallback:', err);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === 'project_id') {
      return; // Read-only property
    } else if (name === 'project_name') {
      setFormData(prev => ({ ...prev, [name]: value }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value === '' ? '' : parseFloat(value) || 0
      }));
    }
  };

  const handlePreset = (presetKey) => {
    const currentId = formData.project_id;
    setFormData({
      ...PRESETS[presetKey],
      project_id: currentId || PRESETS[presetKey].project_id
    });
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

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
      
      // Store in shared React context
      setPredictionData(data, formData);

      // Automatically navigate to Analysis Results page
      navigate('/results');
    } catch (err) {
      setError(err.message || 'Failed to connect to backend server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-transition max-w-3xl mx-auto space-y-6">
      <div className="card-content space-y-6">
        <div>
          <h1 className="page-title">Project Risk Evaluation Input</h1>
        </div>

        {/* Quick Presets */}
        <div className="p-4 bg-[#0B1220] border border-[#232E47] rounded-[6px] space-y-2">
          <span className="emphasis-label">Load Baseline Preset:</span>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => handlePreset('healthy')} className="btn-preset-healthy">
              Healthy Scenario
            </button>
            <button type="button" onClick={() => handlePreset('warning')} className="btn-preset-warning">
              Moderate Warning Scenario
            </button>
            <button type="button" onClick={() => handlePreset('critical')} className="btn-preset-critical">
              Critical Risk Scenario
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-[#131B2E] border border-[#F5544D] rounded-[6px] text-[#F5544D] text-xs">
            Error: {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Project Identity */}
          <div className="p-4 bg-[#0B1220] border border-[#232E47] rounded-[6px] grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="emphasis-label block mb-1">Project ID</label>
              <input
                type="text"
                name="project_id"
                value={formData.project_id || ''}
                readOnly
                className="input-signal font-mono font-bold bg-[#131B2E]/70 text-[#38BDF8] border-[#38BDF8]/40 cursor-not-allowed"
                title="Project ID is automatically generated in PROJ-YYMMXXX format and cannot be manually modified."
              />
            </div>
            <div>
              <label className="emphasis-label block mb-1">
                Project Name <span className="text-[11px] font-normal text-[#8B95AC]">(Entered by user)</span>
              </label>
              <input
                type="text"
                name="project_name"
                value={formData.project_name || ''}
                onChange={handleChange}
                required
                className="input-signal font-medium"
                placeholder="e.g. Core Platform Upgrade"
              />
            </div>
          </div>

          {/* Section 1: Core Velocity & Progress Metrics */}
          <div className="space-y-3">
            <h2 className="section-header">Core Velocity & Progress Metrics</h2>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="small-label block mb-1">Week Number</label>
                <input type="number" step="any" name="week_number" value={formData.week_number} onChange={handleChange} required className="input-signal" placeholder="e.g. 20 (Current sprint/week)" />
              </div>
              <div>
                <label className="small-label block mb-1">Issue Count</label>
                <input type="number" step="any" name="issue_count" value={formData.issue_count} onChange={handleChange} required className="input-signal" placeholder="e.g. 32 (Total logged issues)" />
              </div>
              <div>
                <label className="small-label block mb-1">Task Completion Rate (%)</label>
                <input type="number" step="any" name="task_completion_rate" value={formData.task_completion_rate} onChange={handleChange} required className="input-signal" placeholder="e.g. 42.9 (% completed)" />
              </div>
              <div>
                <label className="small-label block mb-1">Unresolved Issue (%)</label>
                <input type="number" step="any" name="unresolved_issue_percentage" value={formData.unresolved_issue_percentage} onChange={handleChange} required className="input-signal" placeholder="e.g. 57.1 (% unresolved)" />
              </div>
              <div className="col-span-2">
                <label className="small-label block mb-1">Overdue Tasks (%)</label>
                <input type="number" step="any" name="overdue_tasks_percentage" value={formData.overdue_tasks_percentage} onChange={handleChange} required className="input-signal" placeholder="e.g. 57.1 (% overdue tasks)" />
              </div>
            </div>
          </div>

          {/* Section 2: Quality & Resources */}
          <div className="space-y-3">
            <h2 className="section-header">Quality, Bugs & Resource Capacity</h2>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="small-label block mb-1">Defect Density</label>
                <input type="number" step="any" name="defect_density" value={formData.defect_density} onChange={handleChange} required className="input-signal" placeholder="e.g. 28.6 (Bugs per KLOC)" />
              </div>
              <div>
                <label className="small-label block mb-1">Critical Bug Count</label>
                <input type="number" step="any" name="critical_bug_count" value={formData.critical_bug_count} onChange={handleChange} required className="input-signal" placeholder="e.g. 3 (High-severity bugs)" />
              </div>
              <div>
                <label className="small-label block mb-1">Team Size (FTE)</label>
                <input type="number" step="any" name="team_size" value={formData.team_size} onChange={handleChange} required className="input-signal" placeholder="e.g. 4 (Full-time engineers)" />
              </div>
              <div>
                <label className="small-label block mb-1">Schedule Progress (%)</label>
                <input type="number" step="any" name="schedule_progress_percentage" value={formData.schedule_progress_percentage} onChange={handleChange} required className="input-signal" placeholder="e.g. 42.9 (% schedule completed)" />
              </div>
              <div className="col-span-2">
                <label className="small-label block mb-1">Stale Days Threshold</label>
                <input type="number" step="any" name="stale_days_threshold_used" value={formData.stale_days_threshold_used} onChange={handleChange} required className="input-signal" placeholder="e.g. 39 (Days without activity)" />
              </div>
            </div>
          </div>

          {/* Section 3: Weekly Deltas */}
          <div className="space-y-3">
            <h2 className="section-header">Weekly Trend Deltas</h2>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="small-label block mb-1">Issue Count Delta</label>
                <input type="number" step="any" name="issue_count_delta" value={formData.issue_count_delta} onChange={handleChange} required className="input-signal" placeholder="e.g. +8.0 (Weekly count change)" />
              </div>
              <div>
                <label className="small-label block mb-1">Task Completion Rate Delta</label>
                <input type="number" step="any" name="task_completion_rate_delta" value={formData.task_completion_rate_delta} onChange={handleChange} required className="input-signal" placeholder="e.g. -8.5 (Weekly % change)" />
              </div>
              <div>
                <label className="small-label block mb-1">Overdue Tasks Delta (%)</label>
                <input type="number" step="any" name="overdue_tasks_percentage_delta" value={formData.overdue_tasks_percentage_delta} onChange={handleChange} required className="input-signal" placeholder="e.g. +14.2 (Weekly % change)" />
              </div>
              <div>
                <label className="small-label block mb-1">Defect Density Delta</label>
                <input type="number" step="any" name="defect_density_delta" value={formData.defect_density_delta} onChange={handleChange} required className="input-signal" placeholder="e.g. +4.2 (Weekly defect change)" />
              </div>
              <div className="col-span-2">
                <label className="small-label block mb-1">Team Size Delta</label>
                <input type="number" step="any" name="team_size_delta" value={formData.team_size_delta} onChange={handleChange} required className="input-signal" placeholder="e.g. -2.0 (Weekly team change)" />
              </div>
            </div>
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full py-3">
            {loading ? 'Processing Risk Evaluation...' : 'Analyze Project Risk & View Results'}
          </button>
        </form>
      </div>
    </div>
  );
}
