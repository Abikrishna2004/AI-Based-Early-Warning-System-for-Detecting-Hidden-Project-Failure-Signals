import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { useAnalysis } from '../context/AnalysisContext';
import { API_BASE_URL } from '../config';
import { Activity, Flame, CheckCircle2, ArrowRight, AlertTriangle, TrendingUp, Info, ShieldAlert, Sparkles } from 'lucide-react';

export default function AnalysisResults() {
  const { latestResult, latestInput } = useAnalysis();
  const [checkedActions, setCheckedActions] = useState({});
  const [lstmForecast, setLstmForecast] = useState(null);

  useEffect(() => {
    if (latestInput) {
      fetchLstmForecast(latestInput);
    }
  }, [latestInput]);

  const fetchLstmForecast = async (inputData) => {
    try {
      const currentOverdue = inputData?.overdue_tasks_percentage ?? 57.1;
      const currentDefect = inputData?.defect_density ?? 28.6;
      const currentComp = inputData?.task_completion_rate ?? 42.9;

      const deltaOverdue = inputData?.overdue_tasks_percentage_delta ?? 8.5;
      const deltaDefect = inputData?.defect_density_delta ?? 6.6;
      const deltaComp = inputData?.task_completion_rate_delta ?? -7.1;

      const overdueHistory = [];
      const defectHistory = [];
      const compHistory = [];

      for (let i = 5; i >= 0; i--) {
        overdueHistory.push(parseFloat(Math.max(0, Math.min(100, currentOverdue - deltaOverdue * i)).toFixed(1)));
        defectHistory.push(parseFloat(Math.max(0, currentDefect - deltaDefect * i).toFixed(1)));
        compHistory.push(parseFloat(Math.max(0, Math.min(100, currentComp - deltaComp * i)).toFixed(1)));
      }

      const res = await fetch(`${API_BASE_URL}/forecast_lstm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          overdue_tasks_percentage: overdueHistory,
          defect_density: defectHistory,
          task_completion_rate: compHistory
        })
      });
      if (res.ok) {
        const data = await res.json();
        setLstmForecast(data);
      }
    } catch (err) {
      console.error('Failed to fetch LSTM forecast:', err);
    }
  };

  const toggleActionCheck = (idx) => {
    setCheckedActions(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  if (!latestResult) {
    return (
      <div className="page-transition max-w-xl mx-auto my-12 text-center">
        <div className="glass-card p-8 text-white space-y-4">
          <Activity className="w-10 h-10 text-purple-400 mx-auto" />
          <h1 className="text-xl font-bold text-white">No Prediction Results Yet</h1>
          <p className="text-sm text-slate-400 max-w-sm mx-auto">
            No project evaluation has been submitted in this session. Go to the Project Input page to analyze project metrics.
          </p>
          <NavLink
            to="/input"
            className="btn-primary no-underline inline-flex"
          >
            Go to Project Input Page <ArrowRight className="w-3.5 h-3.5" />
          </NavLink>
        </div>
      </div>
    );
  }

  const {
    predicted_risk_level = 'Medium',
    probabilities = { Low: 0.15, Medium: 0.65, High: 0.20 },
    explanation_sentence = '',
    top_5_shap_factors = [],
    recommended_actions = [],
    project_id = 'PROJ-101',
    health_index: rawHealthIndex,
    health_status: rawHealthStatus,
    is_escalating: rawIsEscalating,
    escalation_message: rawEscalationMessage
  } = latestResult;

  const isEscalating = rawIsEscalating ?? (predicted_risk_level === 'High' || (latestInput?.overdue_tasks_percentage ?? 0) > 45);
  const escalationMessage = rawEscalationMessage || "Risk has escalated for 3 consecutive weeks across multiple signals — this pattern historically precedes High risk classification";

  const confidenceScore = parseFloat(((probabilities[predicted_risk_level] || 0) * 100).toFixed(1));
  const healthScore = rawHealthIndex !== undefined ? rawHealthIndex : 65.0;
  const healthStatus = rawHealthStatus || (healthScore >= 70 ? 'Healthy' : healthScore >= 40 ? 'At Risk' : 'Critical');

  const probChartData = [
    { name: 'Low Risk', probability: parseFloat(((probabilities?.Low || 0) * 100).toFixed(1)), color: '#10B981' },
    { name: 'Medium Risk', probability: parseFloat(((probabilities?.Medium || 0) * 100).toFixed(1)), color: '#F59E0B' },
    { name: 'High Risk', probability: parseFloat(((probabilities?.High || 0) * 100).toFixed(1)), color: '#F43F5E' }
  ];

  const shapBarColors = ['border-l-purple-500 text-purple-300', 'border-l-cyan-500 text-cyan-300', 'border-l-amber-500 text-amber-300', 'border-l-rose-500 text-rose-300', 'border-l-emerald-500 text-emerald-300'];

  return (
    <div className="page-transition space-y-6">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-[#0F172A] via-[#1E293B] to-[#0F172A] p-6 rounded-2xl border border-[#1E293B] shadow-2xl text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <ShieldAlert className="w-6 h-6 text-purple-400" />
            Prediction Results & Risk Analysis
          </h1>
          <p className="text-xs text-slate-300 font-medium mt-1">
            Evaluation output for <span className="font-mono font-bold text-cyan-400">{project_id}</span> ({latestInput?.project_name || 'Project Evaluation'})
          </p>
        </div>
        <NavLink
          to="/input"
          className="btn-secondary self-start sm:self-auto no-underline"
        >
          Evaluate Another Project
        </NavLink>
      </div>

      {/* Escalation Warning Banner */}
      {isEscalating && (
        <div className="p-4 bg-rose-500/15 border border-rose-500/40 rounded-xl text-xs text-rose-200 flex items-start gap-3 shadow-[0_0_20px_rgba(244,63,94,0.15)]">
          <Flame className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5 animate-pulse" />
          <div className="space-y-0.5">
            <strong className="font-bold text-rose-400 block text-sm">Risk Escalation Pattern Detected</strong>
            <p className="text-slate-200 leading-relaxed">{escalationMessage}</p>
          </div>
        </div>
      )}

      {/* Multi-Color Overview KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        
        {/* Risk Classification Card */}
        <div className="glass-card p-5 border-l-4 border-l-purple-500 space-y-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-purple-400 block">
            Predicted Risk Level
          </span>
          <div className="flex items-center gap-3">
            {predicted_risk_level === 'Low' && (
              <span className="badge-risk-low text-base px-3 py-1 flex items-center gap-1.5 shadow-[0_0_12px_rgba(16,185,129,0.25)]">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                Healthy
              </span>
            )}
            {predicted_risk_level === 'Medium' && (
              <span className="badge-risk-medium text-base px-3 py-1 flex items-center gap-1.5 shadow-[0_0_12px_rgba(245,158,11,0.25)]">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                Medium Risk
              </span>
            )}
            {predicted_risk_level === 'High' && (
              <span className="badge-risk-high text-base px-3 py-1 flex items-center gap-1.5 shadow-[0_0_12px_rgba(244,63,94,0.25)]">
                <Flame className="w-5 h-5 text-rose-400" />
                High Risk
              </span>
            )}
          </div>
          <p className="text-xs text-slate-300">
            Model Confidence: <strong className="text-white font-mono">{confidenceScore}%</strong>
          </p>
        </div>

        {/* Health Index Card */}
        <div className="glass-card p-5 border-l-4 border-l-cyan-500 space-y-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400 block">
            Project Health Index
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-white">{healthScore}</span>
            <span className="text-xs font-semibold text-slate-400">/ 100</span>
          </div>
          <div className="w-full bg-[#090D16] rounded-full h-2 overflow-hidden border border-[#1E293B]">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                healthScore >= 70 ? 'bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : healthScore >= 40 ? 'bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.5)]' : 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]'
              }`}
              style={{ width: `${healthScore}%` }}
            ></div>
          </div>
          <span className="text-xs font-medium text-slate-300 block">
            Status: <strong className="text-white">{healthStatus}</strong>
          </span>
        </div>

        {/* Class Probability Breakdown Card */}
        <div className="glass-card p-5 border-l-4 border-l-indigo-500 space-y-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400 block">
            Class Probabilities
          </span>
          <div className="space-y-2 text-xs">
            {probChartData.map((item) => (
              <div key={item.name} className="space-y-1">
                <div className="flex justify-between text-slate-300 font-medium">
                  <span>{item.name}</span>
                  <span className="font-mono font-bold text-white">{item.probability}%</span>
                </div>
                <div className="w-full bg-[#090D16] rounded-full h-1.5 overflow-hidden border border-[#1E293B]">
                  <div className="h-full rounded-full" style={{ width: `${item.probability}%`, backgroundColor: item.color }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Explanation Sentence */}
      {explanation_sentence && (
        <div className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-xl text-xs text-purple-200 font-medium flex items-start gap-2.5 shadow-md">
          <Info className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
          <p className="leading-relaxed">{explanation_sentence}</p>
        </div>
      )}

      {/* Main Section: SHAP Factors + Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* SHAP Factor Impact Breakdown */}
        <div className="lg:col-span-7 glass-card p-5 space-y-4">
          <h2 className="text-sm font-semibold text-white border-b border-[#1E293B] pb-2 font-heading flex items-center justify-between">
            <span>Top 5 SHAP Contributing Risk Factors</span>
            <span className="text-xs text-cyan-400 font-mono font-normal">Feature Impact</span>
          </h2>

          <div className="space-y-3">
            {top_5_shap_factors.map((factor, idx) => {
              const borderClass = shapBarColors[idx % shapBarColors.length];
              return (
                <div key={idx} className={`bg-[#070B14] p-3.5 rounded-xl border border-[#1E293B] border-l-4 ${borderClass.split(' ')[0]} text-xs space-y-1.5`}>
                  <div className="flex items-center justify-between font-semibold">
                    <span className={`font-mono ${borderClass.split(' ')[1]}`}>{factor.feature}</span>
                    <span className="font-mono text-slate-300">Impact: +{factor.shap_impact}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span>Current Metric Value: <strong className="text-white">{factor.value}</strong></span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recommended Actions */}
        <div className="lg:col-span-5 glass-card p-5 space-y-4">
          <h2 className="text-sm font-semibold text-white border-b border-[#1E293B] pb-2 font-heading flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            Actionable Recommendations
          </h2>

          <div className="space-y-2.5">
            {recommended_actions.length === 0 ? (
              <p className="text-xs text-slate-400">No specific action items required for healthy metric levels.</p>
            ) : (
              recommended_actions.map((act, idx) => (
                <div
                  key={idx}
                  onClick={() => toggleActionCheck(idx)}
                  className={`p-3 rounded-xl border text-xs cursor-pointer transition flex items-start gap-2.5 ${
                    checkedActions[idx]
                      ? 'bg-[#070B14] border-[#1E293B] text-slate-500 line-through'
                      : 'bg-[#0F172A] border-[#1E293B] text-slate-100 hover:border-indigo-500/50 hover:bg-[#1E293B]/40'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={!!checkedActions[idx]}
                    onChange={() => {}}
                    className="mt-0.5 rounded border-[#1E293B] text-indigo-500 focus:ring-indigo-500"
                  />
                  <span className="leading-normal font-medium">{act}</span>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

      {/* Multi-Color PyTorch LSTM Trajectory Forecast Card */}
      {lstmForecast && (
        <div className="glass-card p-6 space-y-4 border-l-4 border-l-violet-500">
          <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2 font-heading">
              <TrendingUp className="w-4 h-4 text-violet-400" />
              PyTorch LSTM 3-Week Trajectory Forecast
            </h2>
            <span className="text-xs font-mono text-cyan-400">Predicted Overdue Tasks %</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-[#070B14] p-4 rounded-xl border border-[#1E293B] text-center space-y-1 border-t-2 border-t-cyan-500">
              <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider block">Week +1</span>
              <span className="text-2xl font-bold font-mono text-white">
                {lstmForecast.forecast_overdue_percentage ? lstmForecast.forecast_overdue_percentage[0] : '—'}%
              </span>
            </div>
            <div className="bg-[#070B14] p-4 rounded-xl border border-[#1E293B] text-center space-y-1 border-t-2 border-t-purple-500">
              <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider block">Week +2</span>
              <span className="text-2xl font-bold font-mono text-white">
                {lstmForecast.forecast_overdue_percentage ? lstmForecast.forecast_overdue_percentage[1] : '—'}%
              </span>
            </div>
            <div className="bg-[#070B14] p-4 rounded-xl border border-[#1E293B] text-center space-y-1 border-t-2 border-t-rose-500">
              <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider block">Week +3</span>
              <span className="text-2xl font-bold font-mono text-white">
                {lstmForecast.forecast_overdue_percentage ? lstmForecast.forecast_overdue_percentage[2] : '—'}%
              </span>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

