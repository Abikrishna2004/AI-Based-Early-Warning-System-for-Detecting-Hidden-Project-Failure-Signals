import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAnalysis } from '../context/AnalysisContext';
import { UploadCloud, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function IngestDocument() {
  const [ragProjectId, setRagProjectId] = useState('PROJ-101');
  const [ragFile, setRagFile] = useState(null);
  const [ragText, setRagText] = useState('');
  const [ingestLoading, setIngestLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const { addIngestedDocument } = useAnalysis();
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setRagFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setRagFile(e.dataTransfer.files[0]);
    }
  };

  const handleDocumentUploadAndIngest = async (e) => {
    e.preventDefault();
    if (!ragFile && !ragText.trim()) {
      alert("Please select a document file (.pdf / .txt) or enter raw text.");
      return;
    }

    setIngestLoading(true);
    setError(null);

    try {
      let textToIngest = ragText;
      let docName = ragFile ? ragFile.name : 'status_report.txt';
      let wordCount = textToIngest.split(/\s+/).filter(Boolean).length;
      let readingTime = roundTwo(wordCount / 200.0);
      let riskMentions = [];
      let deadlineMentions = [];

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
        textToIngest = analyzeData.extracted_text;
        docName = analyzeData.filename;
        wordCount = analyzeData.word_count;
        readingTime = analyzeData.reading_time_minutes;
        riskMentions = analyzeData.risk_mentions || [];
        deadlineMentions = analyzeData.deadline_mentions || [];
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

      // Store in shared context
      addIngestedDocument({
        project_id: ragProjectId,
        filename: docName,
        word_count: wordCount,
        reading_time_minutes: readingTime,
        chunks_count: ingestData.chunks_ingested || 3,
        risk_mentions: riskMentions,
        deadline_mentions: deadlineMentions,
        extracted_text: textToIngest
      });

      // Automatically navigate to Document Details page
      navigate('/document-details');
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Upload & Ingest Error: Request timed out after 15 seconds. Please try again.');
      } else {
        setError(`Upload & Ingest Error: ${err.message}`);
      }
    } finally {
      setIngestLoading(false);
    }
  };

  const roundTwo = (num) => Math.round((num + Number.EPSILON) * 100) / 100;

  return (
    <div className="page-transition max-w-3xl mx-auto space-y-6">
      <div className="card-content space-y-6">
        <div>
          <h1 className="page-title">Document Ingestion & Knowledge Base</h1>
          <p className="small-label mt-1">
            Upload status reports (PDF/TXT) or paste text to generate embeddings via all-MiniLM-L6-v2 into ChromaDB
          </p>
        </div>

        {error && (
          <div className="p-4 bg-[#131B2E] border border-[#F5544D] rounded-[6px] text-[#F5544D] text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleDocumentUploadAndIngest} className="space-y-5">
          <div>
            <label className="emphasis-label block mb-1">Project ID Context</label>
            <input
              type="text"
              value={ragProjectId}
              onChange={(e) => setRagProjectId(e.target.value)}
              placeholder="e.g. PROJ-101"
              required
              className="input-signal font-mono font-medium"
            />
          </div>

          {/* Drag & Drop Upload Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-[10px] p-8 text-center cursor-pointer transition-colors ${
              isDragOver
                ? 'border-[#FF8A3D] bg-[#1A243B]'
                : 'border-[#232E47] bg-[#0B1220] hover:border-[#FF8A3D]'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt"
              onChange={handleFileChange}
              className="hidden"
            />
            <div className="flex flex-col items-center justify-center space-y-2">
              <div className="w-12 h-12 rounded-full bg-[#131B2E] border border-[#232E47] flex items-center justify-center text-[#FF8A3D]">
                <UploadCloud className="w-6 h-6" />
              </div>
              <div>
                <span className="body-text font-semibold block text-[#E8ECF4]">
                  {ragFile ? `Selected: ${ragFile.name}` : 'Drag and drop status report file here (.pdf / .txt)'}
                </span>
                <span className="small-label block mt-0.5">Or click anywhere to browse local files</span>
              </div>
            </div>
          </div>

          <div>
            <label className="emphasis-label block mb-1">Or Paste Raw Document Text Directly</label>
            <textarea
              rows="5"
              value={ragText}
              onChange={(e) => setRagText(e.target.value)}
              placeholder="Paste weekly status report or meeting notes here..."
              className="input-signal font-mono text-xs"
            />
          </div>

          <button type="submit" disabled={ingestLoading} className="btn-primary w-full py-3 text-base">
            {ingestLoading ? 'Ingesting Vector Chunks into ChromaDB...' : 'Ingest Document & View Details'}
          </button>
        </form>
      </div>
    </div>
  );
}
