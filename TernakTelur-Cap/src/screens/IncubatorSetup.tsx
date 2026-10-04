import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAppStore } from '../store/appStore';
import { EggSpecies, IncubationPrograms } from '../constants/incubation';
import {
  IconChevronLeft, IconThermometer, IconDroplet, IconRefresh, IconPlus,
  IconQuail, IconDuck, IconGoose, IconTurkey,
} from '../components/Icons';

/* ── Species icon helpers ────────────────────────────── */
const ChickenImg = ({ size = 36 }: { size?: number }) => (
  <img src="/icons/telur-ayam.png" alt="Ayam"
    style={{ width: size, height: size, objectFit: 'contain', display: 'block' }} />
);

function SpeciesIcon({ species, size = 36 }: { species: EggSpecies; size?: number }) {
  if (species === 'ayam')   return <ChickenImg size={size} />;
  if (species === 'puyuh')  return <IconQuail  size={size} />;
  if (species === 'bebek')  return <IconDuck   size={size} />;
  if (species === 'angsa')  return <IconGoose  size={size} />;
  return <IconTurkey size={size} />;
}

/* ── Minus icon ──────────────────────────────────────── */
const IconMinus = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
    <line x1="5" y1="12" x2="19" y2="12" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round" />
  </svg>
);

/* ── Star/rocket icon for CTA ────────────────────────── */
const IconRocket = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
    <path d="M12 2L13.5 8H18L14 11.5L15.5 17L12 14L8.5 17L10 11.5L6 8H10.5L12 2Z"
      fill="white" stroke="white" strokeWidth="0.5" strokeLinejoin="round" />
  </svg>
);

export function IncubatorSetup() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const species  = (params.get('species') || 'ayam') as EggSpecies;
  const prog     = IncubationPrograms[species];
  const { addIncubator } = useAppStore();

  const [name,  setName]  = useState(`Inkubator ${prog.nameId} #1`);
  const [count, setCount] = useState(50);

  const startDate  = new Date();
  const hatchDate  = new Date(startDate.getTime() + prog.durationDays * 864e5);
  const hatchStart = new Date(startDate.getTime() + prog.hatchingPhaseStartDay * 864e5);
  const fmtDate    = (d: Date) => d.toLocaleDateString('id-ID', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

  const handleStart = () => {
    addIncubator({
      name: name.trim() || `Inkubator ${prog.nameId}`,
      species, totalEggs: count, startDate, estimatedHatchDate: hatchDate, isActive: true,
      iotData: {
        temperature: prog.targetTemp, humidity: prog.targetHumidity,
        heaterOn: true, heater2On: false, fanOn: true, motorActive: false, humidifierOn: false, uvLightOn: false,
        nextTurningAt: new Date(Date.now() + prog.turningFrequencyHours * 36e5),
        lastUpdated: new Date(),
      },
    });
    navigate('/');
  };

  return (
    <div className="screen anim-fade-in">
      {/* Header — dashboard style (flat light) */}
      <div style={{
        paddingTop: 'env(safe-area-inset-top, 44px)',
        paddingLeft: 16, paddingRight: 16, paddingBottom: 16,
        background: '#F2F4F6',
      }}>
        <div style={{ paddingTop: 10 }}>
          {/* Back button */}
          <button
            onClick={() => navigate(-1)}
            style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'rgba(0,0,0,0.06)', border: '1px solid rgba(0,0,0,0.06)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer', marginBottom: 14,
            }}
          >
            <IconChevronLeft size={20} color="#4A5568" strokeWidth={2.2} />
          </button>

          {/* Title row with species icon */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 48, height: 48, borderRadius: 14,
              background: '#FFFFFF',
              border: '1px solid rgba(0,0,0,0.07)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <SpeciesIcon species={species} size={32} />
            </div>
            <div>
              <h1 style={{ fontSize: 20, fontWeight: 700, color: '#1A2B1C', letterSpacing: -0.3, lineHeight: 1.2 }}>
                Pengaturan Inkubasi
              </h1>
              <p style={{ fontSize: 13, color: '#8A9E8C', marginTop: 2 }}>
                Program {prog.nameId} — {prog.durationDays} hari
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="screen-scroll flex-1" style={{ background: '#F2F4F6' }}>
        <div style={{ padding: '8px 16px 32px', display: 'flex', flexDirection: 'column', gap: 12 }}>

          {/* Form */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label>Nama Inkubator</label>
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder={`Inkubator ${prog.nameId} #1`} />
            </div>
            <div>
              <label>Jumlah Telur</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 6 }}>
                <button className="count-btn" onClick={() => setCount(Math.max(1, count - 1))} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <IconMinus />
                </button>
                <input
                  type="number"
                  value={count}
                  onChange={(e) => setCount(Math.max(1, parseInt(e.target.value) || 1))}
                  style={{ textAlign: 'center', fontSize: 22, fontWeight: 700, border: '1.5px solid #DDD9CC', borderRadius: 12, padding: '10px', background: '#F7F3E8', flex: 1 }}
                />
                <button className="count-btn" onClick={() => setCount(count + 1)} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><line x1="12" y1="5" x2="12" y2="19" stroke="white" strokeWidth="2.5" strokeLinecap="round"/><line x1="5" y1="12" x2="19" y2="12" stroke="white" strokeWidth="2.5" strokeLinecap="round"/></svg>
                </button>
              </div>
              <p className="t-sm c-text-muted" style={{ marginTop: 5 }}>Masukkan jumlah telur yang akan diinkubasi</p>
            </div>
          </div>

          {/* Program Summary — modern premium design */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {/* Section header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 4 }}>
              <div style={{ width: 3, height: 16, borderRadius: 2, background: 'linear-gradient(to bottom,#2F6B3F,#3D8A52)' }} />
              <h3 style={{ fontSize: 13, fontWeight: 700, color: '#1A2B1C', letterSpacing: 0.3, textTransform: 'uppercase' }}>
                Parameter Program
              </h3>
            </div>

            {/* 2×2 premium metric grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>

              {/* Suhu — range */}
              <div style={{
                borderRadius: 18, padding: '16px 14px',
                background: 'linear-gradient(135deg,#FFF1F2,#FFE4E6)',
                border: '1.5px solid rgba(239,68,68,0.15)',
                boxShadow: '0 4px 16px rgba(239,68,68,0.08)',
                display: 'flex', flexDirection: 'column', gap: 8,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ width: 34, height: 34, borderRadius: 10, background: 'rgba(239,68,68,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <IconThermometer size={18} color="#EF4444" />
                  </div>
                  <span style={{ fontSize: 9, fontWeight: 700, color: '#EF4444', background: 'rgba(239,68,68,0.1)', padding: '3px 7px', borderRadius: 999, letterSpacing: 0.5 }}>SUHU</span>
                </div>
                {/* Range display */}
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                  <span style={{ fontSize: 22, fontWeight: 800, color: '#B91C1C', letterSpacing: -0.5 }}>{prog.targetTempHatching}</span>
                  <span style={{ fontSize: 11, color: '#EF4444', fontWeight: 600 }}>°C</span>
                  <span style={{ fontSize: 14, color: 'rgba(239,68,68,0.4)', fontWeight: 500, margin: '0 2px' }}>–</span>
                  <span style={{ fontSize: 22, fontWeight: 800, color: '#B91C1C', letterSpacing: -0.5 }}>{prog.targetTemp}</span>
                  <span style={{ fontSize: 11, color: '#EF4444', fontWeight: 600 }}>°C</span>
                </div>
                {/* Range bar */}
                <div style={{ height: 4, borderRadius: 999, background: 'rgba(239,68,68,0.15)', position: 'relative', overflow: 'hidden' }}>
                  <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '65%', background: 'linear-gradient(to right,#EF4444,#B91C1C)', borderRadius: 999 }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 10, color: 'rgba(239,68,68,0.6)', fontWeight: 500 }}>Menetas</span>
                  <span style={{ fontSize: 10, color: 'rgba(239,68,68,0.6)', fontWeight: 500 }}>Inkubasi</span>
                </div>
              </div>

              {/* Kelembaban — range */}
              <div style={{
                borderRadius: 18, padding: '16px 14px',
                background: 'linear-gradient(135deg,#EFF6FF,#DBEAFE)',
                border: '1.5px solid rgba(59,130,246,0.15)',
                boxShadow: '0 4px 16px rgba(59,130,246,0.08)',
                display: 'flex', flexDirection: 'column', gap: 8,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ width: 34, height: 34, borderRadius: 10, background: 'rgba(59,130,246,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <IconDroplet size={18} color="#3B82F6" />
                  </div>
                  <span style={{ fontSize: 9, fontWeight: 700, color: '#3B82F6', background: 'rgba(59,130,246,0.1)', padding: '3px 7px', borderRadius: 999, letterSpacing: 0.5 }}>LEMBAB</span>
                </div>
                {/* Range display */}
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                  <span style={{ fontSize: 22, fontWeight: 800, color: '#1D4ED8', letterSpacing: -0.5 }}>{prog.targetHumidity}</span>
                  <span style={{ fontSize: 11, color: '#3B82F6', fontWeight: 600 }}>%</span>
                  <span style={{ fontSize: 14, color: 'rgba(59,130,246,0.4)', fontWeight: 500, margin: '0 2px' }}>–</span>
                  <span style={{ fontSize: 22, fontWeight: 800, color: '#1D4ED8', letterSpacing: -0.5 }}>{prog.targetHumidityHatching}</span>
                  <span style={{ fontSize: 11, color: '#3B82F6', fontWeight: 600 }}>%</span>
                </div>
                {/* Range bar */}
                <div style={{ height: 4, borderRadius: 999, background: 'rgba(59,130,246,0.15)', position: 'relative', overflow: 'hidden' }}>
                  <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '60%', background: 'linear-gradient(to right,#3B82F6,#1D4ED8)', borderRadius: 999 }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 10, color: 'rgba(59,130,246,0.6)', fontWeight: 500 }}>Inkubasi</span>
                  <span style={{ fontSize: 10, color: 'rgba(59,130,246,0.6)', fontWeight: 500 }}>Menetas</span>
                </div>
              </div>

              {/* Balik Telur */}
              <div style={{
                borderRadius: 18, padding: '16px 14px',
                background: 'linear-gradient(135deg,#F5F3FF,#EDE9FE)',
                border: '1.5px solid rgba(139,92,246,0.15)',
                boxShadow: '0 4px 16px rgba(139,92,246,0.08)',
                display: 'flex', flexDirection: 'column', gap: 6,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ width: 34, height: 34, borderRadius: 10, background: 'rgba(139,92,246,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <IconRefresh size={18} color="#8B5CF6" />
                  </div>
                  <span style={{ fontSize: 9, fontWeight: 700, color: '#8B5CF6', background: 'rgba(139,92,246,0.1)', padding: '3px 7px', borderRadius: 999, letterSpacing: 0.5 }}>ROTASI</span>
                </div>
                <div>
                  <p style={{ fontSize: 26, fontWeight: 800, color: '#6D28D9', letterSpacing: -1, lineHeight: 1 }}>/{prog.turningFrequencyHours}<span style={{ fontSize: 13, fontWeight: 500, color: '#8B5CF6' }}>jam</span></p>
                  <p style={{ fontSize: 11, color: 'rgba(139,92,246,0.6)', marginTop: 4 }}>Balik Telur</p>
                </div>
                <div style={{ height: 1, background: 'rgba(139,92,246,0.12)' }} />
                <p style={{ fontSize: 11, color: '#8B5CF6', fontWeight: 700 }}>Otomatis</p>
              </div>

              {/* Fase Menetas */}
              <div style={{
                borderRadius: 18, padding: '16px 14px',
                background: 'linear-gradient(135deg,#F0FDF4,#DCFCE7)',
                border: '1.5px solid rgba(47,107,63,0.15)',
                boxShadow: '0 4px 16px rgba(47,107,63,0.08)',
                display: 'flex', flexDirection: 'column', gap: 6,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ width: 34, height: 34, borderRadius: 10, background: 'rgba(47,107,63,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                      <ellipse cx="12" cy="13" rx="6" ry="8" stroke="#2F6B3F" strokeWidth="1.8"/>
                      <path d="M8.5 10 Q12 7 15.5 10" stroke="#2F6B3F" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
                    </svg>
                  </div>
                  <span style={{ fontSize: 9, fontWeight: 700, color: '#2F6B3F', background: 'rgba(47,107,63,0.1)', padding: '3px 7px', borderRadius: 999, letterSpacing: 0.5 }}>HATCH</span>
                </div>
                <div>
                  <p style={{ fontSize: 26, fontWeight: 800, color: '#166534', letterSpacing: -1, lineHeight: 1 }}>H-{prog.hatchingPhaseStartDay}<span style={{ fontSize: 13, fontWeight: 500, color: '#2F6B3F' }}></span></p>
                  <p style={{ fontSize: 11, color: 'rgba(47,107,63,0.6)', marginTop: 4 }}>Fase Menetas</p>
                </div>
                <div style={{ height: 1, background: 'rgba(47,107,63,0.12)' }} />
                <p style={{ fontSize: 11, color: '#2F6B3F', fontWeight: 500 }}>s/d <span style={{ fontWeight: 700 }}>H-{prog.durationDays}</span></p>
              </div>

            </div>
          </div>

          {/* Schedule — vertical timeline */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {/* Section header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 4 }}>
              <div style={{ width: 3, height: 16, borderRadius: 2, background: 'linear-gradient(to bottom,#D97706,#F59E0B)' }} />
              <h3 style={{ fontSize: 13, fontWeight: 700, color: '#1A2B1C', letterSpacing: 0.3, textTransform: 'uppercase' }}>
                Jadwal Inkubasi
              </h3>
            </div>

            {/* Timeline card */}
            <div style={{
              background: '#FFFFFF', borderRadius: 20,
              border: '1px solid rgba(0,0,0,0.06)',
              boxShadow: '0 2px 12px rgba(0,0,0,0.05)',
              padding: '16px 16px 16px 14px',
              display: 'flex', flexDirection: 'column', gap: 0,
            }}>
              {[
                {
                  icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="4" fill="#22C55E"/></svg>,
                  dotColor: '#22C55E', dotBg: '#DCFCE7',
                  label: 'Mulai Inkubasi',
                  sub: 'Hari ini · Hari ke-1',
                  val: fmtDate(startDate),
                  accent: '#16A34A',
                  isLast: false, isHigh: false,
                },
                {
                  icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 2L13.5 8H18L14 11.5L15.5 17L12 14L8.5 17L10 11.5L6 8H10.5L12 2Z" fill="#D97706"/></svg>,
                  dotColor: '#D97706', dotBg: '#FEF3C7',
                  label: `Fase Menetas`,
                  sub: `H-${prog.hatchingPhaseStartDay} · Stop pembalikan`,
                  val: fmtDate(hatchStart),
                  accent: '#B45309',
                  isLast: false, isHigh: false,
                },
                {
                  icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><polygon points="12,2 15,8.5 22,9.5 17,14 18.5,21 12,17.5 5.5,21 7,14 2,9.5 9,8.5" fill="#7C3AED"/></svg>,
                  dotColor: '#7C3AED', dotBg: '#EDE9FE',
                  label: 'Estimasi Menetas',
                  sub: `Hari ke-${prog.durationDays} · 🎉 Panen`,
                  val: fmtDate(hatchDate),
                  accent: '#6D28D9',
                  isLast: true, isHigh: true,
                },
              ].map((step, i) => (
                <div key={i} style={{ display: 'flex', gap: 14 }}>
                  {/* Timeline track */}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                    <div style={{
                      width: 36, height: 36, borderRadius: 12,
                      background: step.dotBg,
                      border: `2px solid ${step.dotColor}30`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0,
                    }}>
                      {step.icon}
                    </div>
                    {!step.isLast && (
                      <div style={{
                        width: 2, flex: 1, minHeight: 20, margin: '4px 0',
                        background: `linear-gradient(to bottom,${step.dotColor}60,${step.dotColor}10)`,
                        borderRadius: 2,
                      }} />
                    )}
                  </div>

                  {/* Content */}
                  <div style={{
                    flex: 1, paddingBottom: step.isLast ? 0 : 20,
                    ...(step.isHigh ? {
                      background: 'linear-gradient(135deg,#F5F3FF,#EDE9FE)',
                      border: '1.5px solid rgba(124,58,237,0.15)',
                      borderRadius: 14, padding: '12px 14px',
                      marginBottom: 0,
                    } : {}),
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                      <div>
                        <p style={{ fontSize: 13, fontWeight: 700, color: step.isHigh ? step.accent : '#1A2B1C', lineHeight: 1.3 }}>
                          {step.label}
                        </p>
                        <p style={{ fontSize: 11, color: step.isHigh ? '#8B5CF6' : '#8A9E8C', marginTop: 2 }}>
                          {step.sub}
                        </p>
                      </div>
                      <p style={{
                        fontSize: 11, fontWeight: 600,
                        color: step.isHigh ? step.accent : '#4A5568',
                        textAlign: 'right', maxWidth: 120, lineHeight: 1.4,
                      }}>
                        {step.val}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>

      {/* CTA */}
      <div className="cta-footer">
        <button className="btn-primary" onClick={handleStart} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
          <IconRocket />
          Mulai Inkubasi Sekarang
        </button>
      </div>
    </div>
  );
}
