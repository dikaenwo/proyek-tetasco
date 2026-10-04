import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/appStore';

/* ── Field SVG Icons ──────────────────────────────────── */
const IconPerson = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="8" r="4" stroke="#8A9E8C" strokeWidth="1.8"/>
    <path d="M4 20c0-3.314 3.582-6 8-6s8 2.686 8 6" stroke="#8A9E8C" strokeWidth="1.8" strokeLinecap="round"/>
  </svg>
);
const IconFarm = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
    <path d="M3 10.5L12 3L21 10.5V20a1 1 0 01-1 1H15v-6H9v6H4a1 1 0 01-1-1V10.5z" stroke="#8A9E8C" strokeWidth="1.8" strokeLinejoin="round"/>
  </svg>
);
const IconMapPin = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
    <path d="M12 2C8.686 2 6 4.686 6 8c0 5.25 6 13 6 13s6-7.75 6-13c0-3.314-2.686-6-6-6z" stroke="#8A9E8C" strokeWidth="1.8"/>
    <circle cx="12" cy="8" r="2" stroke="#8A9E8C" strokeWidth="1.5"/>
  </svg>
);
const IconArea = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
    <rect x="3" y="10" width="8" height="11" rx="1" stroke="#8A9E8C" strokeWidth="1.8"/>
    <path d="M11 21V7l10-4v18" stroke="#8A9E8C" strokeWidth="1.8" strokeLinejoin="round"/>
    <path d="M15 13h2M15 17h2M6 14h2" stroke="#8A9E8C" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
);

/* ── Tetasco Wordmark ─────────────────────────────────── */
const TetascoWordmark = ({ dark = false }: { dark?: boolean }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
    <img
      src="/logo-tetasco.png"
      alt="Tetasco"
      style={{ width: 32, height: 32, objectFit: 'contain' }}
    />
    <span style={{ fontSize: 16, fontWeight: 700, letterSpacing: -0.3, color: dark ? '#1A2B1C' : 'rgba(255,255,255,0.92)' }}>
      Tetasco Connect
    </span>
  </div>
);

/* ── Slide Illustrations ─────────────────────────────── */
const IllustrationMonitor = () => (
  <svg width="200" height="200" viewBox="0 0 200 200" fill="none">
    <circle cx="100" cy="100" r="88" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.08)" strokeWidth="1.5" className="ob-ring"/>
    <circle cx="100" cy="100" r="64" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.06)" strokeWidth="1"/>
    {/* Phone frame */}
    <rect x="68" y="44" width="64" height="108" rx="14" fill="rgba(255,255,255,0.13)" stroke="rgba(255,255,255,0.28)" strokeWidth="1.5"/>
    <rect x="74" y="58" width="52" height="80" rx="5" fill="rgba(47,107,63,0.5)"/>
    <rect x="80" y="68" width="40" height="5" rx="2.5" fill="rgba(255,255,255,0.7)"/>
    <rect x="80" y="78" width="26" height="3" rx="1.5" fill="rgba(255,255,255,0.4)"/>
    <rect x="80" y="88" width="40" height="22" rx="5" fill="rgba(255,255,255,0.07)" stroke="rgba(255,255,255,0.15)" strokeWidth="1"/>
    {/* Animated chart line */}
    <polyline
      className="illus-chart"
      points="83,105 90,98 98,101 107,95 115,99 120,93"
      stroke="rgba(74,222,128,0.9)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" fill="none"
    />
    <rect x="88" y="47" width="24" height="5" rx="2.5" fill="rgba(255,255,255,0.15)"/>
    {/* Animated WiFi signal */}
    <path className="illus-wifi-arc1" d="M136 60 Q152 50 168 60" stroke="rgba(255,255,255,0.85)" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
    <path className="illus-wifi-arc2" d="M139 67 Q152 59 165 67" stroke="rgba(255,255,255,0.9)" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
    <circle className="illus-wifi-dot" cx="152" cy="73" r="4" fill="rgba(255,255,255,0.95)"/>
  </svg>
);

const IllustrationControl = () => (
  <svg width="200" height="200" viewBox="0 0 200 200" fill="none">
    <circle cx="100" cy="100" r="88" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.08)" strokeWidth="1.5" className="ob-ring"/>
    {/* Thermometer tube */}
    <rect x="93" y="40" width="14" height="72" rx="7" fill="rgba(255,255,255,0.13)" stroke="rgba(255,255,255,0.28)" strokeWidth="1.5"/>
    {/* Animated mercury */}
    <rect className="illus-mercury" x="96" y="72" width="8" height="32" rx="4" fill="rgba(217,139,74,0.9)"/>
    <circle cx="100" cy="118" r="13" fill="rgba(217,139,74,0.9)" stroke="rgba(255,255,255,0.25)" strokeWidth="2"/>
    <line x1="89" y1="56" x2="82" y2="56" stroke="rgba(255,255,255,0.35)" strokeWidth="1.8" strokeLinecap="round"/>
    <line x1="89" y1="68" x2="85" y2="68" stroke="rgba(255,255,255,0.25)" strokeWidth="1.8" strokeLinecap="round"/>
    <line x1="89" y1="80" x2="82" y2="80" stroke="rgba(255,255,255,0.35)" strokeWidth="1.8" strokeLinecap="round"/>
    <line x1="89" y1="92" x2="85" y2="92" stroke="rgba(255,255,255,0.25)" strokeWidth="1.8" strokeLinecap="round"/>
    {/* Animated check */}
    <circle cx="148" cy="110" r="22" fill="rgba(39,174,96,0.18)" stroke="rgba(39,174,96,0.5)" strokeWidth="2"/>
    <polyline
      className="illus-check"
      points="138,110 145,117 158,103"
      stroke="rgba(74,222,128,0.95)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none"
    />
  </svg>
);

const IllustrationNotif = () => (
  <svg width="200" height="200" viewBox="0 0 200 200" fill="none">
    <circle cx="100" cy="100" r="88" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.08)" strokeWidth="1.5" className="ob-ring"/>
    {/* Animated bar chart */}
    <rect className="illus-bar1" x="44" y="118" width="20" height="38" rx="5" fill="rgba(255,255,255,0.22)"/>
    <rect className="illus-bar2" x="70" y="96"  width="20" height="60" rx="5" fill="rgba(255,255,255,0.4)"/>
    <rect className="illus-bar3" x="96" y="76"  width="20" height="80" rx="5" fill="rgba(255,255,255,0.6)"/>
    <rect className="illus-bar4" x="122" y="58" width="20" height="98" rx="5" fill="rgba(255,255,255,0.82)"/>
    {/* Trend line */}
    <path d="M44 128 Q86 98 148 62" stroke="rgba(217,139,74,0.9)" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
    <polyline points="136,55 148,62 142,74" stroke="rgba(217,139,74,0.9)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
    {/* Animated notif dot */}
    <circle className="illus-notif" cx="152" cy="52" r="8" fill="rgba(239,68,68,0.9)" stroke="rgba(255,255,255,0.4)" strokeWidth="2"/>
  </svg>
);

/* ── Slides Data ─────────────────────────────────────── */
const slides = [
  {
    title: 'Pantau Inkubator\ndari Mana Saja',
    desc: 'Monitor suhu, kelembaban, dan kondisi inkubator secara real-time langsung dari genggaman tanganmu.',
    grad: ['#163B22', '#2F6B3F', '#3D8A52'] as [string,string,string],
    Illustration: IllustrationMonitor,
  },
  {
    title: 'Kontrol Otomatis\nyang Cerdas',
    desc: 'Setelan otomatis suhu & kelembaban untuk Ayam, Puyuh, dan Bebek. Sistem yang bekerja keras untukmu.',
    grad: ['#4A2E1A', '#8A6848', '#A07850'] as [string,string,string],
    Illustration: IllustrationControl,
  },
  {
    title: 'Notifikasi Cerdas\ndi Genggamanmu',
    desc: 'Kipas, lampu, dan pelembab bisa dikontrol langsung. Notifikasi otomatis saat kondisi tidak ideal.',
    grad: ['#1A3F28', '#347045', '#3F8755'] as [string,string,string],
    Illustration: IllustrationNotif,
  },
];

/* ── Input Field ──────────────────────────────────────── */
function Field({ label, placeholder, value, onChange, Icon }: {
  label: string; placeholder: string; value: string;
  onChange: (v: string) => void; Icon: () => React.ReactElement;
}) {
  return (
    <div className="ob-fadeInUp">
      <label style={{ fontSize: 13, fontWeight: 600, color: '#3A4D3C', display: 'block', marginBottom: 6 }}>
        {label}
      </label>
      <div style={{ position: 'relative' }}>
        <span style={{ position: 'absolute', left: 13, top: '50%', transform: 'translateY(-50%)', display: 'flex', alignItems: 'center', pointerEvents: 'none' }}>
          <Icon />
        </span>
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          style={{
            width: '100%', boxSizing: 'border-box',
            padding: '13px 16px 13px 42px',
            borderRadius: 12, fontSize: 14,
            border: '1.5px solid rgba(0,0,0,0.1)',
            background: '#FFFFFF',
            color: '#1A2B1C', outline: 'none',
            fontFamily: 'inherit',
            transition: 'border-color 0.15s, box-shadow 0.15s',
          }}
          onFocus={(e) => { e.target.style.borderColor = '#2F6B3F'; e.target.style.boxShadow = '0 0 0 3px rgba(47,107,63,0.1)'; }}
          onBlur={(e) => { e.target.style.borderColor = 'rgba(0,0,0,0.1)'; e.target.style.boxShadow = 'none'; }}
        />
      </div>
    </div>
  );
}

/* ── Main Component ───────────────────────────────────── */
export function Onboarding() {
  const navigate = useNavigate();
  const { setFarmer } = useAppStore();
  const [step, setStep]   = useState(0);
  const [animKey, setAnimKey] = useState(0);
  const [form, setForm]   = useState({ name: '', farmName: '', desa: '', kabupaten: '' });
  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const isFormValid = form.name.trim() && form.farmName.trim() && form.kabupaten.trim();

  const goNext = () => { setAnimKey(k => k + 1); setStep(s => s + 1); };
  const goPrev = () => { setAnimKey(k => k + 1); setStep(s => Math.max(0, s - 1)); };
  const skipToForm = () => { setAnimKey(k => k + 1); setStep(slides.length); };
  const handleSubmit = () => {
    if (!isFormValid) return;
    setFarmer({
      name: form.name.trim(), farmName: form.farmName.trim(),
      desa: form.desa.trim() || '-', kabupaten: form.kabupaten.trim(),
      isProfileComplete: true, hasSeenOnboarding: true,
    });
    navigate('/');
  };

  // Reset body overflow for onboarding full-screen
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  /* ────────── FORM SCREEN ────────── */
  if (step === slides.length) {
    return (
      <div className="screen" style={{ background: '#FFFFFF', overflow: 'hidden' }}>
        {/* Header — clean flat */}
        <div
          className="safe-top"
          style={{
            padding: '16px 20px 0',
            background: '#FFFFFF',
          }}
        >
          <div style={{ paddingTop: 8, marginBottom: 24 }}>
            <TetascoWordmark dark />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 8 }}>
            <h1 className="ob-fadeInUp" style={{
              fontSize: 24, fontWeight: 800, color: '#1A2B1C',
              letterSpacing: -0.5, lineHeight: 1.2,
            }}>
              Kenalkan Peternakan Anda
            </h1>
            <p className="ob-fadeInUp ob-delay-1" style={{
              fontSize: 14, color: '#8A9E8C', lineHeight: 1.55,
            }}>
              Isi data berikut agar aplikasi terasa lebih personal
            </p>
          </div>
        </div>

        {/* Form body */}
        <div className="screen-scroll flex-1" style={{ padding: '16px 20px 40px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display:'flex', alignItems:'center', gap:6 }} className="ob-fadeInUp ob-delay-1">
              <div style={{ width:3, height:14, borderRadius:2, background:'#2F6B3F' }} />
              <p style={{ fontSize: 11, fontWeight: 700, color: '#8A9E8C', letterSpacing: 0.8, textTransform: 'uppercase' }}>Data Peternak</p>
            </div>
            <Field label="Nama Peternak *" placeholder="Contoh: Pak Enos" value={form.name} onChange={(v) => set('name', v)} Icon={IconPerson} />
            <Field label="Nama Peternakan *" placeholder="Contoh: Peternakan Pak Enos" value={form.farmName} onChange={(v) => set('farmName', v)} Icon={IconFarm} />

            <div style={{ height: 4 }} />

            <div style={{ display:'flex', alignItems:'center', gap:6 }} className="ob-fadeInUp ob-delay-2">
              <div style={{ width:3, height:14, borderRadius:2, background:'#2F6B3F' }} />
              <p style={{ fontSize: 11, fontWeight: 700, color: '#8A9E8C', letterSpacing: 0.8, textTransform: 'uppercase' }}>Lokasi Peternakan</p>
            </div>
            <Field label="Kabupaten / Kota *" placeholder="Contoh: Kabupaten Maros" value={form.kabupaten} onChange={(v) => set('kabupaten', v)} Icon={IconMapPin} />
            <Field label="Desa / Kelurahan" placeholder="Contoh: Desa Nisombalia" value={form.desa} onChange={(v) => set('desa', v)} Icon={IconArea} />

            <p style={{ fontSize: 11, color: '#ADADAD', marginTop: 4 }}>* wajib diisi</p>
            <div style={{ height: 24 }} />
          </div>
        </div>

        {/* CTA */}
        <div style={{
          padding: '12px 20px',
          paddingBottom: 'max(12px, env(safe-area-inset-bottom))',
          background: '#FFFFFF',
          borderTop: '1px solid rgba(0,0,0,0.06)',
        }}>
          <button className="btn-primary" onClick={handleSubmit} disabled={!isFormValid} style={{
            opacity: isFormValid ? 1 : 0.45,
            width: '100%',
          }}>
            Mulai Gunakan Tetasco Connect
          </button>
        </div>
      </div>
    );
  }

  /* ────────── SLIDE SCREENS ────────── */
  const slide = slides[step];
  const isLast = step === slides.length - 1;
  const grad = `linear-gradient(150deg, ${slide.grad[0]} 0%, ${slide.grad[1]} 55%, ${slide.grad[2]} 100%)`;

  return (
    <div
      className="screen"
      style={{ background: grad, overflow: 'hidden', position: 'relative' }}
    >
      {/* Decorative rings — always animating */}
      <div style={{
        position: 'absolute', width: 360, height: 360, borderRadius: '50%',
        border: '1.5px solid rgba(255,255,255,0.06)',
        top: -80, right: -80, pointerEvents: 'none',
      }} className="ob-ring" />
      <div style={{
        position: 'absolute', width: 240, height: 240, borderRadius: '50%',
        border: '1px solid rgba(255,255,255,0.04)',
        bottom: 40, left: -80, pointerEvents: 'none',
      }} className="ob-ring" />

      {/* Top bar: skip */}
      <div
        className="safe-top"
        style={{ padding: '16px 20px 0', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', position: 'relative', zIndex: 10 }}
      >
        <button
          onClick={skipToForm}
          style={{
            marginLeft: 'auto',
            background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.22)',
            borderRadius: 999, padding: '7px 18px',
            color: 'rgba(255,255,255,0.82)', fontSize: 13, fontWeight: 500, cursor: 'pointer',
            backdropFilter: 'blur(8px)',
          }}
        >
          Lewati
        </button>
      </div>

      {/* Illustration — floats */}
      <div
        key={`illus-${animKey}`}
        className="ob-float ob-fadeIn"
        style={{
          flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
          position: 'relative', zIndex: 5,
        }}
      >
        <slide.Illustration />
      </div>

      {/* Text content — slides in */}
      <div
        key={`text-${animKey}`}
        className="ob-slideIn"
        style={{ padding: '0 28px 0', position: 'relative', zIndex: 5 }}
      >
        <h1 style={{
          fontSize: 30, fontWeight: 700, color: '#FFFFFF',
          letterSpacing: -0.6, lineHeight: 1.2,
          whiteSpace: 'pre-line', marginBottom: 10,
        }}>
          {slide.title}
        </h1>
        <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.68)', lineHeight: 1.65 }}>
          {slide.desc}
        </p>
      </div>

      {/* Bottom controls — frosted glass card, no hard cut */}
      <div
        style={{
          padding: '20px 20px',
          paddingBottom: 'max(28px, env(safe-area-inset-bottom, 20px))',
          background: 'transparent',
          display: 'flex', flexDirection: 'column', gap: 14,
          position: 'relative', zIndex: 10,
          marginTop: 24,
        }}
      >
        {/* Progress dots */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginBottom: 4 }}>
          {slides.map((_, i) => (
            <div key={i} style={{
              height: 6, borderRadius: 3,
              width: i === step ? 22 : 6,
              background: i === step ? '#FFFFFF' : 'rgba(255,255,255,0.3)',
              transition: 'all 0.3s cubic-bezier(0.34,1.56,0.64,1)',
            }} />
          ))}
        </div>

        {/* Prev + CTA row */}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {/* Previous button — only visible when not on first slide */}
          <button
            onClick={goPrev}
            style={{
              width: step > 0 ? 52 : 0,
              height: 52, borderRadius: 16, flexShrink: 0,
              background: 'rgba(255,255,255,0.15)',
              border: '1.5px solid rgba(255,255,255,0.25)',
              color: '#FFFFFF', fontSize: 20, cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              overflow: 'hidden', padding: 0,
              opacity: step > 0 ? 1 : 0,
              transition: 'width 0.3s cubic-bezier(0.34,1.56,0.64,1), opacity 0.25s',
              backdropFilter: 'blur(8px)',
            }}
            disabled={step === 0}
            aria-label="Kembali"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M15 19l-7-7 7-7" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>

          {/* Main CTA */}
          <button
            onClick={isLast ? skipToForm : goNext}
            style={{
              flex: 1, padding: '15px 0', borderRadius: 16,
              background: '#FFFFFF',
              border: 'none', color: slide.grad[1],
              fontSize: 15, fontWeight: 700, cursor: 'pointer',
              letterSpacing: -0.2,
              boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
              transition: 'transform 0.15s, box-shadow 0.15s',
            }}
            onPointerDown={(e) => { e.currentTarget.style.transform = 'scale(0.97)'; e.currentTarget.style.boxShadow = '0 2px 10px rgba(0,0,0,0.15)'; }}
            onPointerUp={(e) => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.2)'; }}
            onPointerLeave={(e) => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.2)'; }}
          >
            {isLast ? 'Isi Data Peternakan' : 'Lanjut'}
          </button>
        </div>

        {!isLast && (
          <p
            style={{ textAlign: 'center', fontSize: 13, color: 'rgba(255,255,255,0.55)', cursor: 'pointer' }}
            onClick={skipToForm}
          >
            Lewati intro
          </p>
        )}
      </div>
    </div>
  );
}
