import React, { createContext, useContext, useState } from 'react';

const AnalysisContext = createContext();

export function AnalysisProvider({ children }) {
  const [latestResult, setLatestResult] = useState(null);
  const [latestInput, setLatestInput] = useState(null);
  const [ingestedDocuments, setIngestedDocuments] = useState([
    // Pre-populate with a default document example if available
    {
      id: 'default-doc-1',
      project_id: 'PROJ-101',
      filename: 'sample_status_report.txt',
      word_count: 85,
      reading_time_minutes: 0.43,
      chunks_count: 3,
      risk_mentions: [
        "Task 4 is currently blocked due to severe resource constraint on backend engineering.",
        "Overdue tasks increased to 57.1% creating slippage concern for upcoming Q4 milestone."
      ],
      deadline_mentions: [
        "Milestone 3 delivery is scheduled for October 15, 2026."
      ],
      extracted_text: "CompilePulse Weekly Status Report - Week 20.\nMilestone 3 delivery is scheduled for October 15, 2026.\nTask 4 is currently blocked due to severe resource constraint on backend engineering.\nOverdue tasks increased to 57.1% creating slippage concern for upcoming Q4 milestone.",
      timestamp: new Date().toISOString()
    }
  ]);
  const [selectedDocId, setSelectedDocId] = useState('default-doc-1');

  const setPredictionData = (resultData, inputData) => {
    setLatestResult(resultData);
    setLatestInput(inputData);
  };

  const addIngestedDocument = (docData) => {
    const newDoc = {
      id: `doc-${Date.now()}`,
      ...docData,
      timestamp: new Date().toISOString()
    };
    setIngestedDocuments(prev => [newDoc, ...prev]);
    setSelectedDocId(newDoc.id);
  };

  return (
    <AnalysisContext.Provider
      value={{
        latestResult,
        latestInput,
        setPredictionData,
        ingestedDocuments,
        addIngestedDocument,
        selectedDocId,
        setSelectedDocId
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  const context = useContext(AnalysisContext);
  if (!context) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
}
