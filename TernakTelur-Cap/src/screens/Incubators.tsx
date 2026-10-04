import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore, Incubator } from '../store/appStore';

import { IncubationPrograms, getStatusLabel } from '../constants/incubation';
import { ProgressRing } from '../components/ProgressRing';
import { IconPlus } from '../components/Icons';

/* ── Chicken image icon ──────────────────────────────── */
const ChickenImg = ({ size = 18 }: { size?: number }) => (
  <img
    src="/icons/telur-ayam.png"
    alt="Ayam"
    style={{ width: size, height: size, objectFit: 'contain', display: 'block' }}
  />
);

/* ── Camera View (single live feed) ──────────────────── */
function CameraView() {
  return (
    <div style={{ padding: '16px 16px 32px', display: 'flex', flexDirection: 'column', gap: 14 }}>
      {/* Status bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '10px 14px',
        background: '#0D1F0F', borderRadius: 14,
        border: '1px solid rgba(82,201,127,0.2)',
      }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#52C97F', animation: 'pulse 2s infinite' }} />
        <span style={{ fontSize: 12, fontWeight: 700, color: '#52C97F', letterSpacing: 0.8 }}>LIVE FEED</span>
        <span style={{ fontSize: 11, color: 'rgba(82,201,127,0.5)' }}>Kamera Inkubator</span>
        <span style={{
          marginLeft: 'auto', fontSize: 10, color: 'rgba(82,201,127,0.4)',
          fontFamily: 'monospace',
        }}>
          {new Date().toLocaleTimeString('id-ID')}
        </span>
      </div>

      {/* Single large camera */}
      <div style={{
        borderRadius: 18, overflow: 'hidden',
        background: '#080F09',
        border: '1.5px solid rgba(82,201,127,0.25)',
        aspectRatio: '16/10',
        position: 'relative',
        boxShadow: '0 8px 32px rgba(0,0,0,0.25)',
      }}>
        {/* Scanlines overlay */}
        <div style={{
          position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 1,
          backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,0,0,0.06) 3px, rgba(0,0,0,0.06) 4px)',
        }} />

        {/* Center placeholder icon */}
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          gap: 12, opacity: 0.22, zIndex: 2,
        }}>
          <svg width="56" height="56" viewBox="0 0 24 24" fill="none">
            <rect x="2" y="7" width="20" height="14" rx="3" stroke="#52C97F" strokeWidth="1.5"/>
            <circle cx="12" cy="14" r="3.5" stroke="#52C97F" strokeWidth="1.5"/>
            <path d="M8 7V5.5A1.5 1.5 0 0 1 9.5 4h5A1.5 1.5 0 0 1 16 5.5V7" stroke="#52C97F" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <span style={{ fontSize: 11, color: '#52C97F', letterSpacing: 1.5, fontWeight: 600 }}>
            MENUNGGU SINYAL
          </span>
        </div>

        {/* LIVE badge */}
        <div style={{
          position: 'absolute', top: 12, left: 12, zIndex: 3,
          display: 'flex', alignItems: 'center', gap: 5,
          background: 'rgba(192,57,43,0.9)', borderRadius: 6,
          padding: '4px 10px',
        }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#FF8A8A', animation: 'pulse 1.5s infinite' }} />
          <span style={{ fontSize: 10, fontWeight: 800, color: '#fff', letterSpacing: 1 }}>LIVE</span>
        </div>

        {/* Camera label */}
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0, zIndex: 3,
          background: 'linear-gradient(transparent, rgba(0,0,0,0.7))',
          padding: '16px 14px 10px',
          display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end',
        }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: '#52C97F', letterSpacing: 0.8 }}>CAM 1</span>
          <span style={{ fontSize: 10, color: 'rgba(82,201,127,0.5)' }}>Inkubator Utama</span>
        </div>

        {/* Corner brackets */}
        <div style={{ position: 'absolute', top: 10, left: 10, width: 14, height: 14, borderTop: '2px solid rgba(82,201,127,0.45)', borderLeft: '2px solid rgba(82,201,127,0.45)', borderRadius: '2px 0 0 0', zIndex: 3 }} />
        <div style={{ position: 'absolute', top: 10, right: 10, width: 14, height: 14, borderTop: '2px solid rgba(82,201,127,0.45)', borderRight: '2px solid rgba(82,201,127,0.45)', borderRadius: '0 2px 0 0', zIndex: 3 }} />
        <div style={{ position: 'absolute', bottom: 10, left: 10, width: 14, height: 14, borderBottom: '2px solid rgba(82,201,127,0.45)', borderLeft: '2px solid rgba(82,201,127,0.45)', borderRadius: '0 0 0 2px', zIndex: 3 }} />
        <div style={{ position: 'absolute', bottom: 10, right: 10, width: 14, height: 14, borderBottom: '2px solid rgba(82,201,127,0.45)', borderRight: '2px solid rgba(82,201,127,0.45)', borderRadius: '0 0 2px 0', zIndex: 3 }} />
      </div>

      {/* Info note */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '12px 16px', borderRadius: 14,
        background: 'rgba(47,107,63,0.06)',
        border: '1px solid rgba(47,107,63,0.12)',
      }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="#2F6B3F" strokeWidth="1.8"/>
          <line x1="12" y1="16" x2="12" y2="12" stroke="#2F6B3F" strokeWidth="2" strokeLinecap="round"/>
          <circle cx="12" cy="8" r="1" fill="#2F6B3F"/>
        </svg>
        <p style={{ fontSize: 12, color: '#2F6B3F', lineHeight: 1.5 }}>
          Kamera akan aktif saat terhubung ke Raspberry Pi
        </p>
      </div>
    </div>
  );
}

/* ── Main Screen ─────────────────────────────────────── */
export function Incubators() {
  const navigate = useNavigate();
  const { incubators, myDevices } = useAppStore();
  const active = incubators.filter((i) => i.isActive);
  const [view, setView] = useState<'list' | 'cam'>('list');


  return (
    <div className="screen anim-fade-in">
      {/* Header — dashboard style (light, flat) */}
      <div style={{
        paddingTop: 'env(safe-area-inset-top, 44px)',
        paddingLeft: 16, paddingRight: 16, paddingBottom: 16,
        background: '#F2F4F6',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 10 }}>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 700, color: '#1A2B1C', letterSpacing: -0.3, lineHeight: 1.2, marginBottom: 2 }}>Inkubator</h1>
            <p style={{ fontSize: 12, color: '#8A9E8C', fontWeight: 400 }}>
              {active.length > 0 ? `${active.length} inkubator aktif` : 'Belum ada inkubator aktif'}
            </p>
          </div>
          {/* View toggle — clean icon buttons */}
          <div style={{ display: 'flex', background: 'rgba(0,0,0,0.06)', borderRadius: 12, padding: 3, gap: 2 }}>
            {(['list', 'cam'] as const).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                style={{
                  width: 36, height: 36, borderRadius: 10, border: 'none', cursor: 'pointer',
                  background: view === v ? '#FFFFFF' : 'transparent',
                  boxShadow: view === v ? '0 1px 4px rgba(0,0,0,0.12)' : 'none',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'all 0.15s',
                }}
              >
                {v === 'list' ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <line x1="3" y1="6" x2="21" y2="6" stroke={view === 'list' ? '#2F6B3F' : '#9CAAA0'} strokeWidth="2" strokeLinecap="round"/>
                    <line x1="3" y1="12" x2="21" y2="12" stroke={view === 'list' ? '#2F6B3F' : '#9CAAA0'} strokeWidth="2" strokeLinecap="round"/>
                    <line x1="3" y1="18" x2="21" y2="18" stroke={view === 'list' ? '#2F6B3F' : '#9CAAA0'} strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                ) : (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <rect x="2" y="7" width="15" height="11" rx="2" stroke={view === 'cam' ? '#2F6B3F' : '#9CAAA0'} strokeWidth="1.8"/>
                    <path d="M17 10l5-3v10l-5-3V10z" stroke={view === 'cam' ? '#2F6B3F' : '#9CAAA0'} strokeWidth="1.8" strokeLinejoin="round"/>
                  </svg>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="screen-scroll flex-1" style={{ background: '#F2F4F6' }}>
        {view === 'cam' ? (
          <CameraView />
        ) : (
          <div style={{ padding: '8px 16px 32px', display: 'flex', flexDirection: 'column', gap: 12 }}>
            {active.length === 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '48px 24px', gap: 16 }}>
                <div style={{
                  width: 80, height: 80, borderRadius: 24,
                  background: 'linear-gradient(135deg,#F0FDF4,#DCFCE7)',
                  border: '2px solid rgba(47,107,63,0.15)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  boxShadow: '0 8px 24px rgba(47,107,63,0.12)',
                }}>
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none"><ellipse cx="12" cy="13" rx="6" ry="8" stroke="#2F6B3F" strokeWidth="1.8"/></svg>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <h3 style={{ fontSize: 18, fontWeight: 700, color: '#1A2B1C', marginBottom: 6 }}>Belum ada inkubator</h3>
                  <p style={{ fontSize: 14, color: '#8A9E8C', lineHeight: 1.5 }}>Mulai inkubasi pertama Anda!</p>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {active.map((inc, i) => <IncCard key={inc.id} inc={inc} index={i + 1} onClick={() => navigate('/')} />)}
              </div>
            )}

            {/* ── Tombol Aksi ── */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 4 }}>
              {/* Tambah Lemari — hubungkan ke hardware */}
              <button
                onClick={() => navigate('/incubator/add-device')}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  padding: '14px', borderRadius: 16, border: 'none', cursor: 'pointer',
                  background: 'linear-gradient(135deg,#2F6B3F,#3D8A52)',
                  color: '#FFFFFF', fontSize: 14, fontWeight: 700,
                  boxShadow: '0 4px 16px rgba(47,107,63,0.3)',
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h.01M18 14h.01M14 18h.01M18 18h.01"/></svg>
                Tambah Lemari{myDevices.length > 0 ? ` (${myDevices.length} terhubung)` : ''}
              </button>

              {/* Tambah Inkubasi — set species/telur (local) */}
              <button
                onClick={() => navigate('/incubator/egg-select')}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  padding: '12px', borderRadius: 14, border: '1.5px solid rgba(47,107,63,0.2)',
                  background: 'rgba(47,107,63,0.06)', color: '#2F6B3F',
                  fontSize: 13, fontWeight: 600, cursor: 'pointer',
                }}
              >
                <IconPlus size={16} /> Tambah Sesi Inkubasi
              </button>
            </div>

          </div>
        )}
      </div>
    </div>
  );
}

/* ── Incubator Card ──────────────────────────────────── */
function IncCard({ inc, index, onClick }: { inc: Incubator; index: number; onClick: () => void }) {
  const prog     = IncubationPrograms[inc.species];
  const progress = inc.currentDay / prog.durationDays;
  const grad     = inc.status === 'berbahaya'
    ? 'linear-gradient(135deg,#7B1E1E,#C0392B)'
    : inc.status === 'perlu_perhatian'
    ? 'linear-gradient(135deg,#6B4A1E,#D98B4A)'
    : 'linear-gradient(135deg,#1E4A2A,#2F6B3F)';

  return (
    <div className="inc-card" onClick={onClick}>
      <div style={{ background: grad, padding: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
          <div>
            {/* Number badge + name row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 2 }}>
              <span style={{
                fontSize: 10, fontWeight: 800, color: 'rgba(255,255,255,0.6)',
                background: 'rgba(255,255,255,0.12)', borderRadius: 6,
                padding: '2px 7px', letterSpacing: 0.5,
              }}>#{index}</span>
              <h3 className="t-h4 c-white" style={{ margin: 0 }}>{inc.name}</h3>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 3 }}>
              {inc.species === 'ayam' ? <ChickenImg size={18} /> : <span style={{ fontSize: 14 }}>{prog.emoji}</span>}
              <p className="t-sm" style={{ color: 'rgba(255,255,255,0.8)' }}>{prog.nameId} · {inc.totalEggs} telur</p>
            </div>
          </div>
          <span className={`badge badge-${inc.status === 'normal' ? 'normal' : inc.status === 'perlu_perhatian' ? 'warning' : 'danger'}`} style={{ fontSize: 11 }}>
            {getStatusLabel(inc.status)}
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: 40, fontWeight: 800, color: '#fff', letterSpacing: -2, lineHeight: 1 }}>{inc.currentDay}</span>
            <p className="t-sm" style={{ color: 'rgba(255,255,255,0.7)' }}>dari {prog.durationDays} hari</p>
          </div>
          <ProgressRing progress={progress} size={80} strokeWidth={7} color="#FFFFFF" trackColor="rgba(255,255,255,0.2)" label={`${Math.round(progress * 100)}%`} sublabel="selesai" />
        </div>
      </div>
      <div className="inc-stats">
        {[
          { icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M14 14.76V4.5a2.5 2.5 0 0 0-5 0v10.26A4 4 0 1 0 14 14.76Z" stroke="#5A6B5C" strokeWidth="1.8"/></svg>, v: `${inc.iotData.temperature}°C`, l: 'Suhu' },
          { icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" stroke="#5A6B5C" strokeWidth="1.8"/></svg>, v: `${inc.iotData.humidity}%`, l: 'Kelembaban' },
          { icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><rect x="3" y="4" width="18" height="18" rx="2" stroke="#5A6B5C" strokeWidth="1.8"/><line x1="16" y1="2" x2="16" y2="6" stroke="#5A6B5C" strokeWidth="1.8" strokeLinecap="round"/><line x1="8" y1="2" x2="8" y2="6" stroke="#5A6B5C" strokeWidth="1.8" strokeLinecap="round"/><line x1="3" y1="10" x2="21" y2="10" stroke="#5A6B5C" strokeWidth="1.8"/></svg>, v: `${prog.durationDays - inc.currentDay}`, l: 'Hari lagi' },
        ].map((s, i) => (
          <div key={i} className="inc-stat">
            {s.icon}
            <span style={{ fontSize: 14, fontWeight: 700, color: '#29332B' }}>{s.v}</span>
            <span className="t-sm c-text-muted">{s.l}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
