import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AnalysisProvider } from './context/AnalysisContext';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import ProjectInput from './pages/ProjectInput';
import AnalysisResults from './pages/AnalysisResults';
import IngestDocument from './pages/IngestDocument';
import DocumentDetails from './pages/DocumentDetails';
import AiAssistant from './pages/AiAssistant';
import WhatIfSimulator from './pages/WhatIfSimulator';
import './App.css';

export default function App() {
  return (
    <AnalysisProvider>
      <Router>
        <div className="min-h-screen bg-[#0B1220] text-[#E8ECF4] font-sans flex flex-col">
          {/* Signal Room Header Navbar */}
          <Navbar />

          {/* Page Body Container */}
          <main className="flex-1 max-w-[1400px] w-full mx-auto px-6 pt-[90px] pb-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/input" element={<ProjectInput />} />
              <Route path="/results" element={<AnalysisResults />} />
              <Route path="/documents" element={<IngestDocument />} />
              <Route path="/document-details" element={<DocumentDetails />} />
              <Route path="/assistant" element={<AiAssistant />} />
              <Route path="/simulator" element={<WhatIfSimulator />} />
            </Routes>
          </main>
        </div>
      </Router>
    </AnalysisProvider>
  );
}
