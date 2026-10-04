import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';

/* ── Tab Icons ────────────────────────────────────────── */

const IconHome = ({ active }: { active: boolean }) => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
    <path
      d="M3 10.5L12 3L21 10.5V20C21 20.55 20.55 21 20 21H15V15H9V21H4C3.45 21 3 20.55 3 20V10.5Z"
      fill={active ? '#2F6B3F' : 'none'}
      stroke={active ? '#2F6B3F' : '#9CAAA0'}
      strokeWidth={active ? 0 : 1.8}
      strokeLinejoin="round"
    />
    {active && (
      <path d="M9 21V15H15V21" fill="#1A4F2A" />
    )}
    {!active && (
      <path d="M9 21V15H15V21" stroke="#9CAAA0" strokeWidth="1.8" strokeLinejoin="round" />
    )}
  </svg>
);

const IconIncubator = ({ active }: { active: boolean }) => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
    <ellipse
      cx="12" cy="13" rx="7" ry="9"
      fill={active ? '#3B82F6' : 'none'}
      stroke={active ? '#3B82F6' : '#9CAAA0'}
      strokeWidth={active ? 0 : 1.8}
    />
    {active && (
      <>
        <ellipse cx="12" cy="13" rx="4" ry="5" fill="#1D4ED8" opacity="0.5" />
        <path d="M9 11 Q12 8 15 11" stroke="white" strokeWidth="1.3" strokeLinecap="round" fill="none" opacity="0.7" />
      </>
    )}
    {!active && (
      <path d="M8.5 10 Q12 7.5 15.5 10" stroke="#9CAAA0" strokeWidth="1.5" strokeLinecap="round" fill="none" />
    )}
  </svg>
);

const IconControl = ({ active }: { active: boolean }) => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
    <line x1="3" y1="6"  x2="21" y2="6"  stroke={active ? '#F59E0B' : '#9CAAA0'} strokeWidth="2" strokeLinecap="round"/>
    <circle cx="8"  cy="6"  r="3" fill={active ? '#F59E0B' : '#9CAAA0'} />
    <line x1="3" y1="12" x2="21" y2="12" stroke={active ? '#F59E0B' : '#9CAAA0'} strokeWidth="2" strokeLinecap="round"/>
    <circle cx="16" cy="12" r="3" fill={active ? '#F59E0B' : '#9CAAA0'} />
    <line x1="3" y1="18" x2="21" y2="18" stroke={active ? '#F59E0B' : '#9CAAA0'} strokeWidth="2" strokeLinecap="round"/>
    <circle cx="11" cy="18" r="3" fill={active ? '#F59E0B' : '#9CAAA0'} />
  </svg>
);

const IconProfile = ({ active }: { active: boolean }) => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
    <circle
      cx="12" cy="8" r="4"
      fill={active ? '#8B5CF6' : 'none'}
      stroke={active ? '#8B5CF6' : '#9CAAA0'}
      strokeWidth={active ? 0 : 1.8}
    />
    <path
      d="M4 20C4 17.24 7.58 15 12 15C16.42 15 20 17.24 20 20"
      stroke={active ? '#8B5CF6' : '#9CAAA0'}
      strokeWidth="1.8"
      strokeLinecap="round"
      fill="none"
    />
    {active && (
      <path d="M4 20C4 17.24 7.58 15 12 15C16.42 15 20 17.24 20 20" stroke="#8B5CF6" strokeWidth="2" strokeLinecap="round" />
    )}
  </svg>
);

/* ── Tab config ──────────────────────────────────────── */
const tabs = [
  {
    path: '/',
    label: 'Beranda',
    Icon: IconHome,
    color: '#2F6B3F',
    bg: 'rgba(47,107,63,0.12)',
  },
  {
    path: '/incubators',
    label: 'Inkubator',
    Icon: IconIncubator,
    color: '#3B82F6',
    bg: 'rgba(59,130,246,0.12)',
  },
  {
    path: '/control',
    label: 'Kontrol',
    Icon: IconControl,
    color: '#F59E0B',
    bg: 'rgba(245,158,11,0.12)',
  },
  {
    path: '/profile',
    label: 'Profil',
    Icon: IconProfile,
    color: '#8B5CF6',
    bg: 'rgba(139,92,246,0.12)',
  },
];

/* ── Layout ──────────────────────────────────────────── */
export function TabLayout() {
  const navigate  = useNavigate();
  const location  = useLocation();

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
      {/* Page content */}
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <Outlet />
      </div>

      {/* Floating bottom nav */}
      <div className="tab-bar-wrapper">
        <nav className="tab-bar">
          {tabs.map((tab) => {
            const active = location.pathname === tab.path;
            return (
              <button
                key={tab.path}
                className={`tab-item ${active ? 'active' : ''}`}
                onClick={() => navigate(tab.path)}
              >
                {/* Colored bg bubble when active */}
                <div
                  className="tab-item-bg"
                  style={{ background: active ? tab.bg : 'transparent' }}
                />

                {/* Icon with colored wrap */}
                <div
                  className="tab-icon-wrap"
                  style={{
                    background: active ? tab.bg : 'transparent',
                    boxShadow: active ? `0 2px 8px ${tab.color}28` : 'none',
                  }}
                >
                  <tab.Icon active={active} />
                </div>

                {/* Label */}
                <span
                  className="tab-label"
                  style={{ color: active ? tab.color : '#9CAAA0', fontWeight: active ? 650 : 500 }}
                >
                  {tab.label}
                </span>
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
