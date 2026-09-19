import React, { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  ShieldAlert,
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

  // Close mobile menu on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [location]);

  const navGroups = [
    {
      groupName: 'Monitor & Analyze',
      links: [
        { path: '/', label: 'Dashboard', Icon: LayoutDashboard },
        { path: '/input', label: 'Project Input', Icon: Sliders },
        { path: '/results', label: 'Prediction Results', Icon: Activity },
      ]
    },
    {
      groupName: 'Knowledge & AI',
      links: [
        { path: '/documents', label: 'Ingest Document', Icon: FileText },
        { path: '/document-details', label: 'Document Insights', Icon: FileSearch },
        { path: '/assistant', label: 'Avira Assistant', Icon: Sparkles },
      ]
    },
    {
      groupName: 'Simulate',
      links: [
        { path: '/simulator', label: 'What-If Simulator', Icon: FlaskConical },
      ]
    }
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-[70px] bg-[#0B1220] border-b border-[#232E47]">
      <div className="max-w-[1400px] h-full mx-auto px-6 flex items-center justify-between">
        
        {/* Left Section: Logo, App Name & Version Badge */}
        <div className="flex items-center gap-8 flex-shrink-0">
          <NavLink to="/" className="flex items-center gap-3 no-underline">
            <div className="w-9 h-9 rounded-[6px] bg-[#FF8A3D] flex items-center justify-center text-[#0B1220]">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div className="flex items-center gap-2.5">
              <span className="font-heading text-[20px] font-bold text-[#E8ECF4] tracking-tight leading-none">
                Project Sentinel
              </span>
              <span className="font-sans text-[12px] font-medium px-2 py-0.5 rounded-[6px] bg-[#131B2E] text-[#8B95AC] border border-[#232E47]">
                v1.5.0
              </span>
            </div>
          </NavLink>

          {/* Desktop Center Navigation (Visible on xl screens) */}
          <nav className="hidden xl:flex items-center">
            {navGroups.map((group, groupIdx) => (
              <React.Fragment key={groupIdx}>
                {groupIdx > 0 && (
                  <div className="w-[1px] h-[24px] bg-[#232E47] mx-[16px] flex-shrink-0"></div>
                )}

                <div className="flex items-center gap-[6px]">
                  {group.links.map(({ path, label, Icon }) => (
                    <NavLink
                      key={path}
                      to={path}
                      className={({ isActive }) =>
                        `h-[40px] px-[14px] rounded-full flex items-center gap-[6px] text-[13px] transition-colors duration-150 no-underline whitespace-nowrap ${
                          isActive
                            ? 'bg-[#FF8A3D] text-white font-semibold shadow-[0_0_12px_rgba(255,138,61,0.35)]'
                            : 'bg-transparent text-[#8B95AC] hover:text-[#E8ECF4] font-medium'
                        }`
                      }
                    >
                      <Icon className="w-4 h-4 flex-shrink-0" />
                      <span className="leading-none">{label}</span>
                    </NavLink>
                  ))}
                </div>
              </React.Fragment>
            ))}
          </nav>
        </div>

        {/* Right Section: API Status Indicator & Mobile Hamburger Toggle */}
        <div className="flex items-center gap-4 ml-6 flex-shrink-0">
          {/* API Status Pill */}
          {apiHealth === 'online' ? (
            <span className="px-3.5 py-1.5 rounded-full bg-[#131B2E] border border-[#232E47] text-[#34D399] text-[12px] font-medium flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#34D399] animate-pulse"></span>
              <span>API Online</span>
            </span>
          ) : (
            <span className="px-3.5 py-1.5 rounded-full bg-[#131B2E] border border-[#232E47] text-[#F5544D] text-[12px] font-medium flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#F5544D]"></span>
              <span>API Offline</span>
            </span>
          )}

          {/* Hamburger Menu Icon Button (Visible on screens < xl) */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="xl:hidden p-2 rounded-[6px] bg-[#131B2E] border border-[#232E47] text-[#E8ECF4] hover:text-[#FF8A3D] focus:outline-none"
            aria-label="Toggle navigation menu"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

      </div>

      {/* Mobile / Narrow Screen Vertical Dropdown Drawer */}
      {mobileOpen && (
        <div className="xl:hidden bg-[#0B1220] border-b border-[#232E47] px-6 py-4 space-y-4 shadow-xl">
          {navGroups.map((group, groupIdx) => (
            <div key={groupIdx} className="space-y-2">
              {groupIdx > 0 && <div className="h-[1px] bg-[#232E47] my-3"></div>}
              <span className="text-[10px] font-mono uppercase tracking-wider text-[#8B95AC] block">
                {group.groupName}
              </span>
              <div className="flex flex-col gap-1.5">
                {group.links.map(({ path, label, Icon }) => (
                  <NavLink
                    key={path}
                    to={path}
                    className={({ isActive }) =>
                      `h-[40px] px-4 rounded-[6px] flex items-center gap-3 text-xs font-medium no-underline ${
                        isActive
                          ? 'bg-[#FF8A3D] text-white font-semibold'
                          : 'bg-[#131B2E] text-[#8B95AC] hover:text-[#E8ECF4]'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 flex-shrink-0" />
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
