import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore, Incubator } from '../store/appStore';
import { IncubationPrograms } from '../constants/incubation';
import {
  IconBell, IconMapPin, IconPlus, IconArrowRight,
  IconThermometer, IconDroplet, IconQuail, IconDuck,
  IconEggFilled, IconCalendar,
} from '../components/Icons';

/* ── Chicken image component ─────────────────────────── */
const ChickenImg = ({ size = 36 }: { size?: number }) => (
  <img
    src="/icons/telur-ayam.png"
    alt="Ayam"
    style={{ width: size, height: size, objectFit: 'contain', display: 'block' }}
  />
);

/* ── Preset data (NO emoji) ───────────────────────────── */
const PRESETS = [
  { key: 'ayam',  label: 'Ayam',  Icon: ChickenImg, temp: IncubationPrograms.ayam.targetTemp,  humid: IncubationPrograms.ayam.targetHumidity,  color: '#D97706', bg: 'rgba(217,119,6,0.08)',  border: 'rgba(217,119,6,0.25)' },
  { key: 'puyuh', label: 'Puyuh', Icon: IconQuail,   temp: IncubationPrograms.puyuh.targetTemp, humid: IncubationPrograms.puyuh.targetHumidity, color: '#92400E', bg: 'rgba(146,64,14,0.08)', border: 'rgba(146,64,14,0.25)' },
  { key: 'bebek', label: 'Bebek', Icon: IconDuck,    temp: IncubationPrograms.bebek.targetTemp, humid: IncubationPrograms.bebek.targetHumidity, color: '#1D4ED8', bg: 'rgba(29,78,216,0.08)',  border: 'rgba(29,78,216,0.25)' },
] as const;

/* ── Custom Preset Modal ──────────────────────────────── */
function CustomPresetModal({ onApply, onClose }: {
  onApply: (name: string, temp: number, humid: number) => void;
  onClose: () => void;
}) {
  const [name,  setName]  = useState('');
  const [temp,  setTemp]  = useState(37.5);
  const [humid, setHumid] = useState(60);

  const stepT = (d: number) => setTemp(v => Math.round(Math.min(42, Math.max(30, v + d)) * 10) / 10);
  const stepH = (d: number) => setHumid(v => Math.min(99, Math.max(30, v + d)));

  const stepBtn = (label: string, onClick: () => void, color: string) => (
    <button onClick={onClick} style={{
      width: 38, height: 38, borderRadius: 12,
      background: color, border: 'none', color: '#fff',
      fontSize: 20, fontWeight: 500, cursor: 'pointer',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0,
    }}>{label}</button>
  );

  return (
    <div style={{
      position:'fixed', inset:0, zIndex:9999,
      background:'rgba(0,0,0,0.5)',
      display:'flex', alignItems:'center', justifyContent:'center',
      padding:'16px 16px 96px',
      animation:'ob-fadeIn 0.2s ease both',
    }} onClick={onClose}>
      <div style={{
        width:'100%', maxWidth:420,
        maxHeight:'100%', overflowY:'auto',
        background:'#FFFFFF', borderRadius:24,
        padding:'20px 20px 24px',
        boxShadow:'0 20px 60px rgba(0,0,0,0.3)',
        animation:'ob-fadeInUp 0.3s cubic-bezier(0.34,1.56,0.64,1) both',
      }} onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:4 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: '#1A2B1C', letterSpacing: -0.3 }}>
            Setelan Kustom
          </h2>
          <button onClick={onClose} style={{ width:32, height:32, borderRadius:10, background:'rgba(0,0,0,0.06)', border:'none', cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M18 6L6 18M6 6l12 12" stroke="#4A5568" strokeWidth="2" strokeLinecap="round"/></svg>
          </button>
        </div>
        <p style={{ fontSize: 13, color: '#8A9E8C', marginBottom: 24, lineHeight: 1.5 }}>
          Masukkan nama jenis telur dan target kondisinya.
        </p>

        {/* Nama */}
        <label style={{ fontSize: 12, fontWeight: 600, color: '#4A5568', display: 'block', marginBottom: 6 }}>
          Nama Jenis Telur
        </label>
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="Contoh: Entok, Angsa, Merpati..."
          style={{
            width: '100%', padding: '12px 14px', borderRadius: 14,
            border: '1.5px solid rgba(0,0,0,0.1)',
            background: '#F8F9FA', fontSize: 14, color: '#1A2B1C',
            outline: 'none', boxSizing: 'border-box',
            fontFamily: 'inherit', marginBottom: 20,
          }}
        />

        {/* Suhu */}
        <label style={{ fontSize: 12, fontWeight: 600, color: '#4A5568', display: 'block', marginBottom: 10 }}>
          Target Suhu
        </label>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20, padding: '12px 14px', background: '#FFF1F2', borderRadius: 14, border: '1px solid rgba(239,68,68,0.1)' }}>
          {stepBtn('−', () => stepT(-0.1), '#EF4444')}
          <span style={{ flex: 1, textAlign: 'center', fontSize: 22, fontWeight: 800, color: '#B91C1C', letterSpacing: -0.5 }}>
            {temp.toFixed(1)}°C
          </span>
          {stepBtn('+', () => stepT(0.1), '#EF4444')}
        </div>

        {/* Kelembaban */}
        <label style={{ fontSize: 12, fontWeight: 600, color: '#4A5568', display: 'block', marginBottom: 10 }}>
          Target Kelembaban
        </label>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24, padding: '12px 14px', background: '#EFF6FF', borderRadius: 14, border: '1px solid rgba(59,130,246,0.1)' }}>
          {stepBtn('−', () => stepH(-1), '#3B82F6')}
          <span style={{ flex: 1, textAlign: 'center', fontSize: 22, fontWeight: 800, color: '#1D4ED8', letterSpacing: -0.5 }}>
            {humid}%
          </span>
          {stepBtn('+', () => stepH(1), '#3B82F6')}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={onClose} style={{
            flex: 1, padding: '14px 0', borderRadius: 14,
            background: '#F2F4F6', border: 'none',
            fontSize: 14, fontWeight: 600, color: '#8A9E8C', cursor: 'pointer',
          }}>Batal</button>
          <button
            onClick={() => { if (name.trim()) { onApply(name.trim(), temp, humid); } }}
            disabled={!name.trim()}
            style={{
              flex: 2, padding: '14px 0', borderRadius: 14,
              background: name.trim() ? 'linear-gradient(135deg,#2F6B3F,#3D8A52)' : '#E2E8F0',
              border: 'none', fontSize: 14, fontWeight: 700,
              color: name.trim() ? '#FFFFFF' : '#A0AEC0', cursor: name.trim() ? 'pointer' : 'not-allowed',
              boxShadow: name.trim() ? '0 6px 18px rgba(47,107,63,0.3)' : 'none',
              transition: 'all 0.2s',
            }}
          >Terapkan Setelan</button>
        </div>
      </div>
    </div>
  );
}

/* ── Range Control (Min / Maks input) ─────────────────── */
function RangeControl({ icon, label, current, currentUnit, color, bg, border, value, min, max, step, format, onChange }: {
  icon: React.ReactNode; label: string; current: number; currentUnit: string;
  color: string; bg: string; border: string;
  value: number; min: number; max: number; step: number;
  format: (v: number) => string;
  onChange: (delta: number) => void;
}) {
  // Derive min & max from value with ±tolerance
  const tol = step === 0.1 ? 1.5 : 5;
  const valMin = Math.max(min, Math.round((value - tol) * (1/step)) / (1/step));
  const valMax = Math.min(max, Math.round((value + tol) * (1/step)) / (1/step));

  const stepBtn = (label: string, delta: number, disabled: boolean) => (
    <button
      onClick={() => !disabled && onChange(delta)}
      disabled={disabled}
      style={{
        width: 28, height: 28, borderRadius: 8, border: 'none',
        cursor: disabled ? 'not-allowed' : 'pointer',
        background: disabled ? 'rgba(0,0,0,0.05)' : `${color}18`,
        color: disabled ? '#ADADAD' : color,
        fontSize: 16, fontWeight: 700,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transition: 'all 0.12s', flexShrink: 0,
      }}
    >{label}</button>
  );

  return (
    <div style={{ padding: '10px 12px', background: bg, borderRadius: 14, border: `1px solid ${border}`, overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <div style={{ width: 32, height: 32, borderRadius: 10, background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          {icon}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ fontSize: 12, fontWeight: 600, color: '#4A5568' }}>{label}</p>
          <p style={{ fontSize: 10, color: '#ADADAD' }}>Saat ini {current}{currentUnit}</p>
        </div>
      </div>

      {/* Min / Maks — value on top, buttons below */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'stretch' }}>
        {/* Min box */}
        <div style={{
          flex: 1, minWidth: 0, background: '#FFFFFF', borderRadius: 10,
          border: `1.5px solid ${color}20`, padding: '8px 6px',
          textAlign: 'center', overflow: 'hidden',
        }}>
          <p style={{ fontSize: 9, fontWeight: 700, color: color, letterSpacing: 0.4, marginBottom: 5, opacity: 0.65 }}>MINIMUM</p>
          <p style={{ fontSize: 15, fontWeight: 800, color: color, letterSpacing: -0.3, marginBottom: 7, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {format(valMin)}
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 6 }}>
            {stepBtn('−', -step, value - step < min)}
            {stepBtn('+', step, false)}
          </div>
        </div>

        {/* Arrow */}
        <div style={{ display: 'flex', alignItems: 'center', color: '#CBD5E1', fontSize: 13, flexShrink: 0 }}>→</div>

        {/* Max box */}
        <div style={{
          flex: 1, minWidth: 0, background: '#FFFFFF', borderRadius: 10,
          border: `1.5px solid ${color}20`, padding: '8px 6px',
          textAlign: 'center', overflow: 'hidden',
        }}>
          <p style={{ fontSize: 9, fontWeight: 700, color: color, letterSpacing: 0.4, marginBottom: 5, opacity: 0.65 }}>MAKSIMUM</p>
          <p style={{ fontSize: 15, fontWeight: 800, color: color, letterSpacing: -0.3, marginBottom: 7, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {format(valMax)}
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 6 }}>
            {stepBtn('−', -step, false)}
            {stepBtn('+', step, value + step > max)}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Manual Control ───────────────────────────────────── */
function ManualControl({ inc, isManual, onToggle }: { inc: Incubator; isManual: boolean; onToggle: (v: boolean) => void }) {
  const { updateIoTData } = useAppStore();
  const prog    = IncubationPrograms[inc.species];
  const tTarget = inc.phase === 'hatching' ? prog.targetTempHatching : prog.targetTemp;
  const hTarget = inc.phase === 'hatching' ? prog.targetHumidityHatching : prog.targetHumidity;
  const [targetTemp,  setTargetTemp]  = useState(tTarget);
  const [targetHumid, setTargetHumid] = useState(hTarget);

  const changeTemp = (d: number) => {
    const v = Math.min(42, Math.max(30, Math.round((targetTemp + d) * 10) / 10));
    setTargetTemp(v); updateIoTData(inc.id, { temperature: v });
  };
  const changeHumid = (d: number) => {
    const v = Math.min(99, Math.max(30, Math.round(targetHumid + d)));
    setTargetHumid(v); updateIoTData(inc.id, { humidity: v });
  };

  return (
    <div style={{
      background: '#FFFFFF', borderRadius: 20,
      border: `1.5px solid ${isManual ? 'rgba(245,158,11,0.3)' : 'rgba(0,0,0,0.06)'}`,
      boxShadow: isManual ? '0 2px 12px rgba(245,158,11,0.1)' : '0 2px 12px rgba(0,0,0,0.06)',
      padding: 16,
      transition: 'border-color 0.25s, box-shadow 0.25s',
    }}>
      {/* Header with toggle */}
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 14 }}>
        <div style={{ width: 6, height: 6, borderRadius: 3, background: isManual ? '#F59E0B' : '#94A3B8', marginRight: 6, transition: 'background 0.2s' }} />
        <span style={{ fontSize: 11, fontWeight: 500, color: '#8A9E8C', letterSpacing: 0.2, flex: 1 }}>Kontrol Manual</span>
        <button
          onClick={() => onToggle(!isManual)}
          style={{
            width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
            background: isManual ? '#F59E0B' : '#E2E8F0',
            position: 'relative', transition: 'background 0.25s', flexShrink: 0, padding: 0,
          }}
          aria-label={isManual ? 'Nonaktifkan kontrol manual' : 'Aktifkan kontrol manual'}
        >
          <div style={{
            position: 'absolute', top: 4, left: isManual ? 22 : 4,
            width: 16, height: 16, borderRadius: 8, background: '#FFFFFF',
            boxShadow: '0 1px 3px rgba(0,0,0,0.25)',
            transition: 'left 0.25s cubic-bezier(0.34,1.56,0.64,1)',
          }} />
        </button>
      </div>

      {/* Controls — dimmed when not in manual mode */}
      <div style={{ opacity: isManual ? 1 : 0.4, pointerEvents: isManual ? 'auto' : 'none', transition: 'opacity 0.25s', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <RangeControl
          icon={<IconThermometer size={18} color="#EF4444" />}
          label="Suhu Target"
          current={inc.iotData.temperature}
          currentUnit="°C"
          color="#EF4444"
          bg="#FFF7F7"
          border="rgba(239,68,68,0.1)"
          value={targetTemp}
          min={30} max={42} step={0.1}
          format={(v) => `${v.toFixed(1)}°C`}
          onChange={(d) => changeTemp(d)}
        />
        <RangeControl
          icon={<IconDroplet size={18} color="#3B82F6" />}
          label="Kelembaban Target"
          current={inc.iotData.humidity}
          currentUnit="%"
          color="#3B82F6"
          bg="#F0F7FF"
          border="rgba(59,130,246,0.1)"
          value={targetHumid}
          min={30} max={99} step={1}
          format={(v) => `${v}%`}
          onChange={(d) => changeHumid(d)}
        />
      </div>
    </div>
  );
}



/* ── Hero Card ─────────────────────────────────────────── */
function HeroCard({ inc, isManual, onClick }: { inc: Incubator; isManual: boolean; onClick: () => void }) {
  const prog      = IncubationPrograms[inc.species];
  const daysLeft  = prog.durationDays - inc.currentDay;
  const progress  = Math.min(inc.currentDay / prog.durationDays, 1);
  const hatchDate = new Date(inc.startDate.getTime() + prog.durationDays * 864e5);
  const hatchStr  = hatchDate.toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' });

  // Always use farm image for ayam — status shown via badge, not bg color
  const bgImage = inc.species === 'ayam'
    ? 'url(/icons/bg-card-ayam.png)' : undefined;
  const textShadow = '0 1px 8px rgba(0,0,0,0.5)';

  return (
    <div
      onClick={onClick}
      style={{
        ...(bgImage
          ? {
              backgroundImage: `${bgImage}, linear-gradient(145deg,#14532D,#2F6B3F)`,
              backgroundSize: 'cover, cover',
              backgroundPosition: '100% 65%, center',
              backgroundRepeat: 'no-repeat, no-repeat',
            }
          : { background: 'linear-gradient(145deg,#14532D,#2F6B3F)' }),
        margin: '0 0 4px',
        borderRadius: 20,
        minHeight: 250,
        padding: '18px 20px 28px',
        cursor: 'pointer',
        position: 'relative', overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(0,0,0,0.28)',
      }}
    >
      {/* Dual overlay: left→right for text, top→bottom to cover farm image at bottom */}
      {bgImage && (
        <div style={{
          position:'absolute', inset:0,
          background:'linear-gradient(105deg,rgba(0,0,0,0.72) 0%,rgba(0,0,0,0.45) 45%,rgba(0,0,0,0.15) 100%)',
          pointerEvents:'none'
        }} />
      )}
      {bgImage && (
        <div style={{
          position:'absolute', inset:0,
          background:'linear-gradient(to bottom,transparent 40%,rgba(0,0,0,0.55) 100%)',
          pointerEvents:'none'
        }} />
      )}

      {/* TOP: Status + title + species icon */}
      <div style={{ position:'relative', zIndex:1, display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:14 }}>
        <div>
          <div style={{ display:'flex', alignItems:'center', gap:6, marginBottom:5 }}>
            <div style={{
              width:6, height:6, borderRadius:'50%',
              background: inc.status === 'berbahaya' ? '#F87171' : inc.status === 'perlu_perhatian' ? '#FCD34D' : '#4ADE80',
              boxShadow: inc.status === 'berbahaya' ? '0 0 6px #F87171' : inc.status === 'perlu_perhatian' ? '0 0 6px #FCD34D' : '0 0 6px #4ADE80',
            }} />
            <p style={{ fontSize:11, fontWeight:500, color:'rgba(255,255,255,0.75)', textShadow }}>
              {inc.status === 'berbahaya' ? 'Perlu Perhatian Segera' : inc.status === 'perlu_perhatian' ? 'Perlu Dicek' : 'Inkubator Aktif'}
            </p>
          </div>
          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
            <p style={{ fontSize:19, fontWeight:600, color:'#FFFFFF', letterSpacing:-0.3, textShadow }}>{inc.name}</p>
          </div>
        </div>
        <div style={{ background:'rgba(255,255,255,0.15)', backdropFilter:'blur(4px)', borderRadius:14, padding:'8px 10px', display:'flex', flexDirection:'column', alignItems:'center', gap:4 }}>
          {inc.species === 'ayam' ? <ChickenImg size={30}/> : inc.species === 'puyuh' ? <IconQuail size={30}/> : <IconDuck size={30}/>}
          <span style={{ fontSize:10, color:'rgba(255,255,255,0.8)', fontWeight:500 }}>{prog.nameId}</span>
        </div>
      </div>

      {/* MIDDLE: Countdown row */}
      <div style={{ position:'relative', zIndex:1, display:'flex', alignItems:'flex-end', gap:8, marginBottom:0 }}>
        <div style={{ display:'flex', alignItems:'baseline', gap:8 }}>
          <span style={{ fontSize:64, fontWeight:500, color:'#FFFFFF', letterSpacing:-3, lineHeight:1, textShadow }}>{daysLeft}</span>
          <div>
            <p style={{ fontSize:16, fontWeight:400, color:'rgba(255,255,255,0.95)', textShadow }}>hari lagi</p>
            <p style={{ fontSize:12, color:'rgba(255,255,255,0.7)', marginTop:2, textShadow }}>Hari ke-{inc.currentDay} / {prog.durationDays}</p>
          </div>
        </div>
        <div style={{ marginLeft:'auto', textAlign:'right', paddingBottom:4 }}>
          <p style={{ fontSize:11, color:'rgba(255,255,255,0.65)', marginBottom:3, textShadow }}>Telur</p>
          <p style={{ fontSize:24, fontWeight:600, color:'#FFFFFF', letterSpacing:-0.5, textShadow }}>{inc.totalEggs}</p>
        </div>
      </div>

      {/* BOTTOM: Progress bar + hatch date */}
      <div style={{ position:'relative', zIndex:1, marginTop:16 }}>
        <div style={{ height:6, background:'rgba(255,255,255,0.18)', borderRadius:999, overflow:'hidden' }}>
          <div style={{ height:'100%', width:`${progress*100}%`, background:'rgba(255,255,255,0.85)', borderRadius:999, transition:'width 0.6s' }} />
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:8, marginTop:10 }}>
          <IconCalendar size={13} color="rgba(255,255,255,0.65)" />
          <p style={{ fontSize:12, color:'rgba(255,255,255,0.82)', textShadow }}>
            Perkiraan menetas: <span style={{ fontWeight:600, color:'#FFFFFF' }}>{hatchStr}</span>
          </p>
          <div style={{ marginLeft:'auto' }}><IconArrowRight size={13} color="rgba(255,255,255,0.5)" /></div>
        </div>
      </div>
    </div>
  );
}

function IncubatorCard({ inc, onFinish }: { inc: Incubator; onFinish: () => void }) {
  const { updateIoTData, manualModes, setManualMode } = useAppStore();
  const isManual = !!manualModes[inc.id];
  const prog = IncubationPrograms[inc.species];
  const isHatching = inc.phase === 'hatching';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* ── Sensor Metrics row ── */}
      <div style={{ display:'flex', gap:12 }}>
        {/* Temperature */}
        <div style={{
          flex:1, borderRadius:18, padding:'18px 16px 16px',
          background:'linear-gradient(135deg,#FFF1F2,#FFE4E6)',
          border:'1.5px solid rgba(239,68,68,0.15)',
        }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12 }}>
            <div style={{ width:36, height:36, borderRadius:12, background:'rgba(239,68,68,0.12)', display:'flex', alignItems:'center', justifyContent:'center' }}>
              <IconThermometer size={20} color="#EF4444" />
            </div>
            <span style={{ fontSize:9, fontWeight:700, color:'#EF4444', background:'rgba(239,68,68,0.1)', padding:'3px 8px', borderRadius:999, letterSpacing:0.5 }}>SUHU</span>
          </div>
          <p style={{ fontSize:32, fontWeight:800, color:'#B91C1C', letterSpacing:-1, lineHeight:1 }}>{inc.iotData.temperature}<span style={{ fontSize:14, fontWeight:500, color:'#EF4444' }}>°C</span></p>
          <p style={{ fontSize:12, color:'rgba(239,68,68,0.6)', marginTop:6 }}>Target {IncubationPrograms[inc.species].targetTemp}°C</p>
        </div>

        {/* Humidity */}
        <div style={{
          flex:1, borderRadius:18, padding:'18px 16px 16px',
          background:'linear-gradient(135deg,#EFF6FF,#DBEAFE)',
          border:'1.5px solid rgba(59,130,246,0.15)',
        }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12 }}>
            <div style={{ width:36, height:36, borderRadius:12, background:'rgba(59,130,246,0.12)', display:'flex', alignItems:'center', justifyContent:'center' }}>
              <IconDroplet size={20} color="#3B82F6" />
            </div>
            <span style={{ fontSize:9, fontWeight:700, color:'#3B82F6', background:'rgba(59,130,246,0.1)', padding:'3px 8px', borderRadius:999, letterSpacing:0.5 }}>LEMBAB</span>
          </div>
          <p style={{ fontSize:32, fontWeight:800, color:'#1D4ED8', letterSpacing:-1, lineHeight:1 }}>{inc.iotData.humidity}<span style={{ fontSize:14, fontWeight:500, color:'#3B82F6' }}>%</span></p>
          <p style={{ fontSize:12, color:'rgba(59,130,246,0.6)', marginTop:6 }}>Target {IncubationPrograms[inc.species].targetHumidity}%</p>
        </div>
      </div>

      {/* ── Setelan Otomatis ── */}
      {/* ── Active program chip ── */}
      {(() => {
        const p = PRESETS.find(x => x.key === inc.species);
        const prog = IncubationPrograms[inc.species];
        return (
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '6px 12px 6px 8px', borderRadius: 999,
            background: p ? p.bg : 'rgba(0,0,0,0.04)',
            border: `1px solid ${p ? p.border : 'rgba(0,0,0,0.08)'}`,
            alignSelf: 'flex-start',
          }}>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: p?.color ?? '#8A9E8C', flexShrink: 0 }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: p?.color ?? '#8A9E8C' }}>
              Setelan {prog.nameId} aktif
            </span>
            <span style={{ fontSize: 10, color: p?.color ?? '#8A9E8C', opacity: 0.7, fontWeight: 500 }}>
              · {prog.targetTemp}° / {prog.targetHumidity}%
            </span>
          </div>
        );
      })()}

      {/* ── Alert banner: only when manual ── */}
      {isManual && (
        <div style={{
          borderRadius: 16,
          background: 'rgba(245,158,11,0.08)',
          border: '1.5px solid rgba(245,158,11,0.25)',
          padding: '12px 14px',
          display: 'flex', alignItems: 'center', gap: 12,
        }}>
          <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(245,158,11,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: 12, fontWeight: 700, color: '#92400E', marginBottom: 2 }}>Mode Manual Aktif</p>
            <p style={{ fontSize: 11, color: '#B45309', lineHeight: 1.4 }}>Setelan otomatis dinonaktifkan untuk inkubator ini.</p>
          </div>
          <button
            onClick={() => setManualMode(inc.id, false)}
            style={{
              background: '#F59E0B', border: 'none', borderRadius: 10,
              padding: '8px 10px', cursor: 'pointer', flexShrink: 0,
              fontSize: 11, fontWeight: 600, color: '#FFFFFF',
              lineHeight: 1.3, textAlign: 'center',
            }}
          >
            Kembali ke{`\n`}Otomatis
          </button>
        </div>
      )}

      {/* ── Kontrol Manual ── */}
      <ManualControl inc={inc} isManual={isManual} onToggle={(v) => setManualMode(inc.id, v)} />

      {/* ── Selesaikan Penetasan (hatching phase) ── */}
      {isHatching && (
        <button
          onClick={onFinish}
          style={{
            width: '100%', padding: '16px 20px', borderRadius: 18,
            background: 'linear-gradient(135deg, #2F6B3F, #3D8A52)',
            border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 14,
            boxShadow: '0 6px 20px rgba(47,107,63,0.25)',
            transition: 'transform 0.15s',
          }}
        >
          <div style={{
            width: 44, height: 44, borderRadius: 14,
            background: 'rgba(255,255,255,0.18)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <IconEggFilled size={24} color="#FFFFFF" />
          </div>
          <div style={{ textAlign: 'left' }}>
            <p style={{ fontSize: 14, fontWeight: 700, color: '#FFFFFF', marginBottom: 2 }}>Selesaikan Penetasan</p>
            <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)' }}>Input jumlah telur yang berhasil menetas</p>
          </div>
          <div style={{ marginLeft: 'auto' }}>
            <IconArrowRight size={18} color="rgba(255,255,255,0.6)" />
          </div>
        </button>
      )}


    </div>
  );
}

/* ── Empty State ──────────────────────────────────────── */
function EmptyState({ onAdd }: { onAdd: () => void }) {
  return (
    <div style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'48px 28px', gap:24 }}>
      {/* Animated icon */}
      <div style={{
        width:110, height:110, borderRadius:32,
        background:'linear-gradient(135deg,#F0FDF4,#DCFCE7)',
        border:'2px solid rgba(47,107,63,0.15)',
        display:'flex', alignItems:'center', justifyContent:'center',
        boxShadow:'0 12px 32px rgba(47,107,63,0.15)',
        position:'relative', overflow:'hidden',
      }}>
        {/* Pulse ring */}
        <div style={{
          position:'absolute', width:'100%', height:'100%', borderRadius:32,
          border:'2px solid rgba(47,107,63,0.2)',
          animation:'pulse 2s ease-in-out infinite',
        }}/>
        <IconEggFilled size={52} color="#2F6B3F" />
      </div>

      <div style={{ textAlign:'center' }}>
        <h2 style={{ fontSize:22, fontWeight:800, color:'#1A2B1C', marginBottom:10, letterSpacing:-0.3 }}>
          Belum Ada Inkubator
        </h2>
        <p style={{ fontSize:14, color:'#8A9E8C', lineHeight:1.7, maxWidth:260 }}>
          Hubungkan lemari IoT kamu ke aplikasi untuk mulai memantau inkubasi secara real-time.
        </p>
      </div>

      <button onClick={onAdd} style={{
        display:'flex', alignItems:'center', gap:10,
        background:'linear-gradient(135deg,#2F6B3F,#3D8A52)',
        color:'#FFFFFF', borderRadius:16, padding:'15px 32px',
        border:'none', fontSize:15, fontWeight:700, cursor:'pointer',
        boxShadow:'0 6px 20px rgba(47,107,63,0.35)',
      }}>
        <IconPlus size={18} /> Tambah Inkubator
      </button>
    </div>
  );
}

/* ── Connection Sheet ───────────────────────────────── */
function ConnectionSheet({ onClose }: { onClose: () => void }) {
  const { backendUrl, setBackendUrl, tetascoId, isConnected, deviceOnline, startRealtime, stopRealtime, startSim, stopSim, _sensorInterval } = useAppStore();
  const isRealtime = !!_sensorInterval;
  const [draft, setDraft] = useState(backendUrl);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<'ok' | 'fail' | null>(null);

  const handleTest = async () => {
    setTesting(true); setTestResult(null);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 6000);
    try {
      const r = await fetch(`${draft.replace(/\/$/, '')}/api/health`, {
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json' },
      });
      const json = r.ok ? await r.json().catch(() => null) : null;
      // Cek status + mqtt_connected agar benar-benar server MQTT kita
      const ok = r.ok && json?.status === 'ok';
      setTestResult(ok ? 'ok' : 'fail');
    } catch { setTestResult('fail'); }
    finally { clearTimeout(timer); }
    setTesting(false);
  };


  const handleSave = () => {
    setBackendUrl(draft);
    if (isRealtime) { stopRealtime(); setTimeout(() => startRealtime(), 100); }
  };

  const toggleMode = () => {
    if (isRealtime) { stopRealtime(); startSim(); }
    else            { stopSim();      startRealtime(); }
  };

  return (
    <div style={{
      position:'fixed', inset:0, zIndex:9999,
      background:'rgba(0,0,0,0.5)',
      display:'flex', alignItems:'center', justifyContent:'center',
      padding:'16px 16px 96px',
      animation:'ob-fadeIn 0.2s ease both',
    }} onClick={onClose}>
      <div style={{
        width:'100%', maxWidth:420,
        maxHeight:'100%', overflowY:'auto',
        background:'#FFFFFF', borderRadius:24,
        padding:'20px 20px 24px',
        boxShadow:'0 20px 60px rgba(0,0,0,0.3)',
        animation:'ob-fadeInUp 0.3s cubic-bezier(0.34,1.56,0.64,1) both',
      }} onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:4 }}>
          <h2 style={{ fontSize:18, fontWeight:700, color:'#1A2B1C', letterSpacing:-0.3 }}>Koneksi Perangkat</h2>
          <button onClick={onClose} style={{ width:32, height:32, borderRadius:10, background:'rgba(0,0,0,0.06)', border:'none', cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M18 6L6 18M6 6l12 12" stroke="#4A5568" strokeWidth="2" strokeLinecap="round"/></svg>
          </button>
        </div>
        <p style={{ fontSize:13, color:'#8A9E8C', marginBottom:20 }}>Hubungkan ke backend Tetasco di <b>tetasco.my.id</b> (Tetasco ID: <b>{tetascoId}</b>).</p>

        {/* Status row */}
        <div style={{ display:'flex', alignItems:'center', gap:10, padding:'12px 14px', borderRadius:14,
          background: isConnected ? (deviceOnline ? 'rgba(34,197,94,0.08)' : 'rgba(245,158,11,0.08)') : isRealtime ? 'rgba(239,68,68,0.07)' : 'rgba(148,163,184,0.08)',
          border: `1.5px solid ${isConnected ? (deviceOnline ? 'rgba(34,197,94,0.2)' : 'rgba(245,158,11,0.2)') : isRealtime ? 'rgba(239,68,68,0.15)' : 'rgba(148,163,184,0.15)'}`,
          marginBottom:20 }}>
          <div style={{ width:10, height:10, borderRadius:'50%', flexShrink:0,
            background: !isRealtime ? '#94A3B8' : !isConnected ? '#EF4444' : deviceOnline ? '#22C55E' : '#F59E0B',
            boxShadow: isConnected && deviceOnline ? '0 0 8px #22C55E80' : isConnected ? '0 0 6px #F59E0B80' : 'none' }} />
          <span style={{ fontSize:13, fontWeight:600, color: !isRealtime ? '#64748B' : !isConnected ? '#991B1B' : deviceOnline ? '#166534' : '#92400E' }}>
            {!isRealtime ? 'Mode Simulasi' : !isConnected ? 'Tidak bisa terhubung ke server' : deviceOnline ? 'Terhubung ke Raspberry Pi' : 'Server OK, Lemari standby...'}
          </span>
        </div>

        {/* URL input */}
        <label style={{ fontSize:12, fontWeight:600, color:'#4A5568', display:'block', marginBottom:6 }}>URL Backend</label>
        <div style={{ display:'flex', gap:8, marginBottom:8 }}>
          <input
            value={draft}
            onChange={e => setDraft(e.target.value)}
            placeholder="https://tetasco.my.id"
            style={{
              flex:1, padding:'11px 14px', borderRadius:12,
              border:'1.5px solid rgba(0,0,0,0.1)',
              background:'#F8F9FA', fontSize:13, color:'#1A2B1C',
              outline:'none', fontFamily:'monospace',
            }}
          />
          <button onClick={handleTest} disabled={testing} style={{
            padding:'11px 14px', borderRadius:12, border:'none',
            background:'rgba(47,107,63,0.1)', color:'#2F6B3F',
            fontSize:12, fontWeight:600, cursor:'pointer', flexShrink:0,
          }}>{testing ? '...' : 'Tes'}</button>
        </div>
        {testResult && (
          <p style={{ fontSize:12, marginBottom:12,
            color: testResult === 'ok' ? '#166534' : '#991B1B',
            fontWeight:500 }}>
            {testResult === 'ok' ? '✓ Berhasil terhubung!' : '✕ Tidak bisa terhubung. Cek IP dan pastikan backend aktif.'}
          </p>
        )}
        <button onClick={handleSave} style={{
          width:'100%', padding:'12px 0', borderRadius:12, border:'none',
          background:'rgba(47,107,63,0.08)', color:'#2F6B3F',
          fontSize:13, fontWeight:600, cursor:'pointer', marginBottom:16,
        }}>Simpan Alamat</button>

        {/* Mode toggle */}
        <button onClick={toggleMode} style={{
          width:'100%', padding:'14px 0', borderRadius:14, border:'none',
          background: isRealtime
            ? 'linear-gradient(135deg,#EF4444,#DC2626)'
            : 'linear-gradient(135deg,#2F6B3F,#3D8A52)',
          color:'#FFF', fontSize:14, fontWeight:700, cursor:'pointer',
          boxShadow: isRealtime ? '0 6px 18px rgba(239,68,68,0.3)' : '0 6px 18px rgba(47,107,63,0.3)',
        }}>
          {isRealtime ? 'Beralih ke Mode Simulasi' : 'Aktifkan Koneksi Nyata'}
        </button>
      </div>
    </div>
  );
}

export function Home() {
  const navigate = useNavigate();
  const { farmer, incubators, notifications, manualModes, isConnected, deviceOnline, _sensorInterval, finishIncubation } = useAppStore();
  const [showConnSheet, setShowConnSheet] = useState(false);
  const [harvestInc, setHarvestInc] = useState<Incubator | null>(null);
  const isRealtime = !!_sensorInterval;

  const active = incubators.filter(i => i.isActive);
  const inc    = active[0];
  const unread = notifications.filter(n => !n.read).length;
  const now    = new Date();

  const timeStr  = now.toLocaleDateString('id-ID', { weekday:'long', day:'numeric', month:'long', year:'numeric' });
  const hour     = now.getHours();
  const greeting = hour < 11 ? 'Selamat pagi' : hour < 15 ? 'Selamat siang' : hour < 18 ? 'Selamat sore' : 'Selamat malam';
  const firstName = (farmer.name || farmer.farmName || 'Peternak').split(' ').slice(0,2).join(' ');

  return (
    <div className="screen anim-fade-in">
      {/* ── Full scrollable body (greeting + cards) ── */}
      <div
        className="screen-scroll flex-1"
        style={{
          paddingTop: 'env(safe-area-inset-top, 44px)',
          paddingLeft: 16,
          paddingRight: 16,
          paddingBottom: 40,
          display:'flex', flexDirection:'column', gap:16,
          background:'#F2F4F6',
        }}
      >
        {/* Greeting */}
        <div style={{ position:'relative', padding:'10px 0 0', paddingRight: 130 }}>
          {/* ── Top-right buttons: Koneksi · Kamera · Notif ── */}
          <div style={{ position:'absolute', top:10, right:16, zIndex:2, display:'flex', gap:6 }}>

            {/* Connection dot */}
            <button
              onClick={() => setShowConnSheet(true)}
              style={{
                width:36, height:36, borderRadius:10,
                background:'rgba(0,0,0,0.06)',
                border:'1px solid rgba(0,0,0,0.08)',
                display:'flex', alignItems:'center', justifyContent:'center',
                cursor:'pointer',
              }}
              title="Koneksi perangkat"
            >
              <div style={{
                width:10, height:10, borderRadius:'50%',
                background: !isRealtime ? '#94A3B8'
                  : !isConnected ? '#EF4444'
                  : deviceOnline ? '#22C55E'
                  : '#F59E0B',
                boxShadow: isConnected && deviceOnline ? '0 0 8px #22C55E99' : isConnected ? '0 0 6px #F59E0B88' : 'none',
              }} />
            </button>

            {/* Camera icon — hanya tampil jika ada inkubator aktif */}
            {inc && (
              <button
                onClick={() => navigate('/camera')}
                style={{
                  width:36, height:36, borderRadius:10,
                  background:'rgba(0,0,0,0.06)',
                  border:'1px solid rgba(0,0,0,0.08)',
                  display:'flex', alignItems:'center', justifyContent:'center',
                  cursor:'pointer', fontSize:17,
                }}
                title="Lihat kamera live"
              >
                🎥
              </button>
            )}

            {/* Bell notif */}
            <button
              onClick={() => navigate('/notifications')}
              style={{
                width:36, height:36, borderRadius:10,
                background:'rgba(0,0,0,0.06)',
                border:'1px solid rgba(0,0,0,0.08)',
                display:'flex', alignItems:'center', justifyContent:'center',
                cursor:'pointer', position:'relative',
              }}
            >
              <IconBell size={17} color="#4A5568" />
              {unread > 0 && (
                <div style={{ position:'absolute', top:7, right:7, width:6, height:6, borderRadius:'50%', background:'#EF4444', border:'1.5px solid #F2F4F6' }} />
              )}
            </button>
          </div>



          <p style={{ fontSize:12, color:'#8A9E8C', fontWeight:400, marginBottom:3 }}>{greeting},</p>
          <h1 style={{ fontSize:22, fontWeight:700, color:'#1A2B1C', lineHeight:1.2, marginBottom:8, letterSpacing:-0.3 }}>
            {firstName}!
          </h1>
          <div style={{
            display:'inline-flex', alignItems:'center', gap:5,
            background:'rgba(47,107,63,0.08)',
            border:'1px solid rgba(47,107,63,0.15)',
            borderRadius:999, padding:'5px 10px',
          }}>
            <IconMapPin size={11} color="#2F6B3F" />
            <span style={{ fontSize:11, color:'#2F6B3F', fontWeight:500 }}>
              {[farmer.desa, farmer.kabupaten].filter(Boolean)[0] || farmer.farmName || 'Lokasi belum diset'}
            </span>
          </div>
        </div>

        {!inc ? (
          <EmptyState onAdd={() => navigate('/incubator/add-device')} />
        ) : (
          <>
            <HeroCard inc={inc} isManual={!!manualModes[inc.id]} onClick={() => navigate(`/incubator/${inc.id}`)} />
            <IncubatorCard inc={inc} onFinish={() => setHarvestInc(inc)} />

            {/* Add more button */}
            {active.length < 3 && (
              <button className="btn-secondary" onClick={() => navigate('/incubator/add-device')}
                style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:8, padding:'14px', borderRadius:16 }}>
                <IconPlus size={16} color="#2F6B3F" />
                <span style={{ fontSize:14, fontWeight:500, color:'#2F6B3F' }}>+ Hubungkan Lemari Lain</span>
              </button>
            )}
          </>
        )}
      </div>

      {/* Connection sheet */}
      {showConnSheet && <ConnectionSheet onClose={() => setShowConnSheet(false)} />}

      {/* Harvest sheet */}
      {harvestInc && (
        <HarvestSheet
          inc={harvestInc}
          onClose={() => setHarvestInc(null)}
          onSubmit={(count) => {
            finishIncubation(harvestInc.id, count);
            setHarvestInc(null);
          }}
        />
      )}
    </div>
  );
}

/* ── Harvest Sheet ────────────────────────────────────── */
function HarvestSheet({ inc, onClose, onSubmit }: { inc: Incubator; onClose: () => void; onSubmit: (hatched: number) => void }) {
  const [count, setCount] = useState(0);
  const [notes, setNotes] = useState('');
  const prog = IncubationPrograms[inc.species];
  const pct = inc.totalEggs > 0 ? Math.round((count / inc.totalEggs) * 100) : 0;

  // Body scroll lock
  useEffect(() => {
    document.body.setAttribute('data-sheet-open', '1');
    return () => document.body.removeAttribute('data-sheet-open');
  }, []);

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 900,
        background: 'rgba(0,0,0,0.5)',
        display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
        animation: 'fadeIn 0.2s ease both',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: 480,
          background: '#FFFFFF', borderRadius: '24px 24px 0 0',
          padding: '20px 20px', paddingBottom: 'max(24px, env(safe-area-inset-bottom))',
          animation: 'custom-slideUp 0.3s cubic-bezier(0.16,1,0.3,1) both',
          maxHeight: '85vh', overflowY: 'auto',
        }}
      >
        {/* Handle */}
        <div style={{ width: 40, height: 4, borderRadius: 2, background: '#E2E8F0', margin: '0 auto 16px' }} />

        {/* Title */}
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 18,
            background: 'linear-gradient(135deg, #F0FDF4, #DCFCE7)',
            border: '2px solid rgba(47,107,63,0.15)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 12px',
          }}>
            <IconEggFilled size={28} color="#2F6B3F" />
          </div>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#1A2B1C', marginBottom: 4 }}>Hasil Penetasan</h2>
          <p style={{ fontSize: 13, color: '#8A9E8C' }}>{inc.name} · {prog.nameId} · {inc.totalEggs} telur</p>
        </div>

        {/* Counter */}
        <div style={{
          background: '#F8F9FA', borderRadius: 20, padding: '20px 16px',
          border: '1.5px solid rgba(0,0,0,0.06)', marginBottom: 16,
        }}>
          <p style={{ fontSize: 12, fontWeight: 600, color: '#8A9E8C', marginBottom: 12, textAlign: 'center' }}>
            Berapa telur yang berhasil menetas?
          </p>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16 }}>
            <button
              onClick={() => setCount(c => Math.max(0, c - 1))}
              style={{
                width: 48, height: 48, borderRadius: 16,
                background: '#FFFFFF', border: '1.5px solid rgba(0,0,0,0.1)',
                fontSize: 22, fontWeight: 700, color: '#4A5568',
                cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: '0 2px 6px rgba(0,0,0,0.06)',
              }}
            >−</button>
            <input
              type="number"
              value={count}
              onChange={e => {
                const v = parseInt(e.target.value) || 0;
                setCount(Math.min(inc.totalEggs, Math.max(0, v)));
              }}
              style={{
                width: 80, textAlign: 'center',
                fontSize: 36, fontWeight: 800, color: '#1A2B1C',
                border: 'none', background: 'transparent', outline: 'none',
                fontFamily: 'inherit',
              }}
            />
            <button
              onClick={() => setCount(c => Math.min(inc.totalEggs, c + 1))}
              style={{
                width: 48, height: 48, borderRadius: 16,
                background: '#2F6B3F', border: 'none',
                fontSize: 22, fontWeight: 700, color: '#FFFFFF',
                cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(47,107,63,0.3)',
              }}
            >+</button>
          </div>
          <p style={{ fontSize: 12, color: '#8A9E8C', textAlign: 'center', marginTop: 8 }}>
            dari {inc.totalEggs} telur ({pct}% berhasil)
          </p>

          {/* Quick fill buttons */}
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 12 }}>
            {[Math.round(inc.totalEggs * 0.5), Math.round(inc.totalEggs * 0.75), inc.totalEggs].map(v => (
              <button
                key={v}
                onClick={() => setCount(v)}
                style={{
                  padding: '6px 14px', borderRadius: 999, border: '1.5px solid rgba(0,0,0,0.08)',
                  background: count === v ? '#2F6B3F' : '#FFFFFF',
                  color: count === v ? '#FFFFFF' : '#4A5568',
                  fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >{v}</button>
            ))}
          </div>
        </div>

        {/* Success rate indicator */}
        <div style={{
          borderRadius: 14, padding: '12px 16px', marginBottom: 16,
          background: pct >= 70 ? 'rgba(34,197,94,0.08)' : pct >= 40 ? 'rgba(245,158,11,0.08)' : 'rgba(239,68,68,0.08)',
          border: `1.5px solid ${pct >= 70 ? 'rgba(34,197,94,0.2)' : pct >= 40 ? 'rgba(245,158,11,0.2)' : 'rgba(239,68,68,0.2)'}`,
          display: 'flex', alignItems: 'center', gap: 10,
        }}>
          <div style={{
            width: 8, height: 8, borderRadius: '50%',
            background: pct >= 70 ? '#22C55E' : pct >= 40 ? '#F59E0B' : '#EF4444',
          }} />
          <p style={{ fontSize: 12, fontWeight: 600, color: pct >= 70 ? '#166534' : pct >= 40 ? '#92400E' : '#991B1B' }}>
            {count === 0 ? 'Belum ada input' : pct >= 70 ? 'Hasil penetasan baik!' : pct >= 40 ? 'Hasil penetasan cukup' : 'Hasil penetasan kurang baik'}
          </p>
        </div>

        {/* Buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <button
            onClick={() => count > 0 && onSubmit(count)}
            disabled={count === 0}
            style={{
              width: '100%', padding: '16px 0', borderRadius: 16,
              background: count > 0 ? 'linear-gradient(135deg, #2F6B3F, #3D8A52)' : '#E2E8F0',
              border: 'none', color: count > 0 ? '#FFFFFF' : '#A0AEC0',
              fontSize: 15, fontWeight: 700, cursor: count > 0 ? 'pointer' : 'not-allowed',
              boxShadow: count > 0 ? '0 6px 20px rgba(47,107,63,0.3)' : 'none',
              transition: 'all 0.2s',
            }}
          >
            Simpan & Selesaikan
          </button>
          <button
            onClick={onClose}
            style={{
              width: '100%', padding: '14px 0', borderRadius: 16,
              background: 'transparent', border: '1.5px solid rgba(0,0,0,0.08)',
              color: '#4A5568', fontSize: 14, fontWeight: 600, cursor: 'pointer',
            }}
          >
            Batal
          </button>
        </div>
      </div>
    </div>
  );
}
