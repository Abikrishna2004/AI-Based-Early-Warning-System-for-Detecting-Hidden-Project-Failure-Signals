import React, { useState } from 'react';
import { API_BASE_URL } from '../config';

export default function DocumentsKnowledge() {
  const [ragProjectId, setRagProjectId] = useState('PROJ-101');
  const [ragFile, setRagFile] = useState(null);
  const [ragText, setRagText] = useState('');
  const [ingestLoading, setIngestLoading] = useState(false);
  const [ingestMessage, setIngestMessage] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setRagFile(e.target.files[0]);
    }
  };

  const handleDocumentUploadAndIngest = async (e) => {
    e.preventDefault();
    if (!ragFile && !ragText.trim()) {
      alert("Please select a document file (.pdf / .txt) or enter raw text.");
      return;
    }

    setIngestLoading(true);
    setIngestMessage(null);
    setAnalysisResult(null);

    try {
      let textToIngest = ragText;
      let docName = ragFile ? ragFile.name : 'status_report.txt';

      if (ragFile) {
        const formData = new FormData();
        formData.append('file', ragFile);

        const analyzeRes = await fetch(`${API_BASE_URL}/analyze_document`, {
          method: 'POST',
          body: formData
        });

        if (!analyzeRes.ok) {
          const errData = await analyzeRes.json();
          throw new Error(errData.detail || 'Document analysis failed.');
        }

        const analyzeData = await analyzeRes.json();
        setAnalysisResult(analyzeData);
        textToIngest = analyzeData.extracted_text;
        docName = analyzeData.filename;
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000);

      const ingestRes = await fetch(`${API_BASE_URL}/ingest_document`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          project_id: ragProjectId,
          text: textToIngest,
          document_name: docName
        })
      });
      clearTimeout(timeoutId);

      if (!ingestRes.ok) {
        const errData = await ingestRes.json();
        throw new Error(errData.detail || 'Document ingestion failed.');
      }

      const ingestData = await ingestRes.json();
      setIngestMessage(ingestData.message);
      setRagText('');
    } catch (err) {
      if (err.name === 'AbortError') {
        alert('Upload & Ingest Error: Request timed out after 15 seconds. Please try again.');
      } else {
        alert(`Upload & Ingest Error: ${err.message}`);
      }
    } finally {
      setIngestLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="card-section rag-card m-0">
        <h2 className="text-xl font-bold text-white flex items-center gap-2 m-0 mb-3">
          <span>📚</span> Document Ingestion & Local RAG Knowledge Base
        </h2>
        <p className="text-sm text-slate-300 mb-6 leading-relaxed">
          Upload project status reports (PDF or TXT) or paste text to extract risk patterns, generate embeddings via <code>all-MiniLM-L6-v2</code>, and store vector chunks in <strong>ChromaDB</strong> for project-scoped natural language Q&A.
        </p>

        {/* Document Ingestion Form */}
        <form onSubmit={handleDocumentUploadAndIngest} className="space-y-4 bg-slate-900/60 p-5 rounded-xl border border-slate-800">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="form-label font-semibold">Project ID</label>
              <input
                type="text"
                value={ragProjectId}
                onChange={(e) => setRagProjectId(e.target.value)}
                placeholder="e.g. PROJ-101"
                required
                className="form-input font-mono"
              />
            </div>
            <div>
              <label className="form-label font-semibold">Upload Status Report (PDF / TXT)</label>
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={handleFileChange}
                className="form-input text-xs"
              />
            </div>
          </div>

          <div>
            <label className="form-label font-semibold">Or Paste Document Text Directly</label>
            <textarea
              rows="6"
              value={ragText}
              onChange={(e) => setRagText(e.target.value)}
              placeholder="Paste project weekly status report, risk notes, or meeting minutes here..."
              className="form-input font-mono text-xs"
            />
          </div>

          <button type="submit" disabled={ingestLoading} className="btn-rag-ingest py-3 text-base">
            {ingestLoading ? 'Processing & Ingesting to ChromaDB...' : '📥 Ingest Document into Vector DB'}
          </button>
        </form>

        {/* Ingestion Status Banner */}
        {ingestMessage && (
          <div className="mt-5 p-4 bg-emerald-950/70 border border-emerald-800 rounded-xl text-emerald-300 text-sm font-semibold flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xl">✅</span>
              <span>{ingestMessage}</span>
            </div>
            <a href="/assistant" className="text-xs bg-emerald-900 hover:bg-emerald-800 text-emerald-200 px-3 py-1.5 rounded-lg border border-emerald-700 font-bold transition">
              Go to AI Assistant →
            </a>
          </div>
        )}

        {/* Document Analysis Feedback */}
        {analysisResult && (
          <div className="mt-5 p-4 bg-slate-900 border border-slate-800 rounded-xl text-xs space-y-3">
            <div className="flex items-center justify-between text-slate-200 font-bold border-b border-slate-800 pb-2 text-sm">
              <span>📄 Document Metadata: {analysisResult.filename}</span>
              <span className="text-sky-400 font-mono">{analysisResult.word_count} words • {analysisResult.reading_time_minutes} min read</span>
            </div>
            
            {analysisResult.risk_mentions && analysisResult.risk_mentions.length > 0 && (
              <div>
                <span className="text-amber-400 font-semibold block mb-1 text-sm">⚠️ Risk & Bottleneck Mentions Identified:</span>
                <ul className="list-disc list-inside text-slate-300 space-y-1 bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                  {analysisResult.risk_mentions.map((rm, i) => (
                    <li key={i}>{rm}</li>
                  ))}
                </ul>
              </div>
            )}

            {analysisResult.deadline_mentions && analysisResult.deadline_mentions.length > 0 && (
              <div>
                <span className="text-sky-400 font-semibold block mb-1 text-sm">📅 Key Dates & Milestones Found:</span>
                <ul className="list-disc list-inside text-slate-300 space-y-1 bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                  {analysisResult.deadline_mentions.map((dm, i) => (
                    <li key={i}>{dm}</li>
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
