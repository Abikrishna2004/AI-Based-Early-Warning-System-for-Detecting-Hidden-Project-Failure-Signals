import React, { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Sliders,
  Activity,
  FileText,
  FileSearch,
  Sparkles,
  FlaskConical,
  Menu,
  X
} from 'lucide-react';

import { API_BASE_URL } from '../config';

export default function Navbar() {
  const [apiHealth, setApiHealth] = useState('checking');
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    fetch(`${API_BASE_URL}/`)
      .then(res => res.json())
      .then(() => setApiHealth('online'))
      .catch(() => setApiHealth('offline'));
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [location]);

  const navGroups = [
    {
      groupName: 'Monitor & Analyze',
      links: [
        { 
          path: '/', 
          label: 'Dashboard', 
          Icon: LayoutDashboard,
          activeClass: 'bg-blue-500/15 text-blue-300 border-blue-500/40 shadow-[0_0_12px_rgba(59,130,246,0.3)]',
          iconColor: 'text-blue-400'
        },
        { 
          path: '/input', 
          label: 'Project Input', 
          Icon: Sliders,
          activeClass: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/40 shadow-[0_0_12px_rgba(6,182,212,0.3)]',
          iconColor: 'text-cyan-400'
        },
        { 
          path: '/results', 
          label: 'Prediction Results', 
          Icon: Activity,
          activeClass: 'bg-purple-500/15 text-purple-300 border-purple-500/40 shadow-[0_0_12px_rgba(168,85,247,0.3)]',
          iconColor: 'text-purple-400'
        },
      ]
    },
    {
      groupName: 'Knowledge & AI',
      links: [
        { 
          path: '/documents', 
          label: 'RAG Knowledge', 
          Icon: FileText,
          activeClass: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40 shadow-[0_0_12px_rgba(16,185,129,0.3)]',
          iconColor: 'text-emerald-400'
        },
        { 
          path: '/document-details', 
          label: 'Document Insights', 
          Icon: FileSearch,
          activeClass: 'bg-amber-500/15 text-amber-300 border-amber-500/40 shadow-[0_0_12px_rgba(245,158,11,0.3)]',
          iconColor: 'text-amber-400'
        },
        { 
          path: '/assistant', 
          label: 'Avira Assistant', 
          Icon: Sparkles,
          activeClass: 'bg-rose-500/15 text-rose-300 border-rose-500/40 shadow-[0_0_12px_rgba(244,63,94,0.3)]',
          iconColor: 'text-rose-400'
        },
      ]
    },
    {
      groupName: 'Simulate',
      links: [
        { 
          path: '/simulator', 
          label: 'What-If Simulator', 
          Icon: FlaskConical,
          activeClass: 'bg-violet-500/15 text-violet-300 border-violet-500/40 shadow-[0_0_12px_rgba(139,92,246,0.3)]',
          iconColor: 'text-violet-400'
        },
      ]
    }
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-[68px] bg-[#070B14]/90 backdrop-blur-md border-b border-[#1E293B] shadow-2xl">
      <div className="max-w-[1280px] h-full mx-auto px-6 flex items-center justify-between">
        
        {/* Left Section: Logo & App Title */}
        <div className="flex items-center gap-8 flex-shrink-0">
          <NavLink to="/" className="flex items-center gap-3 no-underline">
            <div className="w-10 h-10 rounded-xl overflow-hidden border border-indigo-500/40 bg-[#0F172A] flex items-center justify-center shadow-[0_0_18px_rgba(99,102,241,0.3)]">
              <img src="/logo.jpg" alt="CompilePulse Logo" className="w-full h-full object-cover" />
            </div>
            <div className="flex flex-col">
              <span className="text-[17px] font-bold text-white tracking-tight leading-none font-heading">
                Compile<span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-indigo-400">Pulse</span>
              </span>
              <span className="text-[11px] text-cyan-400 font-medium tracking-tight mt-0.5">
                AI Project Intelligence
              </span>
            </div>
          </NavLink>

          {/* Desktop Navigation Links with Individual Vibrant Colors */}
          <nav className="hidden xl:flex items-center">
            {navGroups.map((group, groupIdx) => (
              <React.Fragment key={groupIdx}>
                {groupIdx > 0 && (
                  <div className="w-[1px] h-[20px] bg-[#1E293B] mx-3 flex-shrink-0"></div>
                )}

                <div className="flex items-center gap-1">
                  {group.links.map(({ path, label, Icon, activeClass, iconColor }) => (
                    <NavLink
                      key={path}
                      to={path}
                      className={({ isActive }) =>
                        `h-[36px] px-3.5 rounded-lg flex items-center gap-2 text-[13px] transition-all duration-150 no-underline whitespace-nowrap border ${
                          isActive
                            ? `${activeClass} font-semibold`
                            : 'bg-transparent border-transparent text-slate-400 hover:text-white hover:bg-[#1E293B]/60 font-medium'
                        }`
                      }
                    >
                      <Icon className={`w-4 h-4 flex-shrink-0 ${iconColor}`} />
                      <span className="leading-none">{label}</span>
                    </NavLink>
                  ))}
                </div>
              </React.Fragment>
            ))}
          </nav>
        </div>

        {/* Right Section: API Status Pill */}
        <div className="flex items-center gap-3 flex-shrink-0">
          {apiHealth === 'online' ? (
            <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold flex items-center gap-2 shadow-[0_0_12px_rgba(16,185,129,0.2)]">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>API Online</span>
            </span>
          ) : (
            <span className="px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold flex items-center gap-2 shadow-[0_0_12px_rgba(244,63,94,0.2)]">
              <span className="w-2 h-2 rounded-full bg-rose-400"></span>
              <span>API Offline</span>
            </span>
          )}

          {/* Mobile Hamburger Button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="xl:hidden p-2 rounded-lg bg-[#151D30] border border-[#1E2842] text-slate-200 hover:text-white focus:outline-none"
            aria-label="Toggle navigation menu"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="xl:hidden bg-[#070B14] border-b border-[#1E293B] px-6 py-4 space-y-4 shadow-2xl">
          {navGroups.map((group, groupIdx) => (
            <div key={groupIdx} className="space-y-2">
              {groupIdx > 0 && <div className="h-[1px] bg-[#1E293B] my-2"></div>}
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
                {group.groupName}
              </span>
              <div className="flex flex-col gap-1">
                {group.links.map(({ path, label, Icon, activeClass, iconColor }) => (
                  <NavLink
                    key={path}
                    to={path}
                    className={({ isActive }) =>
                      `h-[38px] px-3.5 rounded-lg flex items-center gap-3 text-xs font-medium no-underline border ${
                        isActive
                          ? `${activeClass} font-semibold`
                          : 'bg-[#0F172A] border-[#1E293B] text-slate-300 hover:text-white'
                      }`
                    }
                  >
                    <Icon className={`w-4 h-4 flex-shrink-0 ${iconColor}`} />
                    <span>{label}</span>
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </header>
  );
}

