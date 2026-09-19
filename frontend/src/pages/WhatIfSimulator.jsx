import React, { useState } from 'react';
import { API_BASE_URL } from '../config';

const BASE_PRESETS = {
  critical: {
    week_number: 20, issue_count: 32, task_completion_rate: 42.9,
    unresolved_issue_percentage: 57.1, overdue_tasks_percentage: 57.1,
    defect_density: 28.6, critical_bug_count: 3, team_size: 4,
    schedule_progress_percentage: 42.9, stale_days_threshold_used: 39,
    issue_count_delta: 8.0, task_completion_rate_delta: -8.5,
    overdue_tasks_percentage_delta: 14.2, defect_density_delta: 4.2, team_size_delta: -2.0
  },
  warning: {
    week_number: 16, issue_count: 18, task_completion_rate: 65.0,
    unresolved_issue_percentage: 35.0, overdue_tasks_percentage: 25.0,
    defect_density: 12.0, critical_bug_count: 1, team_size: 6,
    schedule_progress_percentage: 60.0, stale_days_threshold_used: 28,
    issue_count_delta: 3.0, task_completion_rate_delta: -3.0,
    overdue_tasks_percentage_delta: 5.0, defect_density_delta: 1.5, team_size_delta: -1.0
  }
};

export default function WhatIfSimulator() {
  const [baseFeatures, setBaseFeatures] = useState(BASE_PRESETS.critical);
  const [changes, setChanges] = useState({
    team_size: 2.0,
    overdue_tasks_percentage: -20.0,
    critical_bug_count: -2.0
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [simResult, setSimResult] = useState(null);

  const handleBaseChange = (e) => {
    const { name, value } = e.target;
    setBaseFeatures(prev => ({
      ...prev,
      [name]: value === '' ? '' : parseFloat(value) || 0
    }));
  };

  const handleDeltaChange = (e) => {
    const { name, value } = e.target;
    setChanges(prev => ({
      ...prev,
      [name]: value === '' ? 0 : parseFloat(value) || 0
    }));
  };

  const handleRunSimulation = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSimResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          features: baseFeatures,
          changes: changes
        })
      });

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`);
      }

      const data = await response.json();
      setSimResult(data);
    } catch (err) {
      setError(err.message || 'Simulation request failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-transition grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Left Column: Form Controls */}
      <div className="lg:col-span-6 space-y-6">
        <div className="card-content space-y-6">
          <div>
            <h1 className="page-title">Counterfactual What-If Simulator</h1>
            <p className="small-label mt-1">
              Test hypothetical scenario modifications on project parameters to observe risk transition signals
            </p>
          </div>

          <form onSubmit={handleRunSimulation} className="space-y-6">
            {/* Feature Delta Adjustments */}
            <div className="space-y-3">
              <h2 className="section-header">Feature Delta Adjustments (+ or -)</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="small-label block mb-1">Team Size Delta</label>
                  <input
                    type="number"
                    step="any"
                    name="team_size"
                    value={changes.team_size ?? 0}
                    onChange={handleDeltaChange}
                    className="input-signal font-mono text-xs"
                    placeholder="+2.0"
                  />
                </div>

                <div>
                  <label className="small-label block mb-1">Overdue Tasks Delta %</label>
                  <input
                    type="number"
                    step="any"
                    name="overdue_tasks_percentage"
                    value={changes.overdue_tasks_percentage ?? 0}
                    onChange={handleDeltaChange}
                    className="input-signal font-mono text-xs"
                    placeholder="-20.0"
                  />
                </div>

                <div>
                  <label className="small-label block mb-1">Critical Bugs Delta</label>
                  <input
                    type="number"
                    step="any"
                    name="critical_bug_count"
                    value={changes.critical_bug_count ?? 0}
                    onChange={handleDeltaChange}
                    className="input-signal font-mono text-xs"
                    placeholder="-2.0"
                  />
                </div>
              </div>
            </div>

            {/* Baseline Metric Inputs */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="section-header">Baseline Metric Parameters</h2>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setBaseFeatures(BASE_PRESETS.critical)}
                    className="btn-preset-critical"
                  >
                    Critical Base
                  </button>
                  <button
                    type="button"
                    onClick={() => setBaseFeatures(BASE_PRESETS.warning)}
                    className="btn-preset-warning"
                  >
                    Warning Base
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                <div>
                  <label className="small-label block mb-1">Overdue %</label>
                  <input type="number" step="any" name="overdue_tasks_percentage" value={baseFeatures.overdue_tasks_percentage} onChange={handleBaseChange} className="input-signal text-xs" />
                </div>
                <div>
                  <label className="small-label block mb-1">Team Size</label>
                  <input type="number" step="any" name="team_size" value={baseFeatures.team_size} onChange={handleBaseChange} className="input-signal text-xs" />
                </div>
                <div>
                  <label className="small-label block mb-1">Critical Bugs</label>
                  <input type="number" step="any" name="critical_bug_count" value={baseFeatures.critical_bug_count} onChange={handleBaseChange} className="input-signal text-xs" />
                </div>
                <div>
                  <label className="small-label block mb-1">Task Comp %</label>
                  <input type="number" step="any" name="task_completion_rate" value={baseFeatures.task_completion_rate} onChange={handleBaseChange} className="input-signal text-xs" />
                </div>
                <div>
                  <label className="small-label block mb-1">Defect Density</label>
                  <input type="number" step="any" name="defect_density" value={baseFeatures.defect_density} onChange={handleBaseChange} className="input-signal text-xs" />
                </div>
                <div>
                  <label className="small-label block mb-1">Unresolved %</label>
                  <input type="number" step="any" name="unresolved_issue_percentage" value={baseFeatures.unresolved_issue_percentage} onChange={handleBaseChange} className="input-signal text-xs" />
                </div>
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full py-3">
              {loading ? 'Running Simulation...' : 'Run What-If Counterfactual Simulation'}
            </button>
          </form>
        </div>
      </div>

      {/* Right Column: Simulation Outcomes Comparison */}
      <div className="lg:col-span-6 space-y-6">
        {!loading && !simResult && !error && (
          <div className="card-content flex flex-col items-center justify-center min-h-[380px] text-center space-y-2">
            <h2 className="section-header">Simulation Ready</h2>
            <p className="body-text text-[#8B95AC] max-w-md">
              Specify feature modifications on the left and click <strong>"Run What-If Counterfactual Simulation"</strong> to evaluate risk outcome signals.
            </p>
          </div>
        )}

        {error && (
          <div className="card-content border-[#F5544D] text-[#F5544D] text-xs">
            Simulation Error: {error}
          </div>
        )}

        {simResult && !loading && (
          <div className="space-y-6">
            {/* Comparison Cards (card-kpi treatment) */}
            <div className="grid grid-cols-2 gap-4">
              {/* Baseline Risk Card */}
              <div className="card-kpi">
                <span className="small-label block mb-1">Baseline Classification</span>
                <div className="mt-1">
                  {simResult.baseline.predicted_risk_level === 'Low' && <span className="badge-risk-low">Low Risk</span>}
                  {simResult.baseline.predicted_risk_level === 'Medium' && <span className="badge-risk-medium">Medium Risk</span>}
                  {simResult.baseline.predicted_risk_level === 'High' && <span className="badge-risk-high">High Risk</span>}
                </div>
                <span className="small-label block mt-3 font-mono">
                  Confidence: {(simResult.baseline.confidence * 100).toFixed(1)}%
                </span>
              </div>

              {/* Simulated Outcome Card */}
              <div className="card-kpi border-l-2 border-l-[#FF8A3D]">
                <span className="small-label text-[#FF8A3D] block mb-1 font-semibold">Simulated Outcome</span>
                <div className="mt-1">
                  {simResult.simulated.predicted_risk_level === 'Low' && <span className="badge-risk-low">Low Risk</span>}
                  {simResult.simulated.predicted_risk_level === 'Medium' && <span className="badge-risk-medium">Medium Risk</span>}
                  {simResult.simulated.predicted_risk_level === 'High' && <span className="badge-risk-high">High Risk</span>}
                </div>
                <span className="small-label text-[#FF8A3D] block mt-3 font-mono">
                  Confidence: {(simResult.simulated.confidence * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Summary Sentence Box */}
            <div className="card-content space-y-2">
              <h2 className="section-header">Simulated Impact Summary</h2>
              <p className="body-text bg-[#0B1220] p-4 rounded-[6px] border border-[#232E47]">
                {simResult.summary_sentence}
              </p>
            </div>

            {/* Warnings / Bounds Clamping */}
            {simResult.warnings && simResult.warnings.length > 0 && (
              <div className="card-content space-y-2 border-l-2 border-l-[#FBBF24]">
                <span className="emphasis-label text-[#FBBF24] block">Feature Bounds Clamping Applied</span>
                <ul className="list-disc list-inside small-label space-y-1">
                  {simResult.warnings.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
