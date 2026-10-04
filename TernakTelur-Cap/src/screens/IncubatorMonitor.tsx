import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAppStore } from '../store/appStore';
import { IncubationPrograms, getIncubationPhase, getStatusLabel } from '../constants/incubation';
import { ProgressRing } from '../components/ProgressRing';
import {
  IconChevronLeft, IconTrash, IconThermometer, IconDroplet,
  IconFlame, IconFan, IconRefresh, IconClock, IconWifi,
} from '../components/Icons';
import { useAppStore as _useStore } from '../store/appStore';

export function IncubatorMonitor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { incubators, finishIncubation, removeIncubator } = useAppStore();
  const inc = incubators.find((i) => i.id === id);
  const [countdown, setCountdown] = useState({ d: 0, h: 0, m: 0, s: 0 });
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showCamera, setShowCamera]     = useState(false);
  const { myDevices, backendUrl }       = useAppStore();
  // Cari IP backend untuk inkubator ini (pakai backendId)
  const device   = myDevices.find(d => d.tetascoId === inc?.backendId);
  const raspiUrl = device?.serverUrl ?? backendUrl ?? null;

  useEffect(() => {
    if (!inc) return;
    const calc = () => {
      const diff = new Date(inc.estimatedHatchDate).getTime() - Date.now();
      if (diff <= 0) { setCountdown({ d: 0, h: 0, m: 0, s: 0 }); return; }
      setCountdown({ d: Math.floor(diff / 864e5), h: Math.floor(diff / 36e5) % 24, m: Math.floor(diff / 6e4) % 60, s: Math.floor(diff / 1e3) % 60 });
    };
    calc();
    const t = setInterval(calc, 1000);
    return () => clearInterval(t);
  }, [inc?.estimatedHatchDate]);

  if (!inc) return (
    <div className="screen" style={{ alignItems: 'center', justifyContent: 'center', gap: 16 }}>
      <p className="t-h4 c-text-muted">Inkubator tidak ditemukan</p>
      <button className="btn-primary" style={{ width: 'auto', padding: '10px 20px' }} onClick={() => navigate('/')}>Kembali</button>
    </div>
  );

  const prog = IncubationPrograms[inc.species];
  const phase = getIncubationPhase(inc.currentDay, inc.species);
  const tTarget = phase === 'hatching' ? prog.targetTempHatching : prog.targetTemp;
  const hTarget = phase === 'hatching' ? prog.targetHumidityHatching : prog.targetHumidity;
  const tDiff = Math.abs(inc.iotData.temperature - tTarget);
  const hDiff = Math.abs(inc.iotData.humidity - hTarget);
  const tStatus = tDiff > prog.tempTolerance * 2 ? 'danger' : tDiff > prog.tempTolerance ? 'warning' : 'normal';
  const hStatus = hDiff > prog.humidityTolerance * 2 ? 'danger' : hDiff > prog.humidityTolerance ? 'warning' : 'normal';
  const progress = inc.currentDay / prog.durationDays;
  const hatchProgress = prog.hatchingPhaseStartDay / prog.durationDays;
  const pad = (n: number) => String(n).padStart(2, '0');
  const headerGrad = inc.status === 'berbahaya' ? 'linear-gradient(135deg,#7B1E1E,#C0392B)' : inc.status === 'perlu_perhatian' ? 'linear-gradient(135deg,#6B4A1E,#D98B4A)' : 'linear-gradient(135deg,#1E4A2A,#2F6B3F)';
  const fmtTime = (d: Date) => new Date(d).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });

  const gaugeColors = {
    normal:  { val: '#2F6B3F', bg: 'linear-gradient(135deg,#EAF3EC,#F5FAF6)', border: 'rgba(47,107,63,0.15)',  iconBg: '#EAF3EC', targetBg: '#EAF3EC' },
    warning: { val: '#D98B4A', bg: 'linear-gradient(135deg,#FDF0E3,#FEF9F3)', border: 'rgba(217,139,74,0.2)', iconBg: '#FDF0E3', targetBg: '#FDF0E3' },
    danger:  { val: '#C0392B', bg: 'linear-gradient(135deg,#FDEDEB,#FEF5F4)', border: 'rgba(192,57,43,0.2)',  iconBg: '#FDEDEB', targetBg: '#FDEDEB' },
  };

  return (
    <div className="screen anim-fade-in">
      {/* Header */}
      <div style={{ background: headerGrad, padding: '8px 16px 14px', flexShrink: 0 }} className="safe-top">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <button onClick={() => navigate(-1)} style={{ background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 10, width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
            <IconChevronLeft size={22} color="rgba(255,255,255,0.9)" strokeWidth={2.2} />
          </button>
          <div style={{ display: 'flex', gap: 8 }}>
            {/* Tombol Kamera Live */}
            {raspiUrl && (
              <button
                onClick={() => setShowCamera(true)}
                style={{ background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 10, width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', fontSize: 18 }}
                title="Lihat kamera live"
              >
                🎥
              </button>
            )}
            {/* Tombol Bagikan */}
            <button
              onClick={() => navigate(`/share/${inc.id}`)}
              style={{ background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 10, width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', fontSize: 17 }}
              title="Bagikan akses lemari"
            >
              🔗
            </button>
            <button
              onClick={() => setShowDeleteModal(true)}
              style={{ background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 10, width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
            >
              <IconTrash size={17} color="rgba(255,255,255,0.85)" />
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flex: 1 }}>
            <div style={{ width: 42, height: 42, borderRadius: 10, background: 'rgba(255,255,255,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, flexShrink: 0 }}>{prog.emoji}</div>
            <div style={{ flex: 1 }}>
              <p className="t-h4 c-white" style={{ marginBottom: 2 }}>{inc.name}</p>
              <p className="t-sm" style={{ color: 'rgba(255,255,255,0.75)' }}>{prog.nameId} · {inc.totalEggs} telur</p>
            </div>
          </div>
          <span className={`badge badge-${inc.status === 'normal' ? 'normal' : inc.status === 'perlu_perhatian' ? 'warning' : 'danger'}`} style={{ fontSize: 11, flexShrink: 0 }}>
            {getStatusLabel(inc.status)}
          </span>
        </div>

        {/* Live indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div className="live-dot" />
          <IconWifi size={13} color="rgba(255,255,255,0.5)" />
          <p className="t-sm" style={{ color: 'rgba(255,255,255,0.55)' }}>Live · Diperbarui {fmtTime(inc.iotData.lastUpdated)}</p>
        </div>
      </div>

      <div className="screen-scroll flex-1">
        <div style={{ padding: '14px 14px 32px', display: 'flex', flexDirection: 'column', gap: 12 }}>

          {/* Gauge Cards */}
          <div style={{ display: 'flex', gap: 10 }}>
            {[
              { Icon: IconThermometer, label: 'Suhu', val: inc.iotData.temperature.toFixed(1), unit: '°C', target: `${tTarget.toFixed(1)}`, status: tStatus, sub: tStatus === 'normal' ? 'Optimal' : tStatus === 'warning' ? 'Perlu Perhatian' : 'Berbahaya!' },
              { Icon: IconDroplet,     label: 'Kelembaban', val: `${inc.iotData.humidity}`, unit: '%', target: `${hTarget}`, status: hStatus, sub: hStatus === 'normal' ? 'Optimal' : hStatus === 'warning' ? 'Perlu Perhatian' : 'Berbahaya!' },
            ].map((g) => {
              const gc = gaugeColors[g.status as keyof typeof gaugeColors];
              return (
                <div key={g.label} className="gauge-card" style={{ flex: 1, background: gc.bg, borderColor: gc.border }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <div className="gauge-icon-box" style={{ background: gc.iconBg }}>
                      <g.Icon size={18} color={gc.val} />
                    </div>
                    <span className="t-sm-m c-text-sec">{g.label}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: 3, marginBottom: 6 }}>
                    <span className="gauge-value" style={{ color: gc.val }}>{g.val}</span>
                    <span className="gauge-unit">{g.unit}</span>
                  </div>
                  <span className="gauge-target" style={{ background: gc.targetBg, color: gc.val }}>Target: {g.target}{g.unit}</span>
                  <p className="t-sm" style={{ color: gc.val, marginTop: 4 }}>{g.sub}</p>
                </div>
              );
            })}
          </div>

          {/* Progress */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div>
                <h3 className="t-h4 c-text" style={{ marginBottom: 4 }}>Progress Inkubasi</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 46, fontWeight: 800, color: '#2F6B3F', letterSpacing: -2, lineHeight: 1 }}>{inc.currentDay}</span>
                  <div>
                    <p className="t-sm c-text-muted">dari {prog.durationDays} hari</p>
                    <span style={{ display: 'inline-block', marginTop: 4, padding: '3px 10px', borderRadius: 999, fontSize: 11, fontWeight: 500, background: phase === 'hatching' ? '#FDF0E3' : '#EAF3EC', color: phase === 'hatching' ? '#D98B4A' : '#2F6B3F' }}>
                      {phase === 'hatching' ? 'Fase Menetas' : 'Inkubasi'}
                    </span>
                  </div>
                </div>
              </div>
              <ProgressRing progress={progress} size={90} strokeWidth={9} color={phase === 'hatching' ? '#D98B4A' : '#2F6B3F'} trackColor="#EDE9D8" label={`${Math.round(progress * 100)}%`} sublabel="selesai" />
            </div>
          </div>

          {/* Device Status */}
          <div className="card">
            <h3 className="t-h4 c-text" style={{ marginBottom: 12 }}>Status Perangkat</h3>
            <div className="device-row">
              {[
                { Icon: IconFlame,   label: 'Pemanas',    on: inc.iotData.heaterOn,    info: inc.iotData.heaterOn ? '100W' : 'Standby', color: '#D98B4A', iconBg: inc.iotData.heaterOn ? '#FDF0E3' : '#F0EDE6' },
                { Icon: IconFan,     label: 'Kipas',      on: inc.iotData.fanOn,       info: inc.iotData.fanOn ? 'Penuh' : 'Mati',     color: '#2F6B3F', iconBg: inc.iotData.fanOn ? '#EAF3EC' : '#F0EDE6' },
                { Icon: IconRefresh, label: 'Motor Balik', on: inc.iotData.motorActive, info: inc.iotData.motorActive ? 'Aktif' : fmtTime(inc.iotData.nextTurningAt), color: '#27AE60', iconBg: inc.iotData.motorActive ? '#E8F8F0' : '#F0EDE6' },
              ].map((d, i) => (
                <React.Fragment key={d.label}>
                  {i > 0 && <div className="divider-v" />}
                  <div className="device-item">
                    <div className="device-icon-bg" style={{ background: d.iconBg }}>
                      <d.Icon size={22} color={d.on ? d.color : '#C5CEC6'} />
                    </div>
                    <p className="t-sm-m c-text-sec text-center">{d.label}</p>
                    <span className="device-status-pill" style={{ background: d.on ? `${d.color}18` : '#F0EDE6', color: d.on ? d.color : '#8A9E8C' }}>{d.on ? 'ON' : 'OFF'}</span>
                    <p className="t-sm c-text-muted text-center">{d.info}</p>
                  </div>
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Timeline */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 className="t-h4 c-text">Timeline Inkubasi</h3>
              <span className="t-sm-m c-primary">Hari ke-{inc.currentDay} / {prog.durationDays}</span>
            </div>
            <div style={{ position: 'relative', marginBottom: 28 }}>
              <div className="timeline-bar">
                <div className="timeline-seg" style={{ flex: hatchProgress,     background: inc.currentDay >= 1 ? '#2F6B3F' : '#EDE9D8' }} />
                <div className="timeline-seg" style={{ flex: 1 - hatchProgress, background: inc.currentDay >= prog.hatchingPhaseStartDay ? '#D98B4A' : '#EDE9D8' }} />
              </div>
              <div style={{ position: 'absolute', top: -4, left: `${progress * 100}%`, transform: 'translateX(-50%)' }}>
                <div style={{ width: 20, height: 20, borderRadius: '50%', background: '#29332B', border: '3px solid #FFFFFF', boxShadow: '0 2px 6px rgba(0,0,0,0.15)' }} />
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-around' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}><div style={{ width: 8, height: 8, borderRadius: '50%', background: '#2F6B3F' }} /><span className="t-sm c-text-sec">Inkubasi (H1–{prog.hatchingPhaseStartDay - 1})</span></div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}><div style={{ width: 8, height: 8, borderRadius: '50%', background: '#D98B4A' }} /><span className="t-sm c-text-sec">Menetas (H{prog.hatchingPhaseStartDay}–{prog.durationDays})</span></div>
            </div>
          </div>

          {/* Countdown */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: '#EAF3EC', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 2C9.24 2 7 6.13 7 10.5C7 14.87 9.24 19 12 19c2.76 0 5-4.13 5-8.5C17 6.13 14.76 2 12 2Z" fill="#2F6B3F" opacity="0.15" stroke="#2F6B3F" strokeWidth="1.8"/><path d="M8 17.5C8 19.43 9.79 21 12 21s4-1.57 4-3.5" stroke="#2F6B3F" strokeWidth="1.8" strokeLinecap="round"/></svg>
              </div>
              <div>
                <h3 className="t-h4 c-text">Estimasi Menetas</h3>
                <p className="t-sm c-text-muted">{new Date(inc.estimatedHatchDate).toLocaleDateString('id-ID', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</p>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'center', gap: 4 }}>
              {[{ v: pad(countdown.d), l: 'Hari' }, { v: pad(countdown.h), l: 'Jam' }, { v: pad(countdown.m), l: 'Menit' }, { v: pad(countdown.s), l: 'Detik' }].map((u, i) => (
                <React.Fragment key={u.l}>
                  {i > 0 && <span className="countdown-sep">:</span>}
                  <div className="countdown-unit">
                    <div className="countdown-box"><span style={{ fontSize: 22, fontWeight: 700, color: '#2F6B3F', letterSpacing: -0.5 }}>{u.v}</span></div>
                    <span className="t-sm c-text-muted">{u.l}</span>
                  </div>
                </React.Fragment>
              ))}
            </div>
            <div style={{ marginTop: 14, textAlign: 'center' }}>
              <span style={{ background: '#EAF3EC', border: '1px solid rgba(47,107,63,0.15)', borderRadius: 999, padding: '6px 14px', fontSize: 12, fontWeight: 500, color: '#2F6B3F' }}>
                {inc.totalEggs} telur · Estimasi ~{Math.round(inc.totalEggs * 0.85)} menetas
              </span>
            </div>
          </div>

          {/* Egg Overview */}
          <div className="card">
            <h3 className="t-h4 c-text" style={{ marginBottom: 12 }}>Ringkasan Telur</h3>
            <div style={{ display: 'flex', gap: 8 }}>
              {[
                { icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><ellipse cx="12" cy="13" rx="6" ry="8" fill="#EAF3EC" stroke="#2F6B3F" strokeWidth="1.8"/></svg>, label: 'Total Telur',   val: `${inc.totalEggs}`,                      bg: '#EAF3EC', color: '#2F6B3F' },
                { icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M12 2C9.24 2 7 6.13 7 10.5C7 14.87 9.24 19 12 19c2.76 0 5-4.13 5-8.5C17 6.13 14.76 2 12 2Z" fill="#FDF0E3" stroke="#D98B4A" strokeWidth="1.8"/><path d="M9 15l3 4 3-4" stroke="#D98B4A" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>, label: 'Est. Menetas', val: `~${Math.round(inc.totalEggs * 0.85)}`, bg: '#FDF0E3', color: '#D98B4A' },
                { icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><polyline points="22,12 18,12 15,21 9,3 6,12 2,12" fill="none" stroke="#27AE60" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>, label: 'Prediksi',     val: '~85%',                                  bg: '#E8F8F0', color: '#27AE60' },
              ].map((s) => (
                <div key={s.label} style={{ flex: 1, background: s.bg, borderRadius: 12, padding: '12px 8px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                  {s.icon}
                  <span style={{ fontSize: 19, fontWeight: 700, color: s.color, letterSpacing: -0.5 }}>{s.val}</span>
                  <span className="t-sm c-text-muted text-center">{s.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Params */}
          <div className="card">
            <h3 className="t-h4 c-text" style={{ marginBottom: 12 }}>Parameter Program</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {[
                { Icon: IconThermometer, l: 'Target Suhu',        v: `${tTarget}°C` },
                { Icon: IconDroplet,     l: 'Target Kelembaban',  v: `${hTarget}%` },
                { Icon: IconRefresh,     l: 'Frekuensi Balik',    v: `Setiap ${prog.turningFrequencyHours} jam` },
                { Icon: IconFlame,       l: 'Toleransi Suhu',     v: `±${prog.tempTolerance}°C` },
                { Icon: IconClock,       l: 'Toleransi Lembab',   v: `±${prog.humidityTolerance}%` },
              ].map((p, i) => (
                <div key={p.l} style={{ display: 'flex', alignItems: 'center', gap: 12, paddingTop: i > 0 ? 10 : 0, borderTop: i > 0 ? '1px solid #EEEAD8' : 'none', paddingBottom: 10 }}>
                  <p.Icon size={16} color="#8A9E8C" />
                  <span className="t-body c-text-sec" style={{ flex: 1 }}>{p.l}</span>
                  <span style={{ background: '#EAF3EC', color: '#2F6B3F', padding: '3px 10px', borderRadius: 999, fontSize: 12, fontWeight: 600 }}>{p.v}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Hapus / Putuskan Lemari */}
          <button
            onClick={() => setShowDeleteModal(true)}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              width: '100%', padding: '14px', borderRadius: 16,
              border: '1.5px solid rgba(192,57,43,0.25)',
              background: 'rgba(192,57,43,0.06)',
              color: '#C0392B', fontSize: 14, fontWeight: 700, cursor: 'pointer',
            }}
          >
            <IconTrash size={17} color="#C0392B" />
            Putuskan &amp; Hapus Lemari Ini
          </button>

          {/* Delete Confirmation Modal */}
          {showDeleteModal && (
            <div style={{
              position: 'fixed', inset: 0, zIndex: 200,
              background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)',
              display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
              padding: '0 0 env(safe-area-inset-bottom,20px)',
            }}>
              <div style={{ background: '#FFF', borderRadius: '24px 24px 0 0', padding: '24px 20px 20px', width: '100%', maxWidth: 480 }}>
                <div style={{ textAlign: 'center', marginBottom: 20 }}>
                  <div style={{ width: 60, height: 60, borderRadius: 18, background: 'rgba(192,57,43,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 14px' }}>
                    <IconTrash size={28} color="#C0392B" />
                  </div>
                  <h3 style={{ fontSize: 18, fontWeight: 800, color: '#1A2B1C', marginBottom: 8 }}>Putuskan Lemari?</h3>
                  <p style={{ fontSize: 14, color: '#8A9E8C', lineHeight: 1.6 }}>
                    <b>{inc.name}</b> akan dilepas dari akun kamu.<br/>
                    Monitor lemari akan kembali ke layar <b>Selamat Datang</b> dan bisa disambungkan lagi nanti.
                  </p>
                </div>
                <button
                  onClick={() => { removeIncubator(id!); navigate('/'); }}
                  style={{ width: '100%', padding: '14px', borderRadius: 16, border: 'none', background: 'linear-gradient(135deg,#C0392B,#E74C3C)', color: '#FFF', fontSize: 15, fontWeight: 700, cursor: 'pointer', marginBottom: 10 }}
                >
                  🗑️ Ya, Putuskan Sekarang
                </button>
                <button
                  onClick={() => setShowDeleteModal(false)}
                  style={{ width: '100%', padding: '13px', borderRadius: 16, border: '1.5px solid rgba(0,0,0,0.08)', background: 'transparent', color: '#4A5568', fontSize: 14, cursor: 'pointer' }}
                >
                  Batal
                </button>
              </div>
            </div>
          )}

          {/* Finish Incubation */}
          <button
            className="btn-primary"
            onClick={() => { finishIncubation(id!, Math.round(inc.totalEggs * 0.85)); navigate('/'); }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><polyline points="20,6 9,17 4,12" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Selesaikan Inkubasi
          </button>
        </div>

      </div>

      {/* ── Camera Viewer Modal ── */}
      {showCamera && raspiUrl && (
      <div style={{ position: 'fixed', inset: 0, zIndex: 2000, background: '#000', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '50px 16px 12px', background: 'rgba(0,0,0,0.8)' }}>
          <div>
            <p style={{ color: '#FFF', fontSize: 15, fontWeight: 700 }}>🎥 Kamera Live</p>
            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 12 }}>{inc.name}</p>
          </div>
          <button
            onClick={() => setShowCamera(false)}
            style={{ background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 10, width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#FFF', fontSize: 18 }}
          >✕</button>
        </div>

        {/* Stream */}
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0A0A0A', overflow: 'hidden' }}>
          <img
            src={`${raspiUrl.replace(/\/$/, '')}/api/camera/stream`}
            alt="Live Stream"
            style={{ width: '100%', maxHeight: '100%', objectFit: 'contain', display: 'block' }}
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
          />
        </div>

        {/* Footer */}
        <div style={{ background: 'rgba(0,0,0,0.85)', padding: '12px 16px 32px', display: 'flex', gap: 10 }}>
          <a
            href={`${raspiUrl.replace(/\/$/, '')}/api/camera/snapshot`}
            download="snapshot.jpg"
            style={{ flex: 1, padding: '12px', borderRadius: 14, background: '#2F6B3F', color: '#FFF', fontSize: 13, fontWeight: 700, textAlign: 'center', textDecoration: 'none', display: 'block' }}
          >
            📷 Simpan Foto
          </a>
          <button
            onClick={() => setShowCamera(false)}
            style={{ flex: 1, padding: '12px', borderRadius: 14, border: '1.5px solid rgba(255,255,255,0.15)', background: 'transparent', color: 'rgba(255,255,255,0.7)', fontSize: 13, cursor: 'pointer' }}
          >
            Tutup
          </button>
        </div>
      </div>
    )}

    </div>
  );
}
