import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAnalysis } from '../context/AnalysisContext';
import {
  ResponsiveContainer,
  PieChart, Pie, Cell, Tooltip
} from 'recharts';
import {
  FileText,
  Calendar,
  AlertTriangle,
  ArrowRight,
  Copy,
  Check,
  FileSearch
} from 'lucide-react';

export default function DocumentDetails() {
  const { ingestedDocuments, selectedDocId, setSelectedDocId } = useAnalysis();
  const [showFullText, setShowFullText] = useState(false);
  const [copiedText, setCopiedText] = useState(false);

  const currentDoc = ingestedDocuments.find(d => d.id === selectedDocId) || ingestedDocuments[0];

  if (!currentDoc) {
    return (
      <div className="page-transition max-w-xl mx-auto my-12 text-center">
        <div className="bg-[#0F172A] p-8 rounded-xl border border-[#1E293B] text-white shadow-xl space-y-4">
          <FileText className="w-10 h-10 text-indigo-400 mx-auto" />
          <h1 className="text-xl font-bold text-white">No Document Ingested Yet</h1>
          <p className="text-sm text-slate-400 max-w-sm mx-auto">
            No document has been ingested into ChromaDB. Go to the RAG Knowledge page to add your first project or reference document.
          </p>
          <NavLink
            to="/documents"
            className="btn-primary no-underline inline-flex"
          >
            Go to RAG Knowledge Page <ArrowRight className="w-3.5 h-3.5" />
          </NavLink>
        </div>
      </div>
    );
  }

  const {
    project_id,
    filename,
    word_count,
    reading_time_minutes,
    chunks_count,
    risk_mentions = [],
    deadline_mentions = [],
    extracted_text = ''
  } = currentDoc;

  const riskCount = risk_mentions.length || 0;
  const deadlineCount = deadline_mentions.length || 0;
  const totalSentences = Math.max(riskCount + deadlineCount + 2, Math.ceil(word_count / 15));
  const generalCount = Math.max(1, totalSentences - (riskCount + deadlineCount));

  const compositionChartData = [
    { name: 'Risk Mentions', value: riskCount, color: '#EF4444' },
    { name: 'Deadline Mentions', value: deadlineCount, color: '#6366F1' },
    { name: 'General Content', value: generalCount, color: '#64748B' }
  ];

  const handleCopyText = () => {
    navigator.clipboard.writeText(extracted_text);
    setCopiedText(true);
    setTimeout(() => setCopiedText(false), 2000);
  };

  return (
    <div className="page-transition space-y-6">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-[#0F172A] via-[#1E293B] to-[#0F172A] p-6 rounded-2xl border border-[#1E293B] shadow-2xl text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5 font-heading">
            <FileSearch className="w-6 h-6 text-amber-400" />
            Document Insights
          </h1>
          <p className="text-xs text-slate-300 font-medium mt-1">
            NLP extraction breakdown for <strong className="text-white">{filename}</strong>
          </p>
        </div>

        {ingestedDocuments.length > 1 && (
          <select
            value={selectedDocId || currentDoc.id}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="input-signal w-auto font-medium"
          >
            {ingestedDocuments.map(d => (
              <option key={d.id} value={d.id}>
                {d.filename} ({d.project_id || 'General'})
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Summary Multi-Color KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-5 border-l-4 border-l-cyan-500 space-y-1">
          <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider block">
            Document Name
          </span>
          <span className="text-sm font-bold text-white truncate block">
            {filename}
          </span>
          <span className="text-[11px] font-mono text-cyan-400">
            {project_id ? `Project: ${project_id}` : 'General Document'}
          </span>
        </div>

        <div className="glass-card p-5 border-l-4 border-l-purple-500 space-y-1">
          <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider block">
            Word Count
          </span>
          <span className="text-2xl font-bold text-white font-mono">
            {word_count}
          </span>
          <span className="text-[11px] text-slate-300 block">
            ~{reading_time_minutes} min estimated read
          </span>
        </div>

        <div className="glass-card p-5 border-l-4 border-l-amber-500 space-y-1">
          <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider block">
            Vector DB Chunks
          </span>
          <span className="text-2xl font-bold text-amber-400 font-mono">
            {chunks_count}
          </span>
          <span className="text-[11px] text-slate-300 block">
            Indexed in ChromaDB
          </span>
        </div>

        <div className="glass-card p-5 border-l-4 border-l-rose-500 space-y-1">
          <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider block">
            Risk Mentions
          </span>
          <span className="text-2xl font-bold text-rose-400 font-mono">
            {risk_mentions.length}
          </span>
          <span className="text-[11px] text-slate-300 block">
            Extracted bottleneck sentences
          </span>
        </div>
      </div>

      {/* Main Content Grid: Analysis Findings + Composition */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Risk & Deadline Mentions */}
        <div className="lg:col-span-7 glass-card p-5 space-y-4">
          <h2 className="text-sm font-semibold text-white border-b border-[#1E293B] pb-2 font-heading flex items-center justify-between">
            <span>Identified Risk & Bottleneck Sentences</span>
            <span className="text-xs text-rose-400 font-mono font-normal">NLP Extraction</span>
          </h2>

          <div className="space-y-2.5">
            {risk_mentions.length === 0 ? (
              <p className="text-xs text-slate-400">No explicit risk or bottleneck sentences detected in this document.</p>
            ) : (
              risk_mentions.map((rm, idx) => (
                <div key={idx} className="bg-rose-500/10 p-3 rounded-xl border border-rose-500/30 text-xs text-rose-200 flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
                  <span className="leading-relaxed font-medium">{rm}</span>
                </div>
              ))
            )}
          </div>

          <h2 className="text-sm font-semibold text-white border-b border-[#1E293B] pb-2 pt-2 font-heading flex items-center justify-between">
            <span>Key Dates & Target Milestones</span>
            <span className="text-xs text-indigo-400 font-mono font-normal">Milestones</span>
          </h2>

          <div className="space-y-2.5">
            {deadline_mentions.length === 0 ? (
              <p className="text-xs text-slate-400">No target dates or milestones detected.</p>
            ) : (
              deadline_mentions.map((dm, idx) => (
                <div key={idx} className="bg-indigo-500/10 p-3 rounded-xl border border-indigo-500/30 text-xs text-indigo-200 flex items-start gap-2.5">
                  <Calendar className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
                  <span className="leading-relaxed font-medium">{dm}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Content Composition Donut Chart */}
        <div className="lg:col-span-5 glass-card p-5 space-y-4">
          <h2 className="text-sm font-semibold text-white border-b border-[#1E293B] pb-2 font-heading">
            Document Sentence Composition
          </h2>

          <div className="h-56 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={compositionChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {compositionChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#070B14', borderColor: '#1E293B', borderRadius: '8px', color: '#FFFFFF', fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-2 text-xs pt-2 border-t border-[#1E293B]">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.5)]"></span>
                <span className="text-slate-300 font-medium">Risk Mentions</span>
              </span>
              <span className="font-mono font-bold text-white">{riskCount}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 shadow-[0_0_6px_rgba(99,102,241,0.5)]"></span>
                <span className="text-slate-300 font-medium">Deadline Mentions</span>
              </span>
              <span className="font-mono font-bold text-white">{deadlineCount}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-500"></span>
                <span className="text-slate-300 font-medium">General Context</span>
              </span>
              <span className="font-mono font-bold text-white">{generalCount}</span>
            </div>
          </div>
        </div>

      </div>

      {/* Raw Extracted Text Viewer */}
      <div className="glass-card p-5 space-y-3">
        <div className="flex items-center justify-between border-b border-[#1E293B] pb-2">
          <h2 className="text-sm font-semibold text-white font-heading">
            Extracted Text Content
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyText}
              className="btn-secondary text-xs py-1 px-3"
            >
              {copiedText ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedText ? 'Copied' : 'Copy Text'}</span>
            </button>
            <button
              onClick={() => setShowFullText(!showFullText)}
              className="text-xs font-semibold text-cyan-400 hover:underline flex items-center gap-1"
            >
              {showFullText ? 'Collapse' : 'Expand Full'}
            </button>
          </div>
        </div>

        <div className={`bg-[#070B14] p-4 rounded-xl border border-[#1E293B] font-mono text-xs text-amber-300 leading-relaxed overflow-y-auto ${showFullText ? 'max-h-96' : 'max-h-36'}`}>
          {extracted_text || 'No text extracted.'}
        </div>
      </div>

    </div>
  );
}
