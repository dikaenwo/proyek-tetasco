import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/appStore';

/* ── Step data ───────────────────────────────────────── */
const STEPS = [
  { title: 'Data Peternak',       sub: 'Isi data berikut agar aplikasi terasa lebih personal' },
  { title: 'Lokasi Peternakan',   sub: 'Masukkan lokasi peternakan Anda' },
  { title: 'Konfirmasi Profil',   sub: 'Pastikan data Anda sudah benar' },
];

/* ── Icon SVGs ───────────────────────────────────────── */
const UserIcon = ({ size = 20, color = '#8A9E8C' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="8" r="4" stroke={color} strokeWidth="1.8"/>
    <path d="M4 20c0-3.31 3.58-6 8-6s8 2.69 8 6" stroke={color} strokeWidth="1.8" strokeLinecap="round"/>
  </svg>
);

const HomeIcon = ({ size = 20, color = '#8A9E8C' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke={color} strokeWidth="1.8" strokeLinejoin="round"/>
    <polyline points="9,22 9,12 15,12 15,22" stroke={color} strokeWidth="1.8" strokeLinejoin="round"/>
  </svg>
);

const MapPinIcon = ({ size = 20, color = '#8A9E8C' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0Z" stroke={color} strokeWidth="1.8"/>
    <circle cx="12" cy="10" r="3" stroke={color} strokeWidth="1.8"/>
  </svg>
);

const BuildingIcon = ({ size = 20, color = '#8A9E8C' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <rect x="4" y="2" width="16" height="20" rx="2" stroke={color} strokeWidth="1.8"/>
    <line x1="9" y1="6" x2="9" y2="6.01" stroke={color} strokeWidth="2.5" strokeLinecap="round"/>
    <line x1="15" y1="6" x2="15" y2="6.01" stroke={color} strokeWidth="2.5" strokeLinecap="round"/>
    <line x1="9" y1="10" x2="9" y2="10.01" stroke={color} strokeWidth="2.5" strokeLinecap="round"/>
    <line x1="15" y1="10" x2="15" y2="10.01" stroke={color} strokeWidth="2.5" strokeLinecap="round"/>
    <rect x="9" y="16" width="6" height="6" rx="1" stroke={color} strokeWidth="1.8"/>
  </svg>
);

const GlobeIcon = ({ size = 20, color = '#8A9E8C' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="10" stroke={color} strokeWidth="1.8"/>
    <ellipse cx="12" cy="12" rx="4" ry="10" stroke={color} strokeWidth="1.8"/>
    <line x1="2" y1="12" x2="22" y2="12" stroke={color} strokeWidth="1.8"/>
  </svg>
);

const CheckIcon = ({ size = 20, color = '#2F6B3F' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="10" stroke={color} strokeWidth="1.8"/>
    <polyline points="9,12 11,14 15,10" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const ChevronLeftIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
    <polyline points="15,18 9,12 15,6" stroke="#4A5568" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

/* ── Input Field ─────────────────────────────────────── */
function InputField({ icon, label, placeholder, value, onChange, required = true }: {
  icon: React.ReactNode; label: string; placeholder: string;
  value: string; onChange: (v: string) => void; required?: boolean;
}) {
  const [focused, setFocused] = useState(false);
  return (
    <div>
      <label style={{
        fontSize: 13, fontWeight: 600, color: '#1A2B1C',
        display: 'flex', alignItems: 'center', gap: 4,
        marginBottom: 8,
      }}>
        {label}
        {required && <span style={{ color: '#EF4444', fontSize: 14 }}>*</span>}
      </label>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '0 16px',
        height: 52, borderRadius: 14,
        background: focused ? '#FFFFFF' : '#F8F9FA',
        border: `1.5px solid ${focused ? '#2F6B3F' : 'rgba(0,0,0,0.08)'}`,
        transition: 'all 0.2s',
        boxShadow: focused ? '0 0 0 3px rgba(47,107,63,0.08)' : 'none',
      }}>
        <div style={{ flexShrink: 0, opacity: focused ? 1 : 0.6, transition: 'opacity 0.2s' }}>
          {icon}
        </div>
        <input
          value={value}
          onChange={e => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={placeholder}
          style={{
            flex: 1, border: 'none', background: 'transparent',
            fontSize: 14, color: '#1A2B1C', outline: 'none',
            fontFamily: 'inherit', height: '100%',
          }}
        />
      </div>
    </div>
  );
}

/* ── Section Divider ─────────────────────────────────── */
function SectionLabel({ children }: { children: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8 }}>
      <div style={{ width: 3, height: 14, borderRadius: 2, background: '#2F6B3F' }} />
      <p style={{ fontSize: 11, fontWeight: 700, color: '#8A9E8C', letterSpacing: 0.8, textTransform: 'uppercase' }}>{children}</p>
    </div>
  );
}

/* ── Main Component ──────────────────────────────────── */
export function ProfileSetup() {
  const navigate = useNavigate();
  const { farmer, setFarmer } = useAppStore();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    name: farmer.name, farmName: farmer.farmName,
    desa: farmer.desa, kecamatan: farmer.kecamatan,
    kabupaten: farmer.kabupaten, provinsi: farmer.provinsi,
  });

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));
  const canProceed = () =>
    step === 0 ? form.name.trim() && form.farmName.trim()
    : step === 1 ? form.kabupaten.trim()
    : true;

  const handleNext = () => {
    if (step < 2) { setStep(step + 1); return; }
    setFarmer({ ...form, isProfileComplete: true });
    navigate('/');
  };

  const s = STEPS[step];

  return (
    <div className="screen" style={{ background: '#FFFFFF' }}>
      {/* ── Top Bar ── */}
      <div style={{
        paddingTop: 'env(safe-area-inset-top, 44px)',
        padding: '12px 16px 0',
        background: '#FFFFFF',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, paddingTop: 8 }}>
          <button
            onClick={() => step > 0 ? setStep(step - 1) : navigate(-1)}
            style={{
              width: 40, height: 40, borderRadius: 12,
              background: '#F2F4F6', border: '1px solid rgba(0,0,0,0.06)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer', flexShrink: 0,
              transition: 'all 0.15s',
            }}
          >
            <ChevronLeftIcon />
          </button>
          <div style={{ flex: 1 }}>
            {/* Step dots */}
            <div style={{ display: 'flex', gap: 6, marginBottom: 6 }}>
              {STEPS.map((_, i) => (
                <div key={i} style={{
                  height: 4, borderRadius: 2, flex: 1,
                  background: i <= step ? '#2F6B3F' : '#E5E7EB',
                  transition: 'background 0.3s',
                }} />
              ))}
            </div>
            <p style={{ fontSize: 11, color: '#8A9E8C', fontWeight: 500 }}>
              Langkah {step + 1} dari {STEPS.length}
            </p>
          </div>
        </div>
      </div>

      {/* ── Title Section ── */}
      <div style={{ padding: '24px 20px 8px' }}>
        <h1 style={{
          fontSize: 24, fontWeight: 800, color: '#1A2B1C',
          letterSpacing: -0.5, lineHeight: 1.2, marginBottom: 6,
        }}>
          {s.title}
        </h1>
        <p style={{ fontSize: 14, color: '#8A9E8C', lineHeight: 1.5 }}>
          {s.sub}
        </p>
      </div>

      {/* ── Body ── */}
      <div className="screen-scroll flex-1" style={{ padding: '16px 20px' }}>

        {step === 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <SectionLabel>Data Peternak</SectionLabel>
            <InputField
              icon={<UserIcon size={20} color="#2F6B3F" />}
              label="Nama Peternak"
              placeholder="Contoh: Pak Andi"
              value={form.name}
              onChange={v => set('name', v)}
            />
            <InputField
              icon={<HomeIcon size={20} color="#2F6B3F" />}
              label="Nama Peternakan"
              placeholder="Contoh: Peternakan Pak Andi"
              value={form.farmName}
              onChange={v => set('farmName', v)}
            />
          </div>
        )}

        {step === 1 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <SectionLabel>Lokasi Peternakan</SectionLabel>
            <InputField
              icon={<BuildingIcon size={20} color="#2F6B3F" />}
              label="Kabupaten / Kota"
              placeholder="Contoh: Kabupaten Maros"
              value={form.kabupaten}
              onChange={v => set('kabupaten', v)}
            />
            <InputField
              icon={<MapPinIcon size={20} color="#2F6B3F" />}
              label="Desa / Kelurahan"
              placeholder="Contoh: Desa Nisombalia"
              value={form.desa}
              onChange={v => set('desa', v)}
              required={false}
            />
            <InputField
              icon={<MapPinIcon size={20} color="#2F6B3F" />}
              label="Kecamatan"
              placeholder="Contoh: Mandai"
              value={form.kecamatan}
              onChange={v => set('kecamatan', v)}
              required={false}
            />
            <InputField
              icon={<GlobeIcon size={20} color="#2F6B3F" />}
              label="Provinsi"
              placeholder="Contoh: Sulawesi Selatan"
              value={form.provinsi}
              onChange={v => set('provinsi', v)}
              required={false}
            />
          </div>
        )}

        {step === 2 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <SectionLabel>Pratinjau Profil</SectionLabel>

            {/* Preview card */}
            <div style={{
              borderRadius: 20, overflow: 'hidden',
              border: '1.5px solid rgba(47,107,63,0.15)',
              boxShadow: '0 4px 20px rgba(47,107,63,0.08)',
            }}>
              {/* Top area */}
              <div style={{
                background: 'linear-gradient(135deg, #F0FDF4, #DCFCE7)',
                padding: '28px 24px',
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10,
              }}>
                {/* Avatar */}
                <div style={{
                  width: 72, height: 72, borderRadius: 36,
                  background: '#FFFFFF',
                  border: '3px solid rgba(47,107,63,0.2)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  boxShadow: '0 4px 12px rgba(47,107,63,0.12)',
                }}>
                  <UserIcon size={36} color="#2F6B3F" />
                </div>
                <h2 style={{
                  fontSize: 20, fontWeight: 700, color: '#1A2B1C',
                  textAlign: 'center', letterSpacing: -0.3,
                }}>
                  {form.name || 'Nama Peternak'}
                </h2>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <HomeIcon size={14} color="#2F6B3F" />
                  <p style={{ fontSize: 13, color: '#2F6B3F', fontWeight: 500 }}>
                    {form.farmName || 'Nama Peternakan'}
                  </p>
                </div>
              </div>

              {/* Bottom details */}
              <div style={{ padding: '16px 24px 20px', background: '#FFFFFF' }}>
                {form.kabupaten && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0' }}>
                    <MapPinIcon size={16} color="#8A9E8C" />
                    <p style={{ fontSize: 13, color: '#4A5568' }}>
                      {[form.desa, form.kecamatan, form.kabupaten].filter(Boolean).join(', ')}
                    </p>
                  </div>
                )}
                {form.provinsi && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0' }}>
                    <GlobeIcon size={16} color="#8A9E8C" />
                    <p style={{ fontSize: 13, color: '#4A5568' }}>{form.provinsi}</p>
                  </div>
                )}
              </div>
            </div>

            <div style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '12px 16px', borderRadius: 14,
              background: 'rgba(47,107,63,0.06)',
              border: '1px solid rgba(47,107,63,0.12)',
            }}>
              <CheckIcon size={18} color="#2F6B3F" />
              <p style={{ fontSize: 12, color: '#2F6B3F', lineHeight: 1.5 }}>
                Profil ini akan tampil di beranda aplikasi Anda
              </p>
            </div>
          </div>
        )}

        <div style={{ height: 32 }} />
      </div>

      {/* ── CTA ── */}
      <div style={{
        padding: '12px 20px',
        paddingBottom: 'max(12px, env(safe-area-inset-bottom))',
        background: '#FFFFFF',
        borderTop: '1px solid rgba(0,0,0,0.06)',
      }}>
        <button
          onClick={handleNext}
          disabled={!canProceed()}
          style={{
            width: '100%', padding: '16px 0', borderRadius: 16,
            background: canProceed()
              ? 'linear-gradient(135deg, #2F6B3F, #3D8A52)'
              : '#E2E8F0',
            border: 'none',
            color: canProceed() ? '#FFFFFF' : '#A0AEC0',
            fontSize: 15, fontWeight: 700,
            cursor: canProceed() ? 'pointer' : 'not-allowed',
            boxShadow: canProceed() ? '0 6px 20px rgba(47,107,63,0.3)' : 'none',
            transition: 'all 0.2s',
            letterSpacing: -0.2,
          }}
        >
          {step === 2 ? 'Mulai Gunakan TernakTelur' : 'Lanjutkan'}
        </button>
      </div>
    </div>
  );
}
