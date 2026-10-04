import { useState, useRef, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { EggSpecies, IncubationPrograms } from '../constants/incubation';
import { useAppStore } from '../store/appStore';
import {
  IconChevronLeft, IconThermometer,
  IconDroplet, IconRefresh, IconQuail, IconDuck, IconGoose, IconTurkey,
} from '../components/Icons';

/* ── Chicken image icon ──────────────────────────────── */
const ChickenImg = ({ size = 36 }: { size?: number }) => (
  <img
    src="/icons/telur-ayam.png"
    alt="Ayam"
    style={{ width: size, height: size, objectFit: 'contain', display: 'block' }}
  />
);

/* ── Species config ──────────────────────────────────── */
const SPECIES_LIST: {
  key: EggSpecies;
  Icon: ({ size }: { size?: number }) => ReactNode;
  accentColor: string;
  bgColor: string;
}[] = [
  { key: 'ayam',   Icon: ChickenImg, accentColor: '#D97706', bgColor: 'rgba(217,119,6,0.1)' },
  { key: 'puyuh',  Icon: IconQuail,  accentColor: '#92400E', bgColor: 'rgba(146,64,14,0.1)'  },
  { key: 'bebek',  Icon: IconDuck,   accentColor: '#1D4ED8', bgColor: 'rgba(29,78,216,0.1)'  },
  { key: 'angsa',  Icon: IconGoose,  accentColor: '#475569', bgColor: 'rgba(71,85,105,0.1)'  },
  { key: 'kalkun', Icon: IconTurkey, accentColor: '#92400E', bgColor: 'rgba(120,53,15,0.1)'  },
];

const CUSTOM_COLOR  = '#6366F1';
const CUSTOM_BG     = 'rgba(99,102,241,0.1)';

/* ── Custom modal ────────────────────────────────────── */
function CustomModal({ onApply, onClose }: {
  onApply: (name: string, temp: number, humid: number, days: number) => void;
  onClose: () => void;
}) {
  const [name,  setName]  = useState('');
  const [temp,  setTemp]  = useState(37.5);
  const [humid, setHumid] = useState(60);
  const [days,  setDays]  = useState(21);

  const stepT = (d: number) => setTemp(v => Math.round(Math.min(42, Math.max(30, v + d)) * 10) / 10);
  const stepH = (d: number) => setHumid(v => Math.min(99, Math.max(30, v + d)));
  const stepD = (d: number) => setDays(v  => Math.min(50, Math.max(10, v + d)));

  const Btn = (label: string, onClick: () => void, color: string) => (
    <button onClick={onClick} style={{
      width: 38, height: 38, borderRadius: 12, background: color, border: 'none',
      color: '#fff', fontSize: 20, fontWeight: 500, cursor: 'pointer',
      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
    }}>{label}</button>
  );

  const Row = ({ label, left, right, bg, border }: any) => (
    <div>
      <p style={{ fontSize: 12, fontWeight: 600, color: '#4A5568', marginBottom: 8 }}>{label}</p>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: bg, borderRadius: 14, border }}>
        {left}
        {right}
      </div>
    </div>
  );

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '16px 16px 96px',
    }} onClick={onClose}>
      <div style={{
        width: '100%', maxWidth: 420,
        background: '#FFFFFF', borderRadius: 24,
        padding: '20px 20px 24px',
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
      }} onClick={e => e.stopPropagation()}>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: '#1A2B1C', letterSpacing: -0.3 }}>Jenis Kustom</h2>
          <button onClick={onClose} style={{ width: 32, height: 32, borderRadius: 10, background: 'rgba(0,0,0,0.06)', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M18 6L6 18M6 6l12 12" stroke="#4A5568" strokeWidth="2" strokeLinecap="round"/></svg>
          </button>
        </div>
        <p style={{ fontSize: 13, color: '#8A9E8C', marginBottom: 20, lineHeight: 1.5 }}>Atur sendiri parameter untuk jenis telur lainnya.</p>

        <label style={{ fontSize: 12, fontWeight: 600, color: '#4A5568', display: 'block', marginBottom: 6 }}>Nama Jenis Telur</label>
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="Contoh: Entok, Angsa, Merpati…"
          style={{
            width: '100%', padding: '12px 14px', borderRadius: 14,
            border: '1.5px solid rgba(0,0,0,0.1)',
            background: '#F8F9FA', fontSize: 14, color: '#1A2B1C',
            outline: 'none', boxSizing: 'border-box', fontFamily: 'inherit', marginBottom: 16,
          }}
        />

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 24 }}>
          {Row({
            label: 'Target Suhu',
            bg: '#FFF1F2', border: '1px solid rgba(239,68,68,0.1)',
            left: Btn('−', () => stepT(-0.1), '#EF4444'),
            right: <><span style={{ flex: 1, textAlign: 'center', fontSize: 20, fontWeight: 800, color: '#B91C1C', letterSpacing: -0.5 }}>{temp.toFixed(1)}°C</span>{Btn('+', () => stepT(0.1), '#EF4444')}</>,
          })}
          {Row({
            label: 'Target Kelembaban',
            bg: '#EFF6FF', border: '1px solid rgba(59,130,246,0.1)',
            left: Btn('−', () => stepH(-1), '#3B82F6'),
            right: <><span style={{ flex: 1, textAlign: 'center', fontSize: 20, fontWeight: 800, color: '#1D4ED8', letterSpacing: -0.5 }}>{humid}%</span>{Btn('+', () => stepH(1), '#3B82F6')}</>,
          })}
          {Row({
            label: 'Durasi Inkubasi',
            bg: '#F0FDF4', border: '1px solid rgba(34,197,94,0.1)',
            left: Btn('−', () => stepD(-1), '#22C55E'),
            right: <><span style={{ flex: 1, textAlign: 'center', fontSize: 20, fontWeight: 800, color: '#166534', letterSpacing: -0.5 }}>{days} hari</span>{Btn('+', () => stepD(1), '#22C55E')}</>,
          })}
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={onClose} style={{ flex: 1, padding: '14px 0', borderRadius: 14, background: '#F2F4F6', border: 'none', fontSize: 14, fontWeight: 600, color: '#8A9E8C', cursor: 'pointer' }}>Batal</button>
          <button
            onClick={() => { if (name.trim()) onApply(name.trim(), temp, humid, days); }}
            disabled={!name.trim()}
            style={{
              flex: 2, padding: '14px 0', borderRadius: 14, border: 'none',
              background: name.trim() ? `linear-gradient(135deg,${CUSTOM_COLOR},${CUSTOM_COLOR}CC)` : '#E2E8F0',
              fontSize: 14, fontWeight: 700, color: name.trim() ? '#FFF' : '#A0AEC0',
              cursor: name.trim() ? 'pointer' : 'not-allowed',
              boxShadow: name.trim() ? `0 6px 18px ${CUSTOM_COLOR}44` : 'none',
            }}
          >Simpan &amp; Pilih</button>
        </div>
      </div>
    </div>
  );
}

/* ── Main Screen ─────────────────────────────────────── */
export function EggSelect() {
  const navigate = useNavigate();
  const [selected,    setSelected]    = useState<EggSpecies | null>(null);
  const [isCustomSel, setIsCustomSel] = useState(false);
  const [showCustom,  setShowCustom]  = useState(false);
  const [customLabel, setCustomLabel] = useState('Kustom');
  const [customTemp,  setCustomTemp]  = useState(37.5);
  const [customHumid, setCustomHumid] = useState(60);
  const [customDays,  setCustomDays]  = useState(21);

  const prog = selected ? IncubationPrograms[selected] : null;
  const { addIncubator } = useAppStore();

  // Form state
  const [incName, setIncName] = useState('');
  const [eggCount, setEggCount] = useState(50);

  // Scroll hint
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showHint, setShowHint] = useState(false);

  const handleScroll = () => {
    if (scrollRef.current && scrollRef.current.scrollTop > 40) setShowHint(false);
  };

  const scrollToBottom = () => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    setShowHint(false);
  };

  // Update default name when species changes
  const displayName = prog ? prog.nameId : customLabel;
  const namePlaceholder = `Inkubator ${displayName} #1`;

  const handleCustomApply = (name: string, temp: number, humid: number, days: number) => {
    setCustomLabel(name);
    setCustomTemp(temp);
    setCustomHumid(humid);
    setCustomDays(days);
    setIsCustomSel(true);
    setSelected(null);
    setShowCustom(false);
  };

  const handleSelect = (key: EggSpecies) => {
    setSelected(key);
    setIsCustomSel(false);
    setShowHint(true);
  };

  const handleStart = () => {
    const startDate  = new Date();
    const durationDays = prog ? prog.durationDays : customDays;
    const hatchDate  = new Date(startDate.getTime() + durationDays * 864e5);
    const temp       = prog ? prog.targetTemp       : customTemp;
    const humid      = prog ? prog.targetHumidity   : customHumid;
    const turning    = prog ? prog.turningFrequencyHours : 8;
    const finalName  = incName.trim() || namePlaceholder;

    addIncubator({
      name: finalName,
      species: selected ?? 'ayam',
      totalEggs: eggCount,
      startDate,
      estimatedHatchDate: hatchDate,
      isActive: true,
      iotData: {
        temperature: temp, humidity: humid,
        heaterOn: true, heater2On: false, fanOn: true, motorActive: false, humidifierOn: false, uvLightOn: false,
        nextTurningAt: new Date(Date.now() + turning * 36e5),
        lastUpdated: new Date(),
      },
    });
    navigate('/');
  };

  return (
    <div className="screen anim-fade-in" style={{ position: 'relative' }}>
      {/* Header — dashboard style */}
      <div style={{
        paddingTop: 'env(safe-area-inset-top, 44px)',
        paddingLeft: 16, paddingRight: 16, paddingBottom: 16,
        background: '#F2F4F6',
      }}>
        <div style={{ paddingTop: 10 }}>
          <button
            onClick={() => navigate(-1)}
            style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'rgba(0,0,0,0.06)', border: '1px solid rgba(0,0,0,0.06)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer', marginBottom: 12,
            }}
          >
            <IconChevronLeft size={20} color="#4A5568" strokeWidth={2.2} />
          </button>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#1A2B1C', letterSpacing: -0.3, marginBottom: 4 }}>
            Pilih Jenis Telur
          </h1>
          <p style={{ fontSize: 13, color: '#8A9E8C' }}>Setiap spesies memiliki program inkubasi berbeda</p>
        </div>
      </div>

      <div ref={scrollRef} className="screen-scroll flex-1" style={{ background: '#F2F4F6' }} onScroll={handleScroll}>
        <div style={{ padding: '8px 16px 32px' }}>

          {/* Species grid — 2 columns */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>

            {SPECIES_LIST.map(({ key, Icon, accentColor, bgColor }) => {
              const p   = IncubationPrograms[key];
              const sel = selected === key;
              return (
                <button
                  key={key}
                  onClick={() => handleSelect(key)}
                  style={{
                    borderRadius: 18, padding: '16px 12px 14px',
                    background: sel ? '#FFFFFF' : '#FFFFFF',
                    border: `2px solid ${sel ? accentColor : 'rgba(0,0,0,0.06)'}`,
                    boxShadow: sel ? `0 8px 24px ${accentColor}28` : '0 2px 8px rgba(0,0,0,0.04)',
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
                    cursor: 'pointer', position: 'relative',
                    transform: sel ? 'translateY(-2px)' : 'none',
                    transition: 'all 0.2s cubic-bezier(0.34,1.56,0.64,1)',
                    fontFamily: 'inherit',
                  }}
                >
                  {/* Check badge */}
                  {sel && (
                    <div style={{
                      position: 'absolute', top: 8, right: 8,
                      width: 18, height: 18, borderRadius: '50%',
                      background: accentColor,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none">
                        <polyline points="20,6 9,17 4,12" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                  )}

                  {/* Icon box */}
                  <div style={{
                    width: 60, height: 60, borderRadius: 16,
                    background: sel ? bgColor : 'rgba(0,0,0,0.04)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'background 0.2s',
                  }}>
                    <Icon size={36} />
                  </div>

                  <p style={{ fontSize: 15, fontWeight: 700, color: sel ? accentColor : '#1A2B1C' }}>
                    {p.nameId}
                  </p>
                  <p style={{ fontSize: 12, color: '#8A9E8C', marginTop: -4 }}>{p.durationDays} hari</p>
                  <span style={{
                    fontSize: 11, fontWeight: 600, letterSpacing: 0.2,
                    color: sel ? '#FFFFFF' : accentColor,
                    background: sel ? accentColor : bgColor,
                    padding: '3px 10px', borderRadius: 999,
                  }}>
                    {p.targetTemp}°C
                  </span>
                </button>
              );
            })}

            {/* Custom card */}
            <button
              onClick={() => setShowCustom(true)}
              style={{
                borderRadius: 18, padding: '16px 12px 14px',
                background: '#FFFFFF',
                border: `2px solid ${isCustomSel ? CUSTOM_COLOR : 'rgba(0,0,0,0.06)'}`,
                boxShadow: isCustomSel ? `0 8px 24px ${CUSTOM_COLOR}28` : '0 2px 8px rgba(0,0,0,0.04)',
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
                cursor: 'pointer', position: 'relative',
                transform: isCustomSel ? 'translateY(-2px)' : 'none',
                transition: 'all 0.2s cubic-bezier(0.34,1.56,0.64,1)',
                fontFamily: 'inherit',
              }}
            >
              {isCustomSel && (
                <div style={{
                  position: 'absolute', top: 8, right: 8,
                  width: 18, height: 18, borderRadius: '50%',
                  background: CUSTOM_COLOR,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none">
                    <polyline points="20,6 9,17 4,12" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
              )}
              <div style={{
                width: 60, height: 60, borderRadius: 16,
                background: isCustomSel ? CUSTOM_BG : 'rgba(0,0,0,0.04)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                  <path d="M12 5v14M5 12h14" stroke={isCustomSel ? CUSTOM_COLOR : '#9CAAA0'} strokeWidth="2.5" strokeLinecap="round"/>
                </svg>
              </div>
              <p style={{ fontSize: 15, fontWeight: 700, color: isCustomSel ? CUSTOM_COLOR : '#1A2B1C' }}>
                {isCustomSel ? customLabel : 'Kustom'}
              </p>
              <p style={{ fontSize: 12, color: '#8A9E8C', marginTop: -4 }}>
                {isCustomSel ? `${customDays} hari` : 'Atur sendiri'}
              </p>
              <span style={{
                fontSize: 11, fontWeight: 600, letterSpacing: 0.2,
                color: isCustomSel ? '#FFFFFF' : CUSTOM_COLOR,
                background: isCustomSel ? CUSTOM_COLOR : CUSTOM_BG,
                padding: '3px 10px', borderRadius: 999,
              }}>
                {isCustomSel ? `${customTemp}°C` : '+ Buat'}
              </span>
            </button>

          </div>

          {/* Info panel — species selected */}
          {prog && (
            <div style={{
              background: '#FFFFFF', borderRadius: 20,
              border: '1px solid rgba(0,0,0,0.06)',
              boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
              overflow: 'hidden',
            }}>
              <div style={{ padding: '16px 16px 0', display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 14,
                  background: SPECIES_LIST.find(s => s.key === selected)?.bgColor ?? '#EAF3EC',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {(() => { const s = SPECIES_LIST.find(x => x.key === selected); return s ? <s.Icon size={30} /> : null; })()}
                </div>
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: '#1A2B1C' }}>{prog.nameId}</h3>
                  <p style={{ fontSize: 12, color: '#8A9E8C' }}>Program inkubasi standar</p>
                </div>
              </div>
              <div style={{ padding: '12px 16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                {[
                  { icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><rect x="3" y="4" width="18" height="18" rx="2" stroke="#2F6B3F" strokeWidth="1.8"/><line x1="16" y1="2" x2="16" y2="6" stroke="#2F6B3F" strokeWidth="1.8" strokeLinecap="round"/><line x1="8" y1="2" x2="8" y2="6" stroke="#2F6B3F" strokeWidth="1.8" strokeLinecap="round"/><line x1="3" y1="10" x2="21" y2="10" stroke="#2F6B3F" strokeWidth="1.8"/></svg>, label: 'Durasi', val: `${prog.durationDays} hari` },
                  { icon: <IconThermometer size={16} color="#EF4444" />, label: 'Suhu', val: `${prog.targetTemp}°C` },
                  { icon: <IconDroplet size={16} color="#3B82F6" />, label: 'Kelembaban', val: `${prog.targetHumidity}%` },
                  { icon: <IconRefresh size={16} color="#8B5CF6" />, label: 'Balik Telur', val: `/${prog.turningFrequencyHours} jam` },
                ].map((s) => (
                  <div key={s.label} style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '10px 12px', borderRadius: 12,
                    background: '#F8F9FA', border: '1px solid rgba(0,0,0,0.05)',
                  }}>
                    {s.icon}
                    <div>
                      <p style={{ fontSize: 13, fontWeight: 700, color: '#1A2B1C' }}>{s.val}</p>
                      <p style={{ fontSize: 11, color: '#8A9E8C' }}>{s.label}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ padding: '0 16px 16px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                <p style={{ fontSize: 12, fontWeight: 600, color: '#4A5568', marginBottom: 2 }}>Tips Penting:</p>
                {prog.tips.map((tip, i) => (
                  <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <div style={{ width: 5, height: 5, borderRadius: '50%', background: '#2F6B3F', marginTop: 6, flexShrink: 0 }} />
                    <p style={{ fontSize: 12, color: '#5A6B5C', lineHeight: 1.5 }}>{tip}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Info panel — custom selected */}
          {isCustomSel && (
            <div style={{
              background: '#FFFFFF', borderRadius: 20,
              border: `1.5px solid ${CUSTOM_COLOR}30`,
              boxShadow: `0 4px 20px ${CUSTOM_COLOR}14`,
              overflow: 'hidden',
            }}>
              <div style={{ padding: '16px 16px 0', display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 48, height: 48, borderRadius: 14, background: CUSTOM_BG, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="3" stroke={CUSTOM_COLOR} strokeWidth="2"/>
                    <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" stroke={CUSTOM_COLOR} strokeWidth="1.8"/>
                  </svg>
                </div>
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: '#1A2B1C' }}>{customLabel}</h3>
                  <p style={{ fontSize: 12, color: '#8A9E8C' }}>Program inkubasi kustom</p>
                </div>
                <button onClick={() => setShowCustom(true)} style={{ marginLeft: 'auto', fontSize: 11, fontWeight: 600, color: CUSTOM_COLOR, background: CUSTOM_BG, border: 'none', borderRadius: 8, padding: '6px 10px', cursor: 'pointer' }}>Edit</button>
              </div>
              <div style={{ padding: '12px 16px 16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                {[
                  { icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><rect x="3" y="4" width="18" height="18" rx="2" stroke="#2F6B3F" strokeWidth="1.8"/><line x1="16" y1="2" x2="16" y2="6" stroke="#2F6B3F" strokeWidth="1.8" strokeLinecap="round"/><line x1="8" y1="2" x2="8" y2="6" stroke="#2F6B3F" strokeWidth="1.8" strokeLinecap="round"/><line x1="3" y1="10" x2="21" y2="10" stroke="#2F6B3F" strokeWidth="1.8"/></svg>, label: 'Durasi', val: `${customDays} hari` },
                  { icon: <IconThermometer size={16} color="#EF4444" />, label: 'Suhu', val: `${customTemp.toFixed(1)}°C` },
                  { icon: <IconDroplet size={16} color="#3B82F6" />, label: 'Kelembaban', val: `${customHumid}%` },
                ].map((s) => (
                  <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', borderRadius: 12, background: '#F8F9FA' }}>
                    {s.icon}
                    <div>
                      <p style={{ fontSize: 13, fontWeight: 700, color: '#1A2B1C' }}>{s.val}</p>
                      <p style={{ fontSize: 11, color: '#8A9E8C' }}>{s.label}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}


          {/* ── Form: Nama + Jumlah Telur (shows when any species selected) */}
          {(selected || isCustomSel) && (
            <div style={{
              background: '#FFFFFF', borderRadius: 20,
              border: '1px solid rgba(0,0,0,0.06)',
              boxShadow: '0 2px 12px rgba(0,0,0,0.05)',
              padding: '16px',
              display: 'flex', flexDirection: 'column', gap: 14,
              marginTop: 4,
            }}>
              {/* Nama */}
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#4A5568', display: 'block', marginBottom: 7 }}>Nama Inkubator</label>
                <input
                  value={incName}
                  onChange={e => setIncName(e.target.value)}
                  placeholder={namePlaceholder}
                  style={{
                    width: '100%', padding: '12px 14px', borderRadius: 14,
                    border: '1.5px solid rgba(0,0,0,0.1)',
                    background: '#F8F9FA', fontSize: 14, color: '#1A2B1C',
                    outline: 'none', boxSizing: 'border-box', fontFamily: 'inherit',
                    transition: 'border-color 0.2s',
                  }}
                />
              </div>
              {/* Jumlah Telur */}
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#4A5568', display: 'block', marginBottom: 7 }}>Jumlah Telur</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <button
                    onClick={() => setEggCount(Math.max(1, eggCount - 1))}
                    style={{
                      width: 44, height: 44, borderRadius: 14, flexShrink: 0,
                      background: 'linear-gradient(135deg,#2F6B3F,#3D8A52)',
                      border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                      boxShadow: '0 4px 12px rgba(47,107,63,0.3)',
                    }}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><line x1="5" y1="12" x2="19" y2="12" stroke="white" strokeWidth="2.5" strokeLinecap="round"/></svg>
                  </button>
                  <input
                    type="number"
                    value={eggCount}
                    onChange={e => setEggCount(Math.max(1, parseInt(e.target.value) || 1))}
                    style={{
                      flex: 1, textAlign: 'center', fontSize: 22, fontWeight: 800,
                      border: '1.5px solid rgba(0,0,0,0.1)', borderRadius: 14,
                      padding: '10px', background: '#F8F9FA', color: '#1A2B1C', fontFamily: 'inherit',
                    }}
                  />
                  <button
                    onClick={() => setEggCount(eggCount + 1)}
                    style={{
                      width: 44, height: 44, borderRadius: 14, flexShrink: 0,
                      background: 'linear-gradient(135deg,#2F6B3F,#3D8A52)',
                      border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                      boxShadow: '0 4px 12px rgba(47,107,63,0.3)',
                    }}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><line x1="12" y1="5" x2="12" y2="19" stroke="white" strokeWidth="2.5" strokeLinecap="round"/><line x1="5" y1="12" x2="19" y2="12" stroke="white" strokeWidth="2.5" strokeLinecap="round"/></svg>
                  </button>
                </div>
                <p style={{ fontSize: 11, color: '#8A9E8C', marginTop: 6 }}>Masukkan jumlah telur yang akan diinkubasi</p>
              </div>
            </div>
          )}

          {/* CTA button — inside scroll, not fixed */}
          {(selected || isCustomSel) && (
            <button
              className="btn-primary"
              onClick={handleStart}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 8 }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 2L13.5 8H18L14 11.5L15.5 17L12 14L8.5 17L10 11.5L6 8H10.5L12 2Z" fill="white" stroke="white" strokeWidth="0.5" strokeLinejoin="round"/></svg>
              Mulai Inkubasi Sekarang
            </button>
          )}

        </div>
      </div>

      {/* Custom modal */}
      {showCustom && (
        <CustomModal
          onApply={handleCustomApply}
          onClose={() => setShowCustom(false)}
        />
      )}

      {/* Floating scroll hint — centered circle with arrow */}
      {showHint && (
        <button
          onClick={scrollToBottom}
          style={{
            position: 'absolute',
            bottom: 28, left: 0, right: 0,
            margin: '0 auto',
            width: 44, height: 44, borderRadius: '50%',
            background: 'rgba(47,107,63,0.88)',
            backdropFilter: 'blur(8px)',
            border: '1.5px solid rgba(255,255,255,0.2)',
            boxShadow: '0 4px 20px rgba(47,107,63,0.4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer',
            animation: 'scrollBounce 1.6s ease-in-out infinite',
            zIndex: 10,
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <polyline points="6,9 12,15 18,9" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      )}
    </div>
  );
}
