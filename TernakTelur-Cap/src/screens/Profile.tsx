import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/appStore';
import { IncubationPrograms } from '../constants/incubation';
import { fetchHealth } from '../services/api';
import { IconEdit, IconList, IconBell, IconHelpCircle, IconAbout, IconChevronRight, IconMapPin, IconPlus } from '../components/Icons';

export function Profile() {
  const navigate = useNavigate();
  const { farmer, incubators, history, backendUrl, setBackendUrl, tetascoId, setTetascoId, isConnected, startRealtime, stopRealtime, _sensorInterval } = useAppStore();
  const isRealtime = !!_sensorInterval;
  const totalHatched = history.reduce((s, h) => s + h.hatchedEggs, 0);
  const totalEggs = incubators.reduce((s, i) => s + i.totalEggs, 0) + history.reduce((s, h) => s + h.totalEggs, 0);

  const [urlInput,   setUrlInput]   = useState(backendUrl);
  const [idInput,    setIdInput]    = useState(String(tetascoId));
  const [testing,    setTesting]    = useState(false);
  const [testResult, setTestResult] = useState<'ok' | 'fail' | null>(null);

  const handleSaveUrl = () => {
    const cleaned = urlInput.trim().replace(/\/$/, '');
    setBackendUrl(cleaned);
    setUrlInput(cleaned);
    // Simpan juga tetascoId
    const parsed = parseInt(idInput.trim(), 10);
    if (!isNaN(parsed) && parsed > 0) setTetascoId(parsed);
    setTestResult(null);
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const ok = await fetchHealth(urlInput.trim().replace(/\/$/, ''));
      setTestResult(ok ? 'ok' : 'fail');
    } catch {
      setTestResult('fail');
    } finally {
      setTesting(false);
    }
  };

  const menu = [
    { icon: <IconEdit size={20} color="#2F6B3F" />, label: 'Edit Profil Peternak', action: () => navigate('/profile-setup') },
    { icon: <IconList size={20} color="#2F6B3F" />, label: 'Daftar Inkubator', action: () => navigate('/incubators') },
    { icon: <IconBell size={20} color="#2F6B3F" />, label: 'Notifikasi & Peringatan', action: () => navigate('/notifications') },
    { icon: <IconHelpCircle size={20} color="#2F6B3F" />, label: 'Bantuan & FAQ', action: () => {} },
    { icon: <IconAbout size={20} color="#2F6B3F" />, label: 'Tentang TernakTelur', action: () => {} },
  ];

  return (
    <div className="screen anim-fade-in">
      <div className="screen-scroll flex-1">
        {/* Profile Card */}
        <div className="grad-primary safe-top" style={{ padding: '28px 24px 0', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', width: 220, height: 220, borderRadius: '50%', background: 'rgba(255,255,255,0.04)', top: -70, right: -70, pointerEvents: 'none' }} />
          <div style={{ position: 'absolute', width: 160, height: 160, borderRadius: '50%', background: 'rgba(255,255,255,0.04)', bottom: -50, left: -40, pointerEvents: 'none' }} />

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, paddingBottom: 24 }}>
            <div style={{ width: 88, height: 88, borderRadius: 44, background: 'rgba(255,255,255,0.15)', border: '3px solid rgba(255,255,255,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="50" height="50" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="8" r="4" fill="rgba(255,255,255,0.9)" />
                <path d="M4 20c0-3.31 3.58-6 8-6s8 2.69 8 6" stroke="rgba(255,255,255,0.9)" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </div>
            <h1 style={{ fontSize: 24, fontWeight: 700, color: '#FFFFFF', letterSpacing: -0.5 }}>{farmer.name}</h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="rgba(255,255,255,0.85)" strokeWidth="2" strokeLinejoin="round"/><polyline points="9,22 9,12 15,12 15,22" stroke="rgba(255,255,255,0.85)" strokeWidth="2" strokeLinejoin="round"/></svg>
              <p className="t-body-m" style={{ color: 'rgba(255,255,255,0.9)' }}>{farmer.farmName}</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <IconMapPin size={14} color="rgba(255,255,255,0.75)" />
              <p className="t-sm" style={{ color: 'rgba(255,255,255,0.75)' }}>{farmer.desa}, {farmer.kecamatan}</p>
            </div>
            <p className="t-sm" style={{ color: 'rgba(255,255,255,0.6)' }}>{farmer.kabupaten} · {farmer.provinsi}</p>
          </div>

          {/* Stats strip */}
          <div className="stats-strip">
            {[
              { label: 'Inkubator', val: `${incubators.length}` },
              { label: 'Total Telur', val: `${totalEggs}` },
              { label: 'Total Menetas', val: `${totalHatched}` },
            ].map((s, i) => (
              <React.Fragment key={i}>
                {i > 0 && <div className="divider-v" />}
                <div className="stats-strip-item">
                  <span style={{ fontSize: 20, fontWeight: 700, color: '#FFFFFF', letterSpacing: -0.5 }}>{s.val}</span>
                  <span className="t-sm" style={{ color: 'rgba(255,255,255,0.7)' }}>{s.label}</span>
                </div>
              </React.Fragment>
            ))}
          </div>
        </div>

        <div style={{ padding: '20px 16px 32px', display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Registered Incubators */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <h2 className="t-h4 c-text">Inkubator Terdaftar</h2>
              <button className="btn-ghost" style={{ padding: '4px 8px', display: 'flex', alignItems: 'center', gap: 4 }} onClick={() => navigate('/incubator/egg-select')}>
                <IconPlus size={14} color="#2F6B3F" />
                <span className="t-sm-m c-primary">Tambah</span>
              </button>
            </div>
            {incubators.length === 0 ? (
              <p className="t-body c-text-muted">Belum ada inkubator yang terdaftar.</p>
            ) : (
              <div className="list">
                {incubators.map((inc) => {
                  const prog = IncubationPrograms[inc.species];
                  const dotColor = inc.status === 'normal' ? '#27AE60' : inc.status === 'perlu_perhatian' ? '#D98B4A' : '#C0392B';
                  return (
                    <div key={inc.id} className="card" style={{ padding: '12px 14px', display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{ width: 40, height: 40, borderRadius: 10, background: prog.bgColor, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20 }}>{prog.emoji}</div>
                      <div style={{ flex: 1 }}>
                        <p className="t-body-m c-text">{inc.name}</p>
                        <p className="t-sm c-text-muted">{prog.nameId} · Hari ke-{inc.currentDay}/{prog.durationDays}</p>
                      </div>
                      <div style={{ width: 10, height: 10, borderRadius: '50%', background: dotColor, flexShrink: 0 }} />
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* ── Pengaturan Jaringan ─────────────────────────────── */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <div style={{ width: 3, height: 16, borderRadius: 2, background: 'linear-gradient(to bottom,#2F6B3F,#3D8A52)' }} />
              <h2 className="t-h4 c-text">Pengaturan Jaringan</h2>
              {/* Status koneksi */}
              <div style={{
                marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 5,
                fontSize: 11, fontWeight: 700,
                color: isConnected ? '#15803D' : '#B91C1C',
              }}>
                <div style={{
                  width: 7, height: 7, borderRadius: '50%',
                  background: isConnected ? '#22C55E' : '#EF4444',
                  boxShadow: isConnected ? '0 0 6px #22C55E' : 'none',
                }} />
                {isConnected ? 'Terhubung' : 'Tidak Terhubung'}
              </div>
            </div>

            <div style={{
              background: '#FFFFFF', borderRadius: 18,
              border: '1.5px solid rgba(0,0,0,0.07)',
              boxShadow: '0 2px 10px rgba(0,0,0,0.05)',
              padding: '16px',
              display: 'flex', flexDirection: 'column', gap: 12,
            }}>
              <div>
                <label style={{ fontSize: 11, fontWeight: 700, color: '#8A9E8C', display: 'block', marginBottom: 6, letterSpacing: 0.3 }}>
                  URL BACKEND (IP RASPBERRY PI)
                </label>
                <input
                  value={urlInput}
                  onChange={e => { setUrlInput(e.target.value); setTestResult(null); }}
                  placeholder="http://192.168.1.35:8000"
                  style={{
                    width: '100%', padding: '12px 14px', borderRadius: 12,
                    border: `1.5px solid ${testResult === 'fail' ? '#FCA5A5' : testResult === 'ok' ? '#86EFAC' : 'rgba(0,0,0,0.1)'}`,
                    background: '#F8F9FA', fontSize: 14, color: '#1A2B1C',
                    fontFamily: 'monospace', outline: 'none', boxSizing: 'border-box',
                    transition: 'border-color 0.2s',
                  }}
                />
                {testResult === 'ok' && (
                  <p style={{ fontSize: 12, color: '#15803D', marginTop: 5, fontWeight: 600 }}>✓ Berhasil terhubung ke backend!</p>
                )}
                {testResult === 'fail' && (
                  <p style={{ fontSize: 12, color: '#B91C1C', marginTop: 5, fontWeight: 600 }}>✗ Gagal — pastikan Pi menyala & IP benar</p>
                )}
              </div>

              {/* Tetasco ID */}
              <div>
                <label style={{ fontSize: 11, fontWeight: 700, color: '#8A9E8C', display: 'block', marginBottom: 6, letterSpacing: 0.3 }}>
                  TETASCO ID (ID INKUBATOR DI DATABASE)
                </label>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <input
                    value={idInput}
                    onChange={e => setIdInput(e.target.value.replace(/\D/g, ''))}
                    placeholder="1"
                    inputMode="numeric"
                    style={{
                      flex: 1, padding: '12px 14px', borderRadius: 12,
                      border: '1.5px solid rgba(0,0,0,0.1)',
                      background: '#F8F9FA', fontSize: 14, color: '#1A2B1C',
                      fontFamily: 'monospace', outline: 'none', boxSizing: 'border-box' as const,
                    }}
                  />
                  <div style={{
                    padding: '10px 14px', borderRadius: 12,
                    background: '#EAF3EC', border: '1.5px solid rgba(47,107,63,0.15)',
                    fontSize: 12, fontWeight: 700, color: '#2F6B3F',
                    whiteSpace: 'nowrap',
                  }}>
                    ID aktif: <b>{tetascoId}</b>
                  </div>
                </div>
                <p style={{ fontSize: 11, color: '#A0AEC0', marginTop: 5 }}>
                  Sesuaikan dengan kolom <code style={{ background: '#F3F4F6', padding: '1px 5px', borderRadius: 4 }}>id</code> di tabel <code style={{ background: '#F3F4F6', padding: '1px 5px', borderRadius: 4 }}>tetasco</code> PostgreSQL.
                </p>
              </div>

              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  onClick={handleTest}
                  disabled={testing}
                  style={{
                    flex: 1, padding: '11px', borderRadius: 12,
                    background: testing ? '#F3F4F6' : '#EAF3EC',
                    border: '1.5px solid rgba(47,107,63,0.15)',
                    color: testing ? '#9CA3AF' : '#2F6B3F',
                    fontSize: 13, fontWeight: 700,
                    cursor: testing ? 'not-allowed' : 'pointer',
                    transition: 'all 0.15s',
                  }}
                >
                  {testing ? 'Mengecek…' : '⚡ Tes Koneksi'}
                </button>
                <button
                  onClick={handleSaveUrl}
                  disabled={urlInput.trim().replace(/\/$/, '') === backendUrl}
                  style={{
                    flex: 1, padding: '11px', borderRadius: 12,
                    background: urlInput.trim().replace(/\/$/, '') === backendUrl
                      ? '#F3F4F6'
                      : 'linear-gradient(135deg,#2F6B3F,#3D8A52)',
                    border: 'none',
                    color: urlInput.trim().replace(/\/$/, '') === backendUrl ? '#9CA3AF' : '#FFFFFF',
                    fontSize: 13, fontWeight: 700,
                    cursor: urlInput.trim().replace(/\/$/, '') === backendUrl ? 'not-allowed' : 'pointer',
                    boxShadow: urlInput.trim().replace(/\/$/, '') === backendUrl ? 'none' : '0 4px 12px rgba(47,107,63,0.3)',
                    transition: 'all 0.15s',
                  }}
                >
                  Simpan
                </button>
              </div>

              <p style={{ fontSize: 11, color: '#A0AEC0', textAlign: 'center', lineHeight: 1.6 }}>
                Pastikan perangkat terhubung ke internet.{"\n"}
                Base URL: <span style={{ fontFamily: 'monospace', color: '#8A9E8C' }}>https://tetasco.my.id</span>
              </p>
            </div>
          </div>

          {/* Settings Menu */}
          <div>
            <h2 className="t-h4 c-text" style={{ marginBottom: 10 }}>Pengaturan</h2>
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              {menu.map((item, idx) => (
                <React.Fragment key={item.label}>
                  <button className="menu-item w-full" onClick={item.action} style={{ textAlign: 'left' }}>
                    <div style={{ width: 36, height: 36, borderRadius: 10, background: '#EAF3EC', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      {item.icon}
                    </div>
                    <span className="t-body-m c-text" style={{ flex: 1 }}>{item.label}</span>
                    <IconChevronRight size={18} color="#C5CEC6" />
                  </button>
                  {idx < menu.length - 1 && <div className="divider" style={{ marginLeft: 66 }} />}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* App info */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, paddingTop: 8 }}>
            <div style={{ width: 52, height: 52, borderRadius: 16, background: 'linear-gradient(135deg,#2F6B3F,#3D8A52)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none"><ellipse cx="12" cy="13" rx="6" ry="8" fill="rgba(255,255,255,0.9)"/><circle cx="12" cy="13" r="3" fill="#2F6B3F"/></svg>
            </div>
            <p className="t-sm-m c-text-muted">TernakTelur v1.0.0</p>
            <p className="t-sm" style={{ color: '#ADADAD' }}>Dibuat untuk peternak Indonesia</p>
          </div>
        </div>
      </div>
    </div>
  );
}
