import React, { useState, useEffect } from 'react';
import { useAppStore, TurningSchedule } from '../store/appStore';
import type { DeviceName } from '../services/api';
import {
  IconFan, IconLightbulb, IconSpray, IconRotate, IconUVLight,
  IconEggFilled, IconAlertTriangle,
} from '../components/Icons';

/* ── Toggle Switch ───────────────────────────────────── */
function ToggleSwitch({ on, onChange, accent }: { on: boolean; onChange: () => void; accent: string }) {
  return (
    <button onClick={onChange} style={{
      width: 52, height: 30, borderRadius: 15, border: 'none', cursor: 'pointer',
      background: on ? accent : '#D1D5DB',
      position: 'relative', transition: 'background 0.2s', flexShrink: 0,
      boxShadow: on ? `0 0 0 3px ${accent}28` : 'none',
    }}>
      <div style={{
        position: 'absolute', top: 3, left: on ? 25 : 3,
        width: 24, height: 24, borderRadius: 12,
        background: '#FFFFFF',
        boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
        transition: 'left 0.2s',
      }} />
    </button>
  );
}

/* ── Device Row ──────────────────────────────────────── */
function DeviceRow({ icon, label, desc, on, onChange, accent = '#2F6B3F', onSettingsPress }: {
  icon: React.ReactNode; label: string; desc: string;
  on: boolean; onChange: () => void; accent?: string;
  onSettingsPress?: () => void;
}) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 14,
      background: on ? `${accent}0C` : '#FFFFFF',
      border: `1.5px solid ${on ? `${accent}35` : 'rgba(0,0,0,0.06)'}`,
      borderRadius: 18, padding: '16px 18px',
      transition: 'all 0.2s',
      boxShadow: on ? `0 4px 16px ${accent}18` : '0 1px 4px rgba(0,0,0,0.04)',
    }}>
      <div style={{
        width: 48, height: 48, borderRadius: 14, flexShrink: 0,
        background: on ? `${accent}18` : '#F5F5F5',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transition: 'all 0.2s',
      }}>
        {icon}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ fontSize: 15, fontWeight: 700, color: '#1A2B1C', marginBottom: 2 }}>{label}</p>
        <p style={{ fontSize: 12, color: '#8A9E8C', lineHeight: 1.4 }}>{desc}</p>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
        <span style={{
          fontSize: 11, fontWeight: 700,
          color: on ? accent : '#ADADAD',
          background: on ? `${accent}15` : '#F3F4F6',
          padding: '2px 10px', borderRadius: 999,
          border: `1px solid ${on ? `${accent}30` : '#E5E7EB'}`,
        }}>
          {on ? 'Aktif' : 'Mati'}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {onSettingsPress && on && (
            <button onClick={onSettingsPress} style={{
              width: 30, height: 30, borderRadius: 8, border: 'none', cursor: 'pointer',
              background: `${accent}15`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'all 0.15s',
            }}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="3" stroke={accent} strokeWidth="1.8"/>
                <path d="M12 2v2M12 20v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M2 12h2M20 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke={accent} strokeWidth="1.8" strokeLinecap="round"/>
              </svg>
            </button>
          )}
          <ToggleSwitch on={on} onChange={onChange} accent={accent} />
        </div>
      </div>
    </div>
  );
}

/* ── Section Header ──────────────────────────────────── */
function SectionHeader({ title, color = '#8A9E8C' }: { title: string; color?: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8, marginBottom: 2 }}>
      <div style={{ width: 3, height: 14, borderRadius: 2, background: color }} />
      <p style={{ fontSize: 12, fontWeight: 700, color: '#8A9E8C' }}>{title}</p>
    </div>
  );
}

/* ── Stepper ─────────────────────────────────────────── */
function Stepper({ value, min, max, step = 1, unit, onChange, variant = 'light' }: {
  value: number; min: number; max: number; step?: number; unit?: string;
  onChange: (v: number) => void; variant?: 'light' | 'dark';
}) {
  const accentColor = '#8B5CF6';
  const isDark = variant === 'dark';
  const btnBg = isDark ? 'rgba(255,255,255,0.2)' : '#F5F0FF';
  const btnBgDisabled = isDark ? 'rgba(255,255,255,0.08)' : '#F3F4F6';
  const btnColor = isDark ? '#FFFFFF' : accentColor;
  const btnColorDisabled = isDark ? 'rgba(255,255,255,0.3)' : '#ADADAD';
  const btnBorder = isDark ? '1.5px solid rgba(255,255,255,0.25)' : `1.5px solid rgba(139,92,246,0.25)`;
  const valBg = isDark ? 'rgba(255,255,255,0.15)' : '#F5F0FF';
  const valColor = isDark ? '#FFFFFF' : '#6D28D9';
  const unitColor = isDark ? 'rgba(255,255,255,0.8)' : accentColor;
  const valBorder = isDark ? '1.5px solid rgba(255,255,255,0.2)' : `1.5px solid rgba(139,92,246,0.2)`;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <button
        onClick={() => onChange(Math.max(min, value - step))}
        disabled={value <= min}
        style={{
          width: 36, height: 36, borderRadius: 10,
          border: value <= min ? btnBgDisabled : btnBorder,
          background: value <= min ? btnBgDisabled : btnBg,
          color: value <= min ? btnColorDisabled : btnColor,
          fontSize: 20, fontWeight: 700,
          cursor: value <= min ? 'not-allowed' : 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'all 0.15s',
        }}
      >−</button>
      <div style={{
        minWidth: 76, textAlign: 'center',
        background: valBg, borderRadius: 10, padding: '7px 12px',
        border: valBorder,
      }}>
        <span style={{ fontSize: 17, fontWeight: 700, color: valColor }}>{value}</span>
        {unit && <span style={{ fontSize: 12, color: unitColor, marginLeft: 3 }}>{unit}</span>}
      </div>
      <button
        onClick={() => onChange(Math.min(max, value + step))}
        disabled={value >= max}
        style={{
          width: 36, height: 36, borderRadius: 10,
          border: value >= max ? btnBgDisabled : btnBorder,
          background: value >= max ? btnBgDisabled : btnBg,
          color: value >= max ? btnColorDisabled : btnColor,
          fontSize: 20, fontWeight: 700,
          cursor: value >= max ? 'not-allowed' : 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'all 0.15s',
        }}
      >+</button>
    </div>
  );
}

/* ── Countdown ───────────────────────────────────────── */
function useCountdown(target: Date) {
  const [diff, setDiff] = useState(new Date(target).getTime() - Date.now());
  useEffect(() => {
    const t = setInterval(() => setDiff(new Date(target).getTime() - Date.now()), 1000);
    return () => clearInterval(t);
  }, [target]);
  if (diff <= 0) return 'Sekarang';
  const totalSec = Math.floor(diff / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  if (h > 0) return `${h}j ${m}m`;
  if (m > 0) return `${m}m ${s}d`;
  return `${s}d`;
}

/* ── Turning Schedule Bottom Sheet ───────────────────── */
const DAY_LABELS = ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab'];
const accent = '#8B5CF6';

function TurningScheduleSheet({ incId, sched, onClose }: {
  incId: string; sched: TurningSchedule; onClose: () => void;
}) {
  const { updateTurningSchedule } = useAppStore();
  const countdown = useCountdown(sched.nextTurningAt);

  const toggleDay = (d: number) => {
    const days = sched.activeDays.includes(d)
      ? sched.activeDays.filter(x => x !== d)
      : [...sched.activeDays, d].sort();
    if (days.length === 0) return;
    updateTurningSchedule(incId, { activeDays: days });
  };

  const fmtHour = (h: number) => `${String(h).padStart(2, '0')}:00`;

  const activeHours = Math.max(2, sched.endHour - sched.startHour);
  const timesPerDay = Math.max(1, Math.min(12, Math.round(activeHours / sched.intervalHours)));

  const handleTimesPerDayChange = (times: number) => {
    const newInterval = Math.max(2, Math.min(12, Math.round(activeHours / times)));
    updateTurningSchedule(incId, { intervalHours: newInterval });
  };

  // Interval aktual setelah rounding
  const actualInterval = Math.round(activeHours / timesPerDay);

  const dayRangeLabel = (() => {
    const days = [...sched.activeDays].sort();
    if (days.length === 7) return 'Setiap Hari';
    if (days.length === 0) return '-';
    if (days.length === 1) return DAY_LABELS[days[0]];
    const isConsec = days.every((d, i) => i === 0 || d === days[i - 1] + 1);
    if (isConsec) return `${DAY_LABELS[days[0]]}–${DAY_LABELS[days[days.length - 1]]}`;
    return days.map(d => DAY_LABELS[d]).join(', ');
  })();

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, zIndex: 100,
          background: 'rgba(0,0,0,0.45)',
          backdropFilter: 'blur(2px)',
          animation: 'fadeIn 0.2s ease both',
        }}
      />

      {/* Sheet */}
      <div style={{
        position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 101,
        background: '#FFFFFF',
        borderRadius: '24px 24px 0 0',
        boxShadow: '0 -8px 40px rgba(0,0,0,0.18)',
        animation: 'slideUp 0.32s cubic-bezier(0.16,1,0.3,1) both',
        maxHeight: '88vh',
        display: 'flex', flexDirection: 'column',
      }}>
        {/* Handle bar */}
        <div style={{ display: 'flex', justifyContent: 'center', padding: '12px 0 4px' }}>
          <div style={{ width: 40, height: 4, borderRadius: 2, background: '#E0DCF4' }} />
        </div>

        {/* Header */}
        <div style={{
          padding: '8px 20px 14px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          borderBottom: '1px solid rgba(139,92,246,0.1)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'rgba(139,92,246,0.12)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke={accent} strokeWidth="1.8"/>
                <polyline points="12,6 12,12 16,14" stroke={accent} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div>
              <p style={{ fontSize: 16, fontWeight: 700, color: '#1A2B1C' }}>Jadwal Pembalikan</p>
              <p style={{ fontSize: 11, color: '#8B5CF6' }}>Atur kapan telur dibalik otomatis</p>
            </div>
          </div>
          <button onClick={onClose} style={{
            width: 32, height: 32, borderRadius: 10, border: 'none', cursor: 'pointer',
            background: '#F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <line x1="18" y1="6" x2="6" y2="18" stroke="#6B7280" strokeWidth="2" strokeLinecap="round"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="#6B7280" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
        </div>

        {/* Scrollable content */}
        <div style={{ overflowY: 'auto', padding: '16px 20px 24px', display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Frekuensi — single stepper */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 14 }}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
                <path d="M1 4v6h6" stroke="#4A5C4C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M23 20v-6h-6" stroke="#4A5C4C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4-4.64 4.36A9 9 0 0 1 3.51 15" stroke="#4A5C4C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <p style={{ fontSize: 13, fontWeight: 700, color: '#4A5C4C' }}>Berapa kali sehari?</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <Stepper
                value={timesPerDay}
                min={1} max={12} step={1} unit="×"
                onChange={handleTimesPerDayChange}
              />
              {/* Info interval otomatis */}
              <div style={{
                flex: 1, background: '#F5F0FF', borderRadius: 12,
                border: '1.5px solid rgba(139,92,246,0.15)',
                padding: '10px 14px',
              }}>
                <p style={{ fontSize: 10, color: '#8B5CF6', fontWeight: 600, marginBottom: 2 }}>TIAP</p>
                <p style={{ fontSize: 20, fontWeight: 800, color: '#6D28D9', lineHeight: 1 }}>
                  {actualInterval} <span style={{ fontSize: 13, fontWeight: 500 }}>jam sekali</span>
                </p>
              </div>
            </div>
          </div>

          {/* Hari Aktif */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 10 }}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="4" width="18" height="18" rx="2" stroke="#4A5C4C" strokeWidth="1.8"/>
                <line x1="16" y1="2" x2="16" y2="6" stroke="#4A5C4C" strokeWidth="1.8" strokeLinecap="round"/>
                <line x1="8" y1="2" x2="8" y2="6" stroke="#4A5C4C" strokeWidth="1.8" strokeLinecap="round"/>
                <line x1="3" y1="10" x2="21" y2="10" stroke="#4A5C4C" strokeWidth="1.8"/>
              </svg>
              <p style={{ fontSize: 13, fontWeight: 700, color: '#4A5C4C' }}>Hari Aktif</p>
            </div>
            <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}>
              {DAY_LABELS.map((label, idx) => {
                const isActive = sched.activeDays.includes(idx);
                return (
                  <button
                    key={idx}
                    onClick={() => toggleDay(idx)}
                    style={{
                      width: 40, height: 40, borderRadius: 11,
                      border: `1.5px solid ${isActive ? accent : 'rgba(139,92,246,0.2)'}`,
                      background: isActive ? accent : '#FAFAFA',
                      color: isActive ? '#FFFFFF' : '#8B5CF6',
                      fontSize: 11, fontWeight: 700, cursor: 'pointer',
                      transition: 'all 0.15s',
                      boxShadow: isActive ? `0 3px 10px ${accent}40` : 'none',
                    }}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Jam Operasional */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 10 }}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="#4A5C4C" strokeWidth="1.8"/>
                <polyline points="12,6 12,12 16,14" stroke="#4A5C4C" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <p style={{ fontSize: 13, fontWeight: 700, color: '#4A5C4C' }}>Jam Operasional</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: 10, color: '#8B5CF6', marginBottom: 6, fontWeight: 600 }}>Mulai</p>
                <select
                  value={sched.startHour}
                  onChange={e => {
                    const v = +e.target.value;
                    if (v < sched.endHour) updateTurningSchedule(incId, { startHour: v });
                  }}
                  style={{
                    width: '100%', padding: '10px 12px', borderRadius: 12,
                    border: '1.5px solid rgba(139,92,246,0.25)',
                    background: '#FAFAFA', color: '#5B21B6',
                    fontSize: 15, fontWeight: 700, cursor: 'pointer',
                    textAlign: 'center', appearance: 'none',
                  }}
                >
                  {Array.from({ length: 22 }, (_, i) => i).map(h => (
                    <option key={h} value={h} disabled={h >= sched.endHour}>{fmtHour(h)}</option>
                  ))}
                </select>
              </div>

              <div style={{ color: '#C4B5FD', fontSize: 20, paddingTop: 18, fontWeight: 300 }}>→</div>

              <div style={{ flex: 1 }}>
                <p style={{ fontSize: 10, color: '#8B5CF6', marginBottom: 6, fontWeight: 600 }}>Selesai</p>
                <select
                  value={sched.endHour}
                  onChange={e => {
                    const v = +e.target.value;
                    if (v > sched.startHour) updateTurningSchedule(incId, { endHour: v });
                  }}
                  style={{
                    width: '100%', padding: '10px 12px', borderRadius: 12,
                    border: '1.5px solid rgba(139,92,246,0.25)',
                    background: '#FAFAFA', color: '#5B21B6',
                    fontSize: 15, fontWeight: 700, cursor: 'pointer',
                    textAlign: 'center', appearance: 'none',
                  }}
                >
                  {Array.from({ length: 24 }, (_, i) => i).map(h => (
                    <option key={h} value={h} disabled={h <= sched.startHour}>{fmtHour(h)}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Ringkasan */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(124,58,237,0.08), rgba(139,92,246,0.05))',
            border: '1.5px solid rgba(139,92,246,0.18)',
            borderRadius: 16, padding: '14px 16px',
            display: 'flex', flexDirection: 'column', gap: 10,
          }}>
            <div style={{ display: 'flex', gap: 10 }}>
              <div style={{
                width: 36, height: 36, borderRadius: 10, flexShrink: 0,
                background: 'rgba(139,92,246,0.12)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke={accent} strokeWidth="1.8" strokeLinejoin="round"/>
                  <polyline points="14,2 14,8 20,8" stroke={accent} strokeWidth="1.8" strokeLinejoin="round"/>
                  <line x1="16" y1="13" x2="8" y2="13" stroke={accent} strokeWidth="1.8" strokeLinecap="round"/>
                  <line x1="16" y1="17" x2="8" y2="17" stroke={accent} strokeWidth="1.8" strokeLinecap="round"/>
                </svg>
              </div>
              <div>
                <p style={{ fontSize: 12, fontWeight: 700, color: '#5B21B6' }}>Ringkasan Jadwal</p>
                <p style={{ fontSize: 12, color: '#6D28D9', marginTop: 3, lineHeight: 1.6 }}>
                  Dibalik tiap <b>{sched.intervalHours} jam</b> · <b>{timesPerDay}× sehari</b><br/>
                  {dayRangeLabel} · {fmtHour(sched.startHour)} – {fmtHour(sched.endHour)}
                </p>
              </div>
            </div>
            <div style={{
              paddingTop: 10, borderTop: '1px solid rgba(139,92,246,0.12)',
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <polygon points="5,3 19,12 5,21" fill={accent}/>
              </svg>
              <p style={{ fontSize: 12, color: '#7C3AED', fontWeight: 600 }}>
                Gilir berikutnya: <span style={{ color: accent, fontWeight: 800 }}>{countdown}</span>
              </p>
            </div>
          </div>

          {/* Tombol Simpan */}
          <button
            onClick={onClose}
            style={{
              width: '100%', padding: '14px', borderRadius: 16,
              background: `linear-gradient(135deg, #7C3AED, #8B5CF6)`,
              color: '#FFFFFF', border: 'none', cursor: 'pointer',
              fontSize: 15, fontWeight: 700,
              boxShadow: `0 6px 20px ${accent}40`,
              transition: 'transform 0.15s',
            }}
          >
            ✓ Simpan Jadwal
          </button>
        </div>
      </div>
    </>
  );
}

/* ── Main Screen ─────────────────────────────────────── */
export function DeviceControl() {
  const { incubators, updateIoTData, backendUrl, tetascoId, sendDeviceCommand, manualModes } = useAppStore();
  // Kirim ke backend jika backendUrl & tetascoId terkonfigurasi
  const hasBackend = !!backendUrl && tetascoId > 0;
  const active = incubators.filter(i => i.isActive);
  const [selectedId, setSelectedId] = useState<string>(active[0]?.id ?? '');
  const [showScheduleSheet, setShowScheduleSheet] = useState(false);

  const inc = active.find(i => i.id === selectedId) ?? active[0];
  const isManual = !!manualModes[inc?.id ?? ''];

  // Hide bottom nav when sheet is open
  useEffect(() => {
    if (showScheduleSheet) {
      document.body.setAttribute('data-sheet-open', '1');
    } else {
      document.body.removeAttribute('data-sheet-open');
    }
    return () => document.body.removeAttribute('data-sheet-open');
  }, [showScheduleSheet]);

  const inc = active.find(i => i.id === selectedId) ?? active[0];

  if (!inc) {
    return (
      <div className="screen anim-fade-in">
        <div style={{
          paddingTop: 'env(safe-area-inset-top, 44px)',
          paddingLeft: 16, paddingRight: 16, paddingBottom: 16,
          background: '#F2F4F6',
        }}>
          <div style={{ paddingTop: 10 }}>
            <h1 style={{ fontSize: 22, fontWeight: 700, color: '#1A2B1C', letterSpacing: -0.3, lineHeight: 1.2, marginBottom: 2 }}>Kontrol</h1>
            <p style={{ fontSize: 12, color: '#8A9E8C', fontWeight: 400 }}>Kontrol perangkat inkubator</p>
          </div>
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12, padding: 32 }}>
          <div style={{ width: 72, height: 72, borderRadius: 22, background: '#F0FDF4', border: '2px solid rgba(47,107,63,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <IconEggFilled size={36} color="#2F6B3F" />
          </div>
          <h3 className="t-h3 c-text">Belum Ada Inkubator</h3>
          <p className="t-body c-text-muted" style={{ textAlign: 'center' }}>Tambah inkubator terlebih dahulu untuk mengontrol perangkat.</p>
        </div>
      </div>
    );
  }

  /**
   * Mapping field IoTData → nama device sesuai API backend
   * POST /api/tetasco/{id}/devices/{device}/{on|off}
   */
  const DEVICE_MAP: Partial<Record<keyof typeof inc.iotData, DeviceName>> = {
    heaterOn:     'heater-1',
    heater2On:    'heater-2',
    fanOn:        'fan',
    humidifierOn: 'humidifier',
    motorActive:  'motor',
    uvLightOn:    'uv',
  };

  const toggle = (field: keyof typeof inc.iotData) => {
    // Jika sedang dalam mode otomatis (isManual == false), maka blok klik untuk 
    // perangkat yang dikontrol otomatis (heaterOn, heater2On, fanOn, humidifierOn)
    if (!isManual && (field === 'heaterOn' || field === 'heater2On' || field === 'fanOn' || field === 'humidifierOn')) {
      return;
    }

    const next = !inc.iotData[field];
    const device = DEVICE_MAP[field];
    if (device && hasBackend) {
      // Selalu kirim ke backend (optimistic update + real HTTP call)
      // sendDeviceCommand akan revert jika gagal
      sendDeviceCommand(inc.id, device, next);
    } else {
      // Mode simulasi / belum konfigurasi backend — update lokal saja
      updateIoTData(inc.id, { [field]: next });
    }
  };

  const handleMotorToggle = () => {
    const wasOff = !inc.iotData.motorActive;
    toggle('motorActive');
    if (wasOff) setShowScheduleSheet(true); // buka sheet saat baru diaktifkan
  };

  const sched = inc.turningSchedule;
  const _activeH = sched ? Math.max(2, sched.endHour - sched.startHour) : 14;
  const _times   = sched ? Math.max(1, Math.min(12, Math.round(_activeH / sched.intervalHours))) : 3;
  const _interval = sched ? Math.round(_activeH / _times) : 4;
  const schedDesc = sched
    ? `${_times}× sehari · tiap ${_interval} jam`
    : 'Motor putar rak telur secara otomatis';

  return (
    <div className="screen anim-fade-in">
      {/* Header */}
      <div style={{
        paddingTop: 'env(safe-area-inset-top, 44px)',
        paddingLeft: 16, paddingRight: 16, paddingBottom: 16,
        background: '#F2F4F6',
      }}>
        <div style={{ paddingTop: 10 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#1A2B1C', letterSpacing: -0.3, lineHeight: 1.2, marginBottom: 2 }}>Kontrol</h1>
          <p style={{ fontSize: 12, color: '#8A9E8C', fontWeight: 400 }}>Kontrol perangkat inkubator</p>
        </div>
        {active.length > 1 && (
          <div style={{ display: 'flex', gap: 8, marginTop: 12, overflowX: 'auto' }}>
            {active.map(i => (
              <button key={i.id} onClick={() => setSelectedId(i.id)} style={{
                padding: '6px 14px', borderRadius: 999, border: 'none', cursor: 'pointer',
                background: selectedId === i.id ? '#FFFFFF' : 'rgba(0,0,0,0.06)',
                color: selectedId === i.id ? '#2F6B3F' : '#8A9E8C',
                fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap', flexShrink: 0,
                transition: 'all 0.15s',
                boxShadow: selectedId === i.id ? '0 1px 4px rgba(0,0,0,0.12)' : 'none',
              }}>
                {i.name}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="screen-scroll flex-1" style={{ padding: '16px 16px 40px', display: 'flex', flexDirection: 'column', gap: 10 }}>

        {/* Incubator info card */}
        <div style={{
          background: '#FFFFFF', borderRadius: 18,
          border: '1px solid rgba(0,0,0,0.06)',
          padding: '14px 16px',
          display: 'flex', alignItems: 'center', gap: 12,
          boxShadow: '0 2px 10px rgba(0,0,0,0.05)',
        }}>
          <div style={{ width: 44, height: 44, borderRadius: 14, background: 'linear-gradient(135deg,#1E4A2A,#2F6B3F)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <IconEggFilled size={24} color="rgba(255,255,255,0.85)" />
          </div>
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: 14, fontWeight: 700, color: '#1A2B1C' }}>{inc.name}</p>
            <p style={{ fontSize: 12, color: '#8A9E8C' }}>Hari ke-{inc.currentDay} · {inc.iotData.temperature}°C · {inc.iotData.humidity}%</p>
          </div>
          <span style={{
            fontSize: 11, fontWeight: 700, padding: '4px 12px', borderRadius: 999,
            background: inc.status === 'normal' ? '#DCFCE7' : inc.status === 'perlu_perhatian' ? '#FEF3C7' : '#FEE2E2',
            color: inc.status === 'normal' ? '#15803D' : inc.status === 'perlu_perhatian' ? '#B45309' : '#B91C1C',
          }}>
            {inc.status === 'normal' ? 'Normal' : inc.status === 'perlu_perhatian' ? 'Perhatian' : 'Bahaya'}
          </span>
        </div>

        {/* Pemanas */}
        <SectionHeader title="Pemanas" color="#F59E0B" />
        <DeviceRow
          icon={<IconLightbulb size={24} color={inc.iotData.heaterOn ? '#F59E0B' : '#9CA3AF'} />}
          label="Lampu Pemanas 1"
          desc="Elemen pemanas utama inkubator"
          on={inc.iotData.heaterOn}
          onChange={() => toggle('heaterOn')}
          accent="#F59E0B"
        />
        <DeviceRow
          icon={<IconLightbulb size={24} color={inc.iotData.heater2On ? '#D97706' : '#9CA3AF'} />}
          label="Lampu Pemanas 2"
          desc="Elemen pemanas tambahan inkubator"
          on={inc.iotData.heater2On}
          onChange={() => toggle('heater2On')}
          accent="#D97706"
        />

        {/* Sirkulasi */}
        <SectionHeader title="Sirkulasi Udara" color="#10B981" />
        <DeviceRow
          icon={<IconFan size={24} color={inc.iotData.fanOn ? '#10B981' : '#9CA3AF'} />}
          label="Kipas"
          desc="Sirkulasi udara panas agar merata"
          on={inc.iotData.fanOn}
          onChange={() => toggle('fanOn')}
          accent="#10B981"
        />

        {/* Kelembaban */}
        <SectionHeader title="Kelembaban" color="#3B82F6" />
        <DeviceRow
          icon={<IconSpray size={24} color={inc.iotData.humidifierOn ? '#3B82F6' : '#9CA3AF'} />}
          label="Pelembab"
          desc="Mist maker untuk menjaga kelembaban"
          on={inc.iotData.humidifierOn}
          onChange={() => toggle('humidifierOn')}
          accent="#3B82F6"
        />

        {/* Pembalik Telur */}
        <SectionHeader title="Pembalik Telur" color="#8B5CF6" />
        <DeviceRow
          icon={<IconRotate size={24} color={inc.iotData.motorActive ? '#8B5CF6' : '#9CA3AF'} />}
          label="Pembalik Telur"
          desc={inc.iotData.motorActive ? schedDesc : 'Ketuk toggle untuk aktifkan & atur jadwal'}
          on={inc.iotData.motorActive}
          onChange={handleMotorToggle}
          accent="#8B5CF6"
          onSettingsPress={() => setShowScheduleSheet(true)}
        />

        {/* Sterilisasi */}
        <SectionHeader title="Sterilisasi" color="#7C3AED" />
        <DeviceRow
          icon={<IconUVLight size={24} color={inc.iotData.uvLightOn ? '#7C3AED' : '#9CA3AF'} />}
          label="Lampu UV"
          desc="Lampu ultraviolet untuk sterilisasi inkubator"
          on={inc.iotData.uvLightOn}
          onChange={() => toggle('uvLightOn')}
          accent="#7C3AED"
        />

        {/* Warning */}
        <div style={{
          background: '#FFFBEB', border: '1.5px solid rgba(245,158,11,0.3)',
          borderRadius: 16, padding: '14px 16px',
          display: 'flex', gap: 12, marginTop: 8,
          alignItems: 'flex-start',
        }}>
          <IconAlertTriangle size={18} color="#F59E0B" />
          <p style={{ fontSize: 12, color: '#92400E', lineHeight: 1.6 }}>
            Kontrol manual akan meng-override sistem otomatis. Pastikan Anda memantau kondisi inkubator secara berkala.
          </p>
        </div>
      </div>

      {/* Bottom Sheet */}
      {showScheduleSheet && sched && (
        <TurningScheduleSheet
          incId={inc.id}
          sched={sched}
          onClose={() => setShowScheduleSheet(false)}
        />
      )}
    </div>
  );
}
