import React, { useState } from 'react';
import { API_BASE_URL } from '../config';
import { FlaskConical, ArrowRight, CheckCircle2, AlertTriangle, Flame, RefreshCw, TrendingDown, TrendingUp, Sparkles } from 'lucide-react';

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
    <div className="page-transition space-y-6">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-[#0F172A] via-[#1E293B] to-[#0F172A] p-6 rounded-2xl border border-[#1E293B] shadow-2xl text-white space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5 font-heading">
          <FlaskConical className="w-6 h-6 text-violet-400" />
          What-If Impact Simulator
        </h1>
        <p className="text-xs text-slate-300 font-medium">
          Test hypothetical scenario modifications on project parameters to observe real-time risk transitions
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Form Controls */}
        <div className="lg:col-span-6 space-y-5">
          <form onSubmit={handleRunSimulation} className="glass-card p-5 space-y-5 border-l-4 border-l-violet-500">
            
            {/* Base Scenario Preset Selection */}
            <div className="space-y-2 border-b border-[#1E293B] pb-3">
              <span className="text-xs font-semibold text-violet-400 uppercase tracking-wider block">
                Baseline Project Preset
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setBaseFeatures(BASE_PRESETS.critical)}
                  className="btn-preset-critical flex items-center gap-1.5"
                >
                  <Flame className="w-3.5 h-3.5 text-rose-400" />
                  Critical Baseline
                </button>
                <button
                  type="button"
                  onClick={() => setBaseFeatures(BASE_PRESETS.warning)}
                  className="btn-preset-warning flex items-center gap-1.5"
                >
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  Moderate Baseline
                </button>
              </div>
            </div>

            {/* Feature Adjustments */}
            <div className="space-y-3">
              <h2 className="text-sm font-semibold text-white font-heading">
                Hypothetical Scenario Adjustments (+ or -)
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div>
                  <label className="block font-medium text-slate-300 mb-1">Team Size (+ FTE)</label>
                  <input
                    type="number"
                    step="any"
                    name="team_size"
                    value={changes.team_size}
                    onChange={handleDeltaChange}
                    className="input-signal font-mono font-bold text-violet-400"
                  />
                </div>
                <div>
                  <label className="block font-medium text-slate-300 mb-1">Overdue Tasks (% delta)</label>
                  <input
                    type="number"
                    step="any"
                    name="overdue_tasks_percentage"
                    value={changes.overdue_tasks_percentage}
                    onChange={handleDeltaChange}
                    className="input-signal font-mono font-bold text-violet-400"
                  />
                </div>
                <div>
                  <label className="block font-medium text-slate-300 mb-1">Critical Bug Count</label>
                  <input
                    type="number"
                    step="any"
                    name="critical_bug_count"
                    value={changes.critical_bug_count}
                    onChange={handleDeltaChange}
                    className="input-signal font-mono font-bold text-violet-400"
                  />
                </div>
              </div>
            </div>

            {/* Current Baseline Settings */}
            <div className="space-y-3 pt-2 border-t border-[#1E293B]">
              <h2 className="text-sm font-semibold text-white font-heading">
                Baseline Parameters
              </h2>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block font-medium text-slate-300 mb-1">Current Overdue %</label>
                  <input
                    type="number"
                    step="any"
                    name="overdue_tasks_percentage"
                    value={baseFeatures.overdue_tasks_percentage}
                    onChange={handleBaseChange}
                    className="input-signal"
                  />
                </div>
                <div>
                  <label className="block font-medium text-slate-300 mb-1">Current Critical Bugs</label>
                  <input
                    type="number"
                    step="any"
                    name="critical_bug_count"
                    value={baseFeatures.critical_bug_count}
                    onChange={handleBaseChange}
                    className="input-signal"
                  />
                </div>
              </div>
            </div>

            {error && (
              <div className="p-3 bg-rose-500/15 border border-rose-500/30 rounded-xl text-rose-300 text-xs">
                Error: {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3.5 text-xs font-semibold"
            >
              <FlaskConical className="w-4 h-4" />
              <span>{loading ? 'Simulating Impact...' : 'Run Counterfactual Simulation'}</span>
            </button>
          </form>
        </div>

        {/* Right Column: Simulation Output Results */}
        <div className="lg:col-span-6 space-y-5">
          {simResult ? (
            <div className="glass-card p-5 space-y-4 animate-fadeIn border-l-4 border-l-emerald-500">
              <div className="border-b border-[#1E293B] pb-3">
                <h2 className="text-base font-bold text-white font-heading">
                  Simulation Impact Comparison
                </h2>
                <p className="text-xs text-slate-300">
                  Comparison between original baseline vs simulated scenario
                </p>
              </div>

              {/* Before vs After Risk Pills */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[#070B14] p-4 rounded-xl border border-[#1E293B] space-y-1.5 text-center">
                  <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider block">
                    Original Risk
                  </span>
                  <span className="text-lg font-bold text-rose-400 font-mono block">
                    {simResult.original_risk}
                  </span>
                </div>

                <div className="bg-[#070B14] p-4 rounded-xl border border-emerald-500/40 space-y-1.5 text-center shadow-[0_0_15px_rgba(16,185,129,0.15)]">
                  <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider block">
                    Simulated Risk
                  </span>
                  <span className="text-lg font-bold text-emerald-400 font-mono block">
                    {simResult.simulated_risk}
                  </span>
                </div>
              </div>

              {/* Transition Summary Sentence */}
              {simResult.risk_level_changed ? (
                <div className="p-3 bg-emerald-500/15 border border-emerald-500/40 rounded-xl text-xs text-emerald-300 font-semibold flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>Successful Risk Level Transition: {simResult.original_risk} → {simResult.simulated_risk}</span>
                </div>
              ) : (
                <div className="p-3 bg-amber-500/15 border border-amber-500/40 rounded-xl text-xs text-amber-300 font-medium flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                  <span>Risk Level remained unchanged ({simResult.original_risk}). Additional interventions required.</span>
                </div>
              )}

              {/* Probability Shift Table */}
              <div className="space-y-2 pt-2 border-t border-[#1E293B]">
                <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider block">
                  Probability Shift Analysis
                </span>
                <div className="space-y-2 text-xs">
                  {Object.keys(simResult.simulated_probabilities || {}).map((riskKey) => {
                    const origProb = (simResult.original_probabilities[riskKey] * 100).toFixed(1);
                    const simProb = (simResult.simulated_probabilities[riskKey] * 100).toFixed(1);
                    const diff = (simProb - origProb).toFixed(1);

                    return (
                      <div key={riskKey} className="flex items-center justify-between p-2.5 bg-[#070B14] rounded-xl border border-[#1E293B] font-mono">
                        <span className="font-semibold text-white">{riskKey} Risk</span>
                        <div className="flex items-center gap-3">
                          <span className="text-slate-400">{origProb}% → {simProb}%</span>
                          <span className={`font-bold ${parseFloat(diff) <= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {parseFloat(diff) > 0 ? `+${diff}%` : `${diff}%`}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-card p-8 text-center space-y-3 border-l-4 border-l-violet-500">
              <FlaskConical className="w-10 h-10 text-violet-400 mx-auto" />
              <h2 className="text-base font-bold text-white font-heading">Run a Counterfactual Simulation</h2>
              <p className="text-xs text-slate-300 max-w-sm mx-auto leading-relaxed">
                Adjust feature deltas on the left panel (e.g. increase team size or decrease overdue task %) to observe how machine learning risk probabilities shift.
              </p>
            </div>
          )}
        </div>

      </div>

    </div>
  );
}

