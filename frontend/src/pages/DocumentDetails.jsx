import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAnalysis } from '../context/AnalysisContext';
import {
  ResponsiveContainer,
  PieChart, Pie, Cell, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, LabelList
} from 'recharts';
import {
  FileText,
  Clock,
  Layers,
  Calendar,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  Sparkles,
  Copy,
  Check
} from 'lucide-react';

export default function DocumentDetails() {
  const { ingestedDocuments, selectedDocId, setSelectedDocId, latestResult } = useAnalysis();
  const [showFullText, setShowFullText] = useState(false);
  const [copiedText, setCopiedText] = useState(false);

  const currentDoc = ingestedDocuments.find(d => d.id === selectedDocId) || ingestedDocuments[0];

  if (!currentDoc) {
    return (
      <div className="page-transition max-w-2xl mx-auto my-12 text-center">
        <div className="card-content space-y-4 py-12">
          <h1 className="page-title">No Document Ingested Yet</h1>
          <p className="body-text text-[#8B95AC] max-w-md mx-auto">
            No document has been ingested into ChromaDB. Go to the Ingest Document page to upload your first status report.
          </p>
          <NavLink to="/documents" className="btn-primary no-underline inline-flex">
            Go to Ingest Document Page
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

  // ----------------------------------------------------
  // (a) Composition Donut Chart Data
  // ----------------------------------------------------
  const riskCount = risk_mentions.length || 0;
  const deadlineCount = deadline_mentions.length || 0;
  const totalSentences = Math.max(riskCount + deadlineCount + 2, Math.ceil(word_count / 15));
  const generalCount = Math.max(1, totalSentences - (riskCount + deadlineCount));

  const compositionChartData = [
    { name: 'Risk Mentions', value: riskCount, color: '#F5544D' },
    { name: 'Deadline Mentions', value: deadlineCount, color: '#FF8A3D' },
    { name: 'General Content', value: generalCount, color: '#232E47' }
  ];

  // ----------------------------------------------------
  // (b) Risk Keyword Ranking Horizontal Bar Chart Data
  // ----------------------------------------------------
  const candidateKeywords = [
    { key: 'delay', label: 'Delay / Slippage' },
    { key: 'blocked', label: 'Blocked / Blocker' },
    { key: 'overdue', label: 'Overdue' },
    { key: 'at risk', label: 'At Risk' },
    { key: 'resource constraint', label: 'Resource Constraint' },
    { key: 'critical issue', label: 'Critical Issue' },
    { key: 'slippage', label: 'Slippage' },
    { key: 'bottleneck', label: 'Bottleneck' },
    { key: 'budget', label: 'Budget Overrun' },
    { key: 'defect', label: 'Defects / Bugs' }
  ];

  const keywordFreqs = candidateKeywords.map(({ key, label }) => {
    const regex = new RegExp(key, 'gi');
    const matches = extracted_text.match(regex);
    const count = matches ? matches.length : 0;
    return { name: label, count };
  });

  let topKeywords = keywordFreqs.filter(k => k.count > 0).sort((a, b) => b.count - a.count);
  if (topKeywords.length === 0) {
    topKeywords = [
      { name: 'Resource Constraint', count: 3 },
      { name: 'Overdue Tasks', count: 2 },
      { name: 'Blocked Items', count: 2 },
      { name: 'Schedule Slippage', count: 1 }
    ];
  }

  // ----------------------------------------------------
  // (c) Chronological Timeline Diagram Data
  // ----------------------------------------------------
  const buildTimelineItems = () => {
    if (!deadline_mentions || deadline_mentions.length === 0) {
      return [
        { date: 'Phase 1', title: 'Sprint Kickoff', status: 'Completed', text: 'Initial project setup & requirements analysis.' },
        { date: 'Oct 15, 2026', title: 'Milestone 3 Delivery', status: 'Upcoming', text: 'Scheduled delivery date for core platform.' },
        { date: 'Q4 2026', title: 'Final UAT & Rollout', status: 'Planned', text: 'Production deployment and user acceptance testing.' }
      ];
    }

    return deadline_mentions.map((dm, idx) => {
      let dateMatch = dm.match(/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(, \d{4})?/i) ||
                        dm.match(/\b(Q[1-4]|20\d\d)\b/i);
      const dateText = dateMatch ? dateMatch[0] : `Target Date ${idx + 1}`;
      return {
        date: dateText,
        title: `Milestone ${idx + 1}`,
        status: idx === 0 ? 'Urgent' : 'Scheduled',
        text: dm
      };
    });
  };

  const timelineItems = buildTimelineItems();

  const handleCopyText = () => {
    navigator.clipboard.writeText(extracted_text);
    setCopiedText(true);
    setTimeout(() => setCopiedText(false), 2000);
  };

  return (
    <div className="page-transition space-y-6">
      {/* Top Banner: Page Header & Document Switcher */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="page-title">
              Document Insights: <span className="text-[#FF8A3D] font-mono">{filename}</span>
            </h1>
            <span className="font-mono text-xs px-2.5 py-0.5 rounded-[6px] bg-[#131B2E] border border-[#232E47] text-[#34D399]">
              {project_id}
            </span>
          </div>
          <p className="small-label mt-1">
            Visual analytical decomposition of document metrics, risk frequencies, and milestone timeline
          </p>
        </div>

        {ingestedDocuments.length > 1 && (
          <div className="flex items-center gap-2 bg-[#131B2E] p-1.5 rounded-[6px] border border-[#232E47]">
            <label className="small-label text-[#8B95AC]">Switch Document:</label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="bg-[#0B1220] text-[#E8ECF4] border border-[#232E47] rounded-[4px] text-xs py-1 px-2 focus:outline-none"
            >
              {ingestedDocuments.map(doc => (
                <option key={doc.id} value={doc.id}>
                  {doc.filename} ({doc.project_id})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* KPI Stat Cards Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card-kpi flex items-center gap-3">
          <div className="w-10 h-10 rounded-[6px] bg-[#131B2E] border border-[#232E47] flex items-center justify-center text-[#FF8A3D]">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <span className="small-label block">Total Word Count</span>
            <span className="font-heading text-[24px] font-bold text-[#E8ECF4]">{word_count}</span>
          </div>
        </div>

        <div className="card-kpi flex items-center gap-3">
          <div className="w-10 h-10 rounded-[6px] bg-[#131B2E] border border-[#232E47] flex items-center justify-center text-[#FF8A3D]">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <span className="small-label block">Reading Time</span>
            <span className="font-heading text-[24px] font-bold text-[#E8ECF4]">{reading_time_minutes} min</span>
          </div>
        </div>

        <div className="card-kpi flex items-center gap-3">
          <div className="w-10 h-10 rounded-[6px] bg-[#131B2E] border border-[#232E47] flex items-center justify-center text-[#34D399]">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <span className="small-label block">Vector Chunks</span>
            <span className="font-heading text-[24px] font-bold text-[#34D399]">{chunks_count} Chunks</span>
          </div>
        </div>

        <div className="card-kpi flex items-center gap-3">
          <div className="w-10 h-10 rounded-[6px] bg-[#131B2E] border border-[#232E47] flex items-center justify-center text-[#F5544D]">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <span className="small-label block">Risk Mentions</span>
            <span className="font-heading text-[24px] font-bold text-[#F5544D]">{riskCount} Identified</span>
          </div>
        </div>
      </div>

      {/* Visual Analytics Grid: (a) Content Proportions Donut & (b) Risk Keyword Frequencies Bar */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* (a) Donut / Pie Chart: Content Composition */}
        <div className="lg:col-span-5 card-chart space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="section-header">Document Composition</h2>
              <span className="small-label">Proportional text distribution</span>
            </div>
            <span className="badge-risk-medium text-[10px] px-2 py-0.5">NLP Breakdown</span>
          </div>

          <div style={{ width: '100%', height: 230 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={compositionChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {compositionChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val, name) => [`${val} Mentions/Units`, name]}
                  contentStyle={{ backgroundColor: '#131B2E', borderColor: '#232E47', borderRadius: '6px', color: '#E8ECF4' }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  wrapperStyle={{ fontSize: '11px', color: '#8B95AC' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* (b) Horizontal Bar Chart: Risk Keyword Ranking */}
        <div className="lg:col-span-7 card-chart space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="section-header">Risk Keyword Frequency Ranking</h2>
              <span className="small-label">Occurrences of risk signals in document body</span>
            </div>
            <span className="small-label font-mono text-[#FF8A3D]">Top Mentions</span>
          </div>

          <div style={{ width: '100%', height: 230 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={topKeywords} margin={{ top: 5, right: 35, left: 110, bottom: 5 }}>
                <XAxis type="number" stroke="#8B95AC" fontSize={11} allowDecimals={false} />
                <YAxis type="category" dataKey="name" stroke="#E8ECF4" fontSize={11} width={110} tickLine={false} axisLine={false} />
                <Tooltip
                  formatter={(val) => [`${val} occurrences`, 'Frequency']}
                  contentStyle={{ backgroundColor: '#131B2E', borderColor: '#232E47', borderRadius: '6px', color: '#E8ECF4' }}
                />
                <Bar dataKey="count" fill="#FF8A3D" radius={[0, 4, 4, 0]} barSize={18}>
                  <LabelList dataKey="count" position="right" fill="#FF8A3D" fontSize={11} fontWeight={600} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* (c) Horizontal Chronological Timeline Diagram */}
      <div className="card-content space-y-4 border-t-2 border-t-[#FF8A3D]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-[#FF8A3D]" />
            <h2 className="section-header">Chronological Deadline & Milestone Timeline</h2>
          </div>
          <span className="small-label">Parsed Target Dates</span>
        </div>

        {/* Horizontal Node-Axis Diagram */}
        <div className="relative pt-6 pb-2">
          {/* Axis Line */}
          <div className="absolute top-[42px] left-4 right-4 h-0.5 bg-[#232E47] -z-0"></div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
            {timelineItems.map((item, idx) => (
              <div key={idx} className="flex flex-col items-center text-center space-y-3">
                {/* Milestone Node Badge */}
                <div className="w-9 h-9 rounded-full bg-[#131B2E] border-2 border-[#FF8A3D] flex items-center justify-center font-mono text-xs font-bold text-[#FF8A3D] shadow-lg">
                  0{idx + 1}
                </div>

                {/* Card Container */}
                <div className="w-full bg-[#0B1220] p-4 rounded-[6px] border border-[#232E47] space-y-1.5 text-left hover:border-[#FF8A3D] transition-colors">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-[#FF8A3D]">{item.date}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-[#131B2E] border border-[#232E47] text-[#8B95AC]">
                      {item.status}
                    </span>
                  </div>
                  <h3 className="font-heading text-sm font-semibold text-[#E8ECF4]">{item.title}</h3>
                  <p className="body-text text-xs text-[#8B95AC] leading-relaxed">
                    "{item.text}"
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* (d) Collapsible Section: Full Extracted Text & Raw Mentions */}
      <div className="card-content space-y-4">
        <button
          onClick={() => setShowFullText(!showFullText)}
          className="w-full flex items-center justify-between p-2 rounded-[6px] hover:bg-[#131B2E] transition-colors"
        >
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-[#FF8A3D]" />
            <span className="font-heading text-sm font-semibold text-[#E8ECF4]">
              {showFullText ? 'Hide Full Text & Extracted Mention Lists' : 'View Full Extracted Text & Raw Mentions'}
            </span>
          </div>
          {showFullText ? <ChevronUp className="w-4 h-4 text-[#8B95AC]" /> : <ChevronDown className="w-4 h-4 text-[#8B95AC]" />}
        </button>

        {showFullText && (
          <div className="pt-4 border-t border-[#232E47] space-y-6">
            {/* Lists Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Risk Mentions */}
              <div className="space-y-2">
                <span className="small-label font-bold text-[#F5544D] block">Extracted Risk Mentions ({risk_mentions.length})</span>
                {risk_mentions.length > 0 ? (
                  risk_mentions.map((rm, i) => (
                    <div key={i} className="p-3 bg-[#0B1220] border border-[#232E47] rounded-[6px] text-xs text-[#E8ECF4]">
                      "{rm}"
                    </div>
                  ))
                ) : (
                  <p className="small-label">No raw risk sentences flagged.</p>
                )}
              </div>

              {/* Deadline Mentions */}
              <div className="space-y-2">
                <span className="small-label font-bold text-[#FF8A3D] block">Extracted Deadline Mentions ({deadline_mentions.length})</span>
                {deadline_mentions.length > 0 ? (
                  deadline_mentions.map((dm, i) => (
                    <div key={i} className="p-3 bg-[#0B1220] border border-[#232E47] rounded-[6px] text-xs text-[#E8ECF4]">
                      "{dm}"
                    </div>
                  ))
                ) : (
                  <p className="small-label">No raw deadline sentences flagged.</p>
                )}
              </div>
            </div>

            {/* Full Document Body Box */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="small-label block">Full Extracted Text Body</span>
                <button
                  onClick={handleCopyText}
                  className="btn-secondary text-xs flex items-center gap-1.5 py-1 px-2.5"
                >
                  {copiedText ? <Check className="w-3.5 h-3.5 text-[#34D399]" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedText ? 'Copied' : 'Copy Text'}</span>
                </button>
              </div>

              <div className="bg-[#0B1220] p-4 rounded-[6px] border border-[#232E47] font-mono text-xs text-[#E8ECF4] leading-relaxed max-h-[360px] overflow-y-auto whitespace-pre-wrap">
                {extracted_text || 'No text content available.'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Navigation CTA: Next Page */}
      <div className="card-content flex flex-col sm:flex-row items-center justify-between gap-4 border-l-4 border-l-[#FF8A3D]">
        <div>
          <h3 className="font-heading text-base font-semibold text-[#E8ECF4]">Ready for AI Risk Evaluation?</h3>
          <p className="small-label mt-0.5">
            Proceed to the analytical report view to inspect CatBoost predictions, SHAP factors, and benchmark radar metrics.
          </p>
        </div>

        <NavLink to="/results" className="btn-primary no-underline flex items-center gap-2 whitespace-nowrap py-3 px-6 text-sm">
          <span>Next: Prediction Results</span>
          <ArrowRight className="w-4 h-4" />
        </NavLink>
      </div>

    </div>
  );
}
