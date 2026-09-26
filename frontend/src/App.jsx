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
        <div className="min-h-screen bg-[#0A0F1D] text-[#F1F5F9] font-sans flex flex-col selection:bg-indigo-500/30 selection:text-indigo-200 relative overflow-x-hidden">
          
          {/* Subtle Ambient Radial Gradient Mesh Background */}
          <div className="fixed inset-0 pointer-events-none z-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(99,102,241,0.12),rgba(255,255,255,0))]"></div>

          {/* Navigation Bar */}
          <Navbar />

          {/* Page Main Grid Body Container */}
          <main className="flex-1 max-w-[1240px] w-full mx-auto px-6 pt-[88px] pb-12 z-10 relative">
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
