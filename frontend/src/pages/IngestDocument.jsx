import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';
import {
  Sparkles,
  Plus,
  BarChart2,
  Search,
  Eye,
  X,
  BookOpen
} from 'lucide-react';

export default function IngestDocument() {
  // 1. Knowledge Scope: 'project' | 'general'
  const [scope, setScope] = useState('project');

  // 2. Database Objects
  const [projectsList, setProjectsList] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');

  const [sourcesList, setSourcesList] = useState([]);
  const [selectedSourceId, setSelectedSourceId] = useState('');

  // 3. Question & Answer
  const [question, setQuestion] = useState('');
  const [queryStatus, setQueryStatus] = useState(null); // null | 'searching' | 'generating'
  const [answerResult, setAnswerResult] = useState(null);

  // 4. History
  const [ragSessions, setRagSessions] = useState([]);
  const [showAllHistory, setShowAllHistory] = useState(false);
  const [selectedHistoryDetail, setSelectedHistoryDetail] = useState(null);

  // 5. Add Source Modal State
  const [isAddSourceOpen, setIsAddSourceOpen] = useState(false);
  const [newSourceName, setNewSourceName] = useState('');
  const [newSourceFile, setNewSourceFile] = useState(null);
  const [newSourceText, setNewSourceText] = useState('');
  const [addSourceLoading, setAddSourceLoading] = useState(false);

  // 6. Risk Analysis Button Loading State
  const [analysisLoading, setAnalysisLoading] = useState(false);

  useEffect(() => {
    fetchProjects();
    fetchRAGHistory();
  }, []);

  useEffect(() => {
    if (scope === 'project') {
      if (selectedProjectId) {
        fetchSourcesForProject(selectedProjectId);
      } else {
        setSourcesList([]);
        setSelectedSourceId('');
      }
    } else {
      fetchGeneralSources();
    }
  }, [scope, selectedProjectId]);

  const fetchProjects = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/projects`);
      if (res.ok) {
        const data = await res.json();
        setProjectsList(data);
        if (data.length > 0) {
          setSelectedProjectId(data[0].project_id);
        }
      }
    } catch (err) {
      console.error("Failed to fetch projects:", err);
    }
  };

  const fetchSourcesForProject = async (projId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/rag_sources?project_id=${projId}`);
      if (res.ok) {
        const data = await res.json();
        setSourcesList(data);
        if (data.length > 0) {
          setSelectedSourceId(data[0].source_id);
        } else {
          setSelectedSourceId('');
        }
      }
    } catch (err) {
      console.error("Failed to fetch project sources:", err);
    }
  };

  const fetchGeneralSources = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/rag_sources?is_independent=true`);
      if (res.ok) {
        const data = await res.json();
        setSourcesList(data);
        if (data.length > 0) {
          setSelectedSourceId(data[0].source_id);
        } else {
          setSelectedSourceId('');
        }
      }
    } catch (err) {
      console.error("Failed to fetch general sources:", err);
    }
  };

  const fetchRAGHistory = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/rag_sessions`);
      if (res.ok) {
        const data = await res.json();
        setRagSessions(data);
      }
    } catch (err) {
      console.error("Failed to fetch RAG history:", err);
    }
  };

  const handleUseLatestRiskAnalysis = async () => {
    if (!selectedProjectId) return;
    setAnalysisLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/rag_sources/create_from_analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: selectedProjectId })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to convert project analysis.');
      }
      const data = await res.json();
      await fetchSourcesForProject(selectedProjectId);
      setSelectedSourceId(data.source_id);
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleCreateSourceSubmit = async (e) => {
    e.preventDefault();
    if (!newSourceName.trim() && !newSourceFile && !newSourceText.trim()) {
      alert("Please provide a source name, upload a file, or paste text.");
      return;
    }

    setAddSourceLoading(true);
    try {
      let textContent = newSourceText.trim();
      let fileName = newSourceFile ? newSourceFile.name : null;

      if (newSourceFile) {
        const fileContent = await newSourceFile.text();
        if (fileContent && fileContent.trim()) {
          textContent = fileContent.trim();
        }
      }

      if (!textContent) {
        alert("Could not extract text content from the provided file or input. Please paste text directly.");
        setAddSourceLoading(false);
        return;
      }

      const payload = {
        project_id: scope === 'project' ? selectedProjectId : null,
        source_type: scope === 'project' ? 'PROJECT_DOCUMENT' : 'INDEPENDENT_DOCUMENT',
        source_name: newSourceName.trim() || fileName || 'New Knowledge Source',
        file_name: fileName,
        text: textContent
      };

      const res = await fetch(`${API_BASE_URL}/rag_sources/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to create source.');
      }

      const created = await res.json();
      setIsAddSourceOpen(false);
      setNewSourceName('');
      setNewSourceFile(null);
      setNewSourceText('');

      if (scope === 'project' && selectedProjectId) {
        await fetchSourcesForProject(selectedProjectId);
      } else {
        await fetchGeneralSources();
      }
      setSelectedSourceId(created.source_id);
    } catch (err) {
      alert(`Create Source Error: ${err.message}`);
    } finally {
      setAddSourceLoading(false);
    }
  };

  const handleAskCompilePulse = async (e) => {
    e.preventDefault();
    if (!question.trim()) {
      alert("Please enter a question.");
      return;
    }
    if (!selectedSourceId) {
      alert("Please select a knowledge source.");
      return;
    }

    setQueryStatus('searching');
    setAnswerResult(null);

    const timer = setTimeout(() => {
      setQueryStatus('generating');
    }, 1200);

    try {
      const res = await fetch(`${API_BASE_URL}/ask_rag`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: question.trim(),
          source_id: selectedSourceId,
          project_id: scope === 'project' ? selectedProjectId : null
        })
      });

      clearTimeout(timer);

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'RAG query failed.');
      }

      const data = await res.json();
      setAnswerResult(data);
      fetchRAGHistory();
    } catch (err) {
      alert(`Query Error: ${err.message}`);
    } finally {
      setQueryStatus(null);
    }
  };

  const formatTime = (isoString) => {
    if (!isoString) return '—';
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return isoString;
    }
  };

  const formatFullDate = (isoString) => {
    if (!isoString) return '—';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) + ', ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return isoString;
    }
  };

  const displayedHistory = showAllHistory ? ragSessions : ragSessions.slice(0, 5);

  return (
    <div className="page-transition max-w-4xl mx-auto space-y-6">
      
      {/* 1. Header Banner */}
      <div className="bg-gradient-to-r from-[#0F172A] via-[#1E293B] to-[#0F172A] p-6 rounded-2xl border border-[#1E293B] shadow-2xl text-white space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5 font-heading">
          <BookOpen className="w-6 h-6 text-emerald-400" />
          RAG Knowledge
        </h1>
        <p className="text-xs text-slate-300 font-medium">
          Ask questions from project or reference knowledge.
        </p>
      </div>

      {/* 2. Scope & Project Selector Card */}
      <div className="glass-card p-5 space-y-4 border-l-4 border-l-emerald-500">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          
          {/* Knowledge Scope Dropdown */}
          <div>
            <label className="block text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">
              Knowledge Scope
            </label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value)}
              className="input-signal font-medium"
            >
              <option value="project">Project Knowledge</option>
              <option value="general">General Knowledge</option>
            </select>
          </div>

          {/* Project Dropdown (Visible only for Project Knowledge) */}
          {scope === 'project' && (
            <div>
              <label className="block text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-2">
                Project
              </label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="input-signal font-medium"
              >
                {projectsList.length === 0 ? (
                  <option value="">No projects available in database</option>
                ) : (
                  projectsList.map((p) => (
                    <option key={p.project_id} value={p.project_id}>
                      {p.project_id} — {p.project_name}
                    </option>
                  ))
                )}
              </select>
            </div>
          )}

        </div>

        {/* 3. Knowledge Source Selection & Actions */}
        <div className="pt-3 border-t border-[#1E293B]">
          <div className="flex flex-col sm:flex-row sm:items-end gap-3 justify-between">
            <div className="flex-1">
              <label className="block text-xs font-semibold text-purple-400 uppercase tracking-wider mb-2">
                Knowledge Source
              </label>
              <select
                value={selectedSourceId}
                onChange={(e) => setSelectedSourceId(e.target.value)}
                className="input-signal font-medium"
              >
                {sourcesList.length === 0 ? (
                  <option value="">No stored sources found</option>
                ) : (
                  sourcesList.map((s) => (
                    <option key={s.source_id} value={s.source_id}>
                      {s.source_id} — {s.source_name}
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* Compact Action Buttons */}
            <div className="flex items-center gap-2 flex-wrap pt-1 sm:pt-0">
              <button
                type="button"
                onClick={() => setIsAddSourceOpen(true)}
                className="btn-secondary"
              >
                <Plus className="w-3.5 h-3.5 text-cyan-400" />
                <span>+ Add Source</span>
              </button>

              {scope === 'project' && selectedProjectId && (
                <button
                  type="button"
                  onClick={handleUseLatestRiskAnalysis}
                  disabled={analysisLoading}
                  className="px-3.5 py-2 rounded-lg bg-indigo-500/15 hover:bg-indigo-500/25 text-indigo-300 border border-indigo-500/40 text-xs font-semibold flex items-center gap-1.5 transition disabled:opacity-50"
                >
                  <BarChart2 className="w-3.5 h-3.5 text-indigo-400" />
                  <span>{analysisLoading ? 'Converting Analysis...' : 'Use Latest Risk Analysis'}</span>
                </button>
              )}
            </div>
          </div>
        </div>

      </div>

      {/* 4. Question Input Box Card */}
      <div className="glass-card p-5 space-y-3 border-l-4 border-l-cyan-500">
        <label className="block text-xs font-semibold text-cyan-400 uppercase tracking-wider">
          Ask a Question
        </label>
        <textarea
          rows={3}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask something about the selected knowledge..."
          className="input-signal resize-none"
        />

        <div className="flex items-center justify-between">
          <div className="text-xs font-medium">
            {queryStatus === 'searching' && (
              <span className="text-cyan-400 flex items-center gap-1.5 animate-pulse font-semibold">
                <Search className="w-3.5 h-3.5 animate-spin" />
                Searching knowledge...
              </span>
            )}
            {queryStatus === 'generating' && (
              <span className="text-purple-400 flex items-center gap-1.5 animate-pulse font-semibold">
                <Sparkles className="w-3.5 h-3.5 animate-spin" />
                Generating answer...
              </span>
            )}
          </div>

          <button
            type="button"
            onClick={handleAskCompilePulse}
            disabled={!!queryStatus || !selectedSourceId}
            className="btn-primary"
          >
            <Sparkles className="w-4 h-4" />
            <span>{queryStatus ? 'Processing...' : 'Ask CompilePulse'}</span>
          </button>
        </div>
      </div>

      {/* 5. AI Answer Display Card */}
      {answerResult && (
        <div className="glass-card p-6 border-l-4 border-l-purple-500 text-white shadow-2xl space-y-4 animate-fadeIn">
          <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
            <h3 className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              Answer
            </h3>
            <span className="text-[11px] font-mono text-slate-400">
              {formatTime(answerResult.created_at)}
            </span>
          </div>

          <p className="text-sm text-slate-100 leading-relaxed font-normal whitespace-pre-line">
            {answerResult.answer}
          </p>

          {/* Retrieved Source Context Chunks */}
          {answerResult.retrieved_chunks && answerResult.retrieved_chunks.length > 0 && (
            <div className="pt-2 border-t border-[#1E293B] space-y-2">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Retrieved Context:
              </span>
              <div className="space-y-1.5">
                {answerResult.retrieved_chunks.map((chunk, idx) => (
                  <div key={idx} className="bg-[#070B14] p-3 rounded-lg border border-[#1E293B] text-xs text-purple-300 font-mono leading-normal">
                    {chunk.chunk_text}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Bottom Source & Project Metadata Pills */}
          <div className="flex items-center gap-3 pt-2 text-xs font-mono text-slate-300">
            <span className="bg-[#070B14] px-3 py-1 rounded-md border border-[#1E293B]">
              Source: <strong className="text-purple-400">{answerResult.source_id}</strong>
            </span>
            {answerResult.project_id && (
              <span className="bg-[#070B14] px-3 py-1 rounded-md border border-[#1E293B]">
                Project: <strong className="text-cyan-400">{answerResult.project_id}</strong>
              </span>
            )}
          </div>
        </div>
      )}

      {/* 6. Recent Queries Table */}
      <div className="glass-card overflow-hidden">
        <div className="bg-[#090D16] p-4 text-white flex items-center justify-between border-b border-[#1E293B]">
          <div className="flex items-center gap-2.5">
            <h2 className="text-base font-bold text-white tracking-tight">
              Recent Queries
            </h2>
            <span className="px-2.5 py-0.5 rounded-full bg-[#1E293B] border border-[#334155] text-xs text-cyan-400 font-medium font-mono">
              {ragSessions.length} queries
            </span>
          </div>

          {ragSessions.length > 5 && (
            <button
              onClick={() => setShowAllHistory(!showAllHistory)}
              className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition"
            >
              {showAllHistory ? 'Show Less' : 'View All →'}
            </button>
          )}
        </div>

        {/* Dynamic Table */}
        <div className="overflow-x-auto p-4 pt-2">
          <table className="w-full text-left text-xs text-slate-200">
            <thead className="bg-[#070B14] text-slate-400 font-semibold uppercase tracking-wider border-b border-[#1E293B]">
              <tr>
                <th className="py-2.5 px-3 font-mono">Session</th>
                <th className="py-2.5 px-3">Project</th>
                <th className="py-2.5 px-3">Source</th>
                <th className="py-2.5 px-3">Question</th>
                <th className="py-2.5 px-3 font-mono">Time</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E293B]/60">
              {displayedHistory.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    No historical RAG queries logged in database yet.
                  </td>
                </tr>
              ) : (
                displayedHistory.map((row) => (
                  <tr key={row.rag_session_id} className="hover:bg-[#1E293B]/40 transition">
                    <td className="py-2.5 px-3 font-mono text-purple-400 font-semibold">
                      {row.rag_session_id}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-cyan-400">
                      {row.project_id || 'General'}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-200 font-medium">
                      {row.source_id}
                    </td>
                    <td className="py-2.5 px-3 max-w-[260px] truncate font-medium text-slate-100">
                      {row.query}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">
                      {formatTime(row.created_at)}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => setSelectedHistoryDetail(row)}
                        className="btn-secondary text-[11px] py-1 px-2.5"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 7. Dark Modal: View History Details */}
      {selectedHistoryDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs animate-fadeIn">
          <div className="bg-[#0F172A] border border-[#1E293B] text-white rounded-xl max-w-xl w-full p-6 space-y-4 shadow-2xl relative">
            <button
              onClick={() => setSelectedHistoryDetail(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="border-b border-[#1E293B] pb-3">
              <h3 className="text-base font-mono font-bold text-indigo-400">
                {selectedHistoryDetail.rag_session_id}
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Created: {formatFullDate(selectedHistoryDetail.created_at)}
              </p>
            </div>

            <div className="space-y-3 text-xs text-slate-200">
              <div>
                <span className="text-slate-400 font-semibold uppercase block mb-0.5">Project:</span>
                <span className="font-mono text-white font-bold">{selectedHistoryDetail.project_id || 'General'}</span>
              </div>

              <div>
                <span className="text-slate-400 font-semibold uppercase block mb-0.5">Source:</span>
                <span className="font-mono text-indigo-400 font-bold">{selectedHistoryDetail.source_id} {selectedHistoryDetail.source_name !== '—' ? `(${selectedHistoryDetail.source_name})` : ''}</span>
              </div>

              <div>
                <span className="text-slate-400 font-semibold uppercase block mb-0.5">Question:</span>
                <p className="bg-[#0B1220] p-3 rounded-lg border border-[#1E293B] font-medium text-white">
                  {selectedHistoryDetail.query}
                </p>
              </div>

              <div>
                <span className="text-slate-400 font-semibold uppercase block mb-0.5">Answer:</span>
                <p className="bg-[#0B1220] p-3 rounded-lg border border-[#1E293B] whitespace-pre-line leading-relaxed text-slate-200">
                  {selectedHistoryDetail.answer || 'No answer recorded.'}
                </p>
              </div>

              {selectedHistoryDetail.retrieved_context && (
                <div>
                  <span className="text-slate-400 font-semibold uppercase block mb-0.5">Retrieved Knowledge:</span>
                  <div className="bg-[#0B1220] p-3 rounded-lg border border-[#1E293B] font-mono text-[11px] text-indigo-300 max-h-36 overflow-y-auto whitespace-pre-line">
                    {selectedHistoryDetail.retrieved_context}
                  </div>
                </div>
              )}
            </div>

            <div className="pt-2 text-right border-t border-[#1E293B]">
              <button
                onClick={() => setSelectedHistoryDetail(null)}
                className="px-4 py-2 rounded-lg bg-[#1E293B] hover:bg-[#334155] text-white text-xs font-semibold transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 8. Dark Modal: Add Knowledge Source */}
      {isAddSourceOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs animate-fadeIn">
          <form onSubmit={handleCreateSourceSubmit} className="bg-[#0F172A] border border-[#1E293B] text-white rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl relative">
            <button
              type="button"
              onClick={() => setIsAddSourceOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="border-b border-[#1E293B] pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Plus className="w-4 h-4 text-indigo-400" />
                Add Knowledge Source
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Scope: <strong className="text-white uppercase">{scope} knowledge</strong>
                {scope === 'project' && ` (${selectedProjectId})`}
              </p>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold uppercase mb-1">
                  Source Name
                </label>
                <input
                  type="text"
                  value={newSourceName}
                  onChange={(e) => setNewSourceName(e.target.value)}
                  placeholder="e.g. Weekly Architecture Meeting Notes"
                  className="w-full bg-[#0B1220] border border-[#1E293B] text-white rounded-lg p-2.5 text-xs outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold uppercase mb-1">
                  Upload File (.txt, .pdf, .md)
                </label>
                <input
                  type="file"
                  accept=".txt,.pdf,.md"
                  onChange={(e) => setNewSourceFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full bg-[#0B1220] border border-[#1E293B] text-slate-300 rounded-lg p-2 text-xs outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold uppercase mb-1">
                  Or Paste Text
                </label>
                <textarea
                  rows={4}
                  value={newSourceText}
                  onChange={(e) => setNewSourceText(e.target.value)}
                  placeholder="Paste document or knowledge reference content here..."
                  className="w-full bg-[#0B1220] border border-[#1E293B] text-white rounded-lg p-2.5 text-xs font-mono outline-none focus:border-indigo-500 resize-none"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#1E293B]">
              <button
                type="button"
                onClick={() => setIsAddSourceOpen(false)}
                className="px-4 py-2 rounded-lg bg-[#1E293B] hover:bg-[#334155] text-white text-xs font-semibold transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={addSourceLoading}
                className="btn-primary text-xs font-semibold"
              >
                {addSourceLoading ? 'Creating...' : 'Create Source'}
              </button>
            </div>
          </form>
        </div>
      )}

    </div>
  );
}
