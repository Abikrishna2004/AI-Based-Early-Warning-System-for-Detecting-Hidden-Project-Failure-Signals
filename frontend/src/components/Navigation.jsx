import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';

import { API_BASE_URL } from '../config';

export default function Navigation() {
  const [apiHealth, setApiHealth] = useState('checking');

  useEffect(() => {
    fetch(`${API_BASE_URL}/`)
      .then(res => res.json())
      .then(() => setApiHealth('online'))
      .catch(() => setApiHealth('offline'));
  }, []);

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/analyze', label: 'Analyze Project', icon: '🚀' },
    { path: '/documents', label: 'Documents & Knowledge Base', icon: '📚' },
    { path: '/assistant', label: 'AI Assistant', icon: '🤖' },
    { path: '/simulator', label: 'What-If Simulator', icon: '🎛️' },
  ];

  return (
    <header className="header-card flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div>
        <div className="flex items-center gap-3 mb-2">
          <h1 className="header-title text-2xl font-bold text-white flex items-center gap-2 m-0">
            <span>🛡️</span> Project Sentinel
          </h1>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-sky-950 text-sky-400 border border-sky-800 font-mono">
            v1.5.0 Multi-Page
          </span>
        </div>
        <p className="header-subtitle text-xs text-slate-400 m-0">
          AI Risk Early Warning, SHAP Explainability, Local ChromaDB RAG & Portfolio Analytics
        </p>

        {/* Navigation Tabs */}
        <nav className="nav-container mt-4 flex flex-wrap gap-2">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `nav-link ${isActive ? 'nav-link-active' : ''}`
              }
            >
              <span className="mr-1.5">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="self-start md:self-center">
        {apiHealth === 'online' ? (
          <span className="api-badge-online">
            <span className="status-dot dot-online"></span>
            API Online (Port 8000)
          </span>
        ) : (
          <span className="api-badge-offline">
            <span className="status-dot dot-offline"></span>
            API Disconnected
          </span>
        )}
      </div>
    </header>
  );
}
