/**
 * AddDevice.tsx — Tambah & Setup Lemari IoT
 *
 * Flow:
 *  0. Pilih: Scan Kamera (live QR) atau Ketik Kode Manual
 *  1. Input kode QR dari monitor HDMI lemari
 *  2. Konfirmasi lemari
 *  3. Setup: nama lemari + pilih jenis telur + jumlah telur
 *  4. Selesai → lemari aktif di dashboard
 */
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate }   from 'react-router-dom';
import { useAppStore }   from '../store/appStore';
import { EggSpecies, IncubationPrograms } from '../constants/incubation';
import {
  claimDevice,
  fetchAllDevices,
  type DeviceInfo,
} from '../services/api';
import jsQR from 'jsqr';

// ── Icons ────────────────────────────────────────────────────────
const IconQR    = ({ s = 24 }: { s?: number }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
    <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
    <rect x="3" y="14" width="7" height="7" rx="1"/>
    <path d="M14 14h.01M18 14h.01M14 18h.01M18 18h.01M16 16v.01"/>
  </svg>
);
const IconCamera = ({ s = 24 }: { s?: number }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
    <circle cx="12" cy="13" r="4"/>
  </svg>
);
const IconSearch = ({ s = 24 }: { s?: number }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
  </svg>
);
const IconCheck = ({ s = 20, c = '#22C55E' }: { s?: number; c?: string }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2.5" strokeLinecap="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
);
const IconBack = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <path d="M19 12H5M12 5l-7 7 7 7"/>
  </svg>
);
const IconClose = ({ s = 20 }: { s?: number }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <path d="M18 6L6 18M6 6l12 12"/>
  </svg>
);
const IconWifi = ({ s = 20, c = 'currentColor' }: { s?: number; c?: string }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round">
    <path d="M5 12.55a11 11 0 0114.08 0"/><path d="M1.42 9a16 16 0 0121.16 0"/>
    <path d="M8.53 16.11a6 6 0 016.95 0"/><circle cx="12" cy="20" r="1" fill={c} stroke="none"/>
  </svg>
);

// ── Species config ───────────────────────────────────────────────
const SPECIES_LIST: { key: EggSpecies; emoji: string; name: string; days: number }[] = [
  { key: 'ayam',  emoji: '🐔', name: 'Ayam',  days: 21 },
  { key: 'bebek', emoji: '🦆', name: 'Bebek', days: 28 },
  { key: 'puyuh', emoji: '🪶', name: 'Puyuh', days: 17 },
  { key: 'angsa', emoji: '🦢', name: 'Angsa', days: 30 },
];

// ── Shared styles ────────────────────────────────────────────────
const labelStyle: React.CSSProperties = { fontSize: 12, fontWeight: 600, color: '#4A5568', display: 'block', marginBottom: 6 };
const errStyle: React.CSSProperties   = { fontSize: 12, color: '#991B1B', marginTop: 8 };
const inputStyle: React.CSSProperties = { width: '100%', padding: '12px 14px', borderRadius: 12, border: '1.5px solid rgba(0,0,0,0.1)', background: '#F8F9FA', fontSize: 14, outline: 'none', boxSizing: 'border-box', color: '#1A2B1C' };
const btnPrimary: React.CSSProperties = { width: '100%', padding: '14px', borderRadius: 16, border: 'none', background: 'linear-gradient(135deg,#2F6B3F,#3D8A52)', color: '#FFF', fontSize: 14, fontWeight: 700, cursor: 'pointer', display: 'block', marginTop: 16 };
const btnGhost: React.CSSProperties   = { width: '100%', padding: '12px', borderRadius: 12, border: '1.5px solid rgba(0,0,0,0.08)', background: 'transparent', color: '#4A5568', fontSize: 14, cursor: 'pointer', marginTop: 8, display: 'block' };

// ─────────────────────────────────────────────────────────────────
// QR dari Foto (file input) — works on Android Capacitor
// ─────────────────────────────────────────────────────────────────
function decodeQRFromFile(file: File): Promise<string | null> {
  return new Promise((resolve) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d')!;
      ctx.drawImage(img, 0, 0);
      const data = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const code = jsQR(data.data, data.width, data.height, { inversionAttempts: 'attemptBoth' });
      URL.revokeObjectURL(url);
      resolve(code?.data ?? null);
    };
    img.onerror = () => { URL.revokeObjectURL(url); resolve(null); };
    img.src = url;
  });
}

// ─────────────────────────────────────────────────────────────────
// Live QR Camera Scanner (untuk Web — Android pakai file input)
// ─────────────────────────────────────────────────────────────────
function QRScanner({ onScan, onClose }: { onScan: (result: string) => void; onClose: () => void }) {
  const videoRef  = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const rafRef    = useRef<number>(0);
  const [camErr, setCamErr] = useState('');
  const [scanning, setScanning] = useState(true);

  useEffect(() => {
    let stopped = false;

    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
        });
        if (stopped) { stream.getTracks().forEach(t => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play();
        }
      } catch {
        setCamErr('CAMERA_UNAVAILABLE');
      }
    };

    startCamera();

    return () => {
      stopped = true;
      cancelAnimationFrame(rafRef.current);
      streamRef.current?.getTracks().forEach(t => t.stop());
    };
  }, []);

  const handleVideoPlay = () => {
    const tick = () => {
      const video  = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas || video.readyState !== video.HAVE_ENOUGH_DATA) {
        rafRef.current = requestAnimationFrame(tick);
        return;
      }
      // Scale up untuk resolusi lebih baik (minimum 640px)
      const scale  = Math.max(1, 640 / video.videoWidth);
      canvas.width  = video.videoWidth  * scale;
      canvas.height = video.videoHeight * scale;
      const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const code = jsQR(imageData.data, imageData.width, imageData.height, {
        inversionAttempts: 'attemptBoth',  // Decode QR normal & inverted (LCD dark background)
      });
      if (code?.data) {
        setScanning(false);
        streamRef.current?.getTracks().forEach(t => t.stop());
        onScan(code.data);
        return;
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  };

  // Kamera tidak tersedia (Capacitor Android) — tampilkan tombol foto
  if (camErr === 'CAMERA_UNAVAILABLE') {
    return (
      <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: '#1A1A2E', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 32 }}>
        <div style={{ textAlign: 'center', color: '#FFF', marginBottom: 32 }}>
          <div style={{ fontSize: 64, marginBottom: 16 }}>📷</div>
          <h2 style={{ fontSize: 20, fontWeight: 800, marginBottom: 8 }}>Foto QR Code</h2>
          <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.6)', lineHeight: 1.6 }}>
            Arahkan kamera ke QR Code di monitor lemari,<br/>lalu ambil foto untuk scan otomatis.
          </p>
        </div>
        <label style={{ width: '100%', maxWidth: 320 }}>
          <div style={{ width: '100%', padding: '18px', borderRadius: 18, background: 'linear-gradient(135deg,#2F6B3F,#3D8A52)', color: '#FFF', fontSize: 16, fontWeight: 700, textAlign: 'center', cursor: 'pointer' }}>
            📸 Buka Kamera & Foto QR
          </div>
          <input type="file" accept="image/*" capture="environment" style={{ display: 'none' }}
            onChange={async (e) => {
              const file = e.target.files?.[0];
              e.target.value = '';
              if (!file) return;
              const result = await decodeQRFromFile(file);
              if (result) { onScan(result); }
              else { setCamErr('QR tidak terbaca. Coba foto lebih dekat, pastikan QR terlihat jelas.'); }
            }}
          />
        </label>
        <button onClick={onClose} style={{ marginTop: 16, background: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 12, color: 'rgba(255,255,255,0.7)', padding: '12px 24px', fontSize: 14, cursor: 'pointer' }}>Batal</button>
        {camErr !== 'CAMERA_UNAVAILABLE' && <p style={{ color: '#FCA5A5', marginTop: 12, fontSize: 13 }}>{camErr}</p>}
      </div>
    );
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: '#000', display: 'flex', flexDirection: 'column',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '50px 16px 16px', background: 'rgba(0,0,0,0.8)' }}>
        <p style={{ color: '#FFF', fontSize: 16, fontWeight: 700 }}>Scan QR Monitor Lemari</p>
        <button onClick={onClose} style={{ background: 'rgba(255,255,255,0.15)', border: 'none', borderRadius: 10, width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
          <IconClose s={18} />
        </button>
      </div>

      {/* Camera view */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <video
          ref={videoRef}
          onPlay={handleVideoPlay}
          playsInline muted autoPlay
          style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
        />
        {/* Overlay */}
        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
          <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.5)' }} />
          <div style={{
            position: 'relative', width: 260, height: 260,
            border: '3px solid ' + (scanning ? '#52C97F' : '#FFD700'),
            borderRadius: 20,
            boxShadow: `0 0 0 9999px rgba(0,0,0,0.5)`,
          }}>
            {scanning && (
              <div style={{ position: 'absolute', left: 4, right: 4, height: 3, background: 'linear-gradient(90deg,transparent,#52C97F,transparent)', animation: 'scanline 2s ease-in-out infinite', borderRadius: 3 }}/>
            )}
            {[{top:0,left:0},{top:0,right:0},{bottom:0,left:0},{bottom:0,right:0}].map((pos, i) => (
              <div key={i} style={{ position: 'absolute', width: 24, height: 24, borderTop: i<2?'4px solid #52C97F':'none', borderBottom: i>=2?'4px solid #52C97F':'none', borderLeft: i%2===0?'4px solid #52C97F':'none', borderRight: i%2!==0?'4px solid #52C97F':'none', borderRadius: i===0?'12px 0 0 0':i===1?'0 12px 0 0':i===2?'0 0 0 12px':'0 0 12px 0', ...pos }}/>
            ))}
          </div>
        </div>
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </div>

      <div style={{ background: 'rgba(0,0,0,0.85)', padding: '16px 20px 40px', textAlign: 'center' }}>
        <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 13 }}>
          Arahkan kamera ke <b style={{ color: '#52C97F' }}>QR Code di monitor lemari</b>
        </p>
      </div>

      <style>{`@keyframes scanline { 0%, 100% { top: 8px; } 50% { top: calc(100% - 12px); } }`}</style>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// QR Input Tab — 4 step flow
// ─────────────────────────────────────────────────────────────────
function QRInputTab() {
  const navigate = useNavigate();
  const { backendUrl, appId, addMyDevice, addIncubator, syncMyDevices } = useAppStore();
  const [code, setCode]         = useState('');
  const [step, setStep]         = useState<0|1|2|3|4>(0); // 4 = joined (share)
  const [parsed, setParsed]     = useState<{ id: number; token: string } | null>(null);
  const [shareData, setShareData] = useState<{id:number;tok:string;nm:string;sv:string} | null>(null);
  const [errMsg, setErrMsg]     = useState('');
  const [loading, setLoading]   = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [joinedInfo, setJoinedInfo] = useState<{name:string;tetascoId:number} | null>(null);

  // Setup state
  const [lemariName, setLemariName] = useState('');
  const [species, setSpecies]       = useState<EggSpecies>('ayam');
  const [eggCount, setEggCount]     = useState('48');


  // ── Parse QR — support pairing QR dan share QR ────────────────
  const parseQR = (raw: string): { type: 'claim'; id: number; token: string } | { type: 'share'; id: number; tok: string; nm: string; sv: string } | null => {
    const s = raw.trim();
    // Share QR — JSON payload
    try {
      const obj = JSON.parse(s);
      if (obj.t === 'share' && obj.id && obj.tok) {
        return { type: 'share', id: obj.id, tok: obj.tok, nm: obj.nm ?? `Lemari #${obj.id}`, sv: obj.sv ?? 'https://tetasco.my.id' };
      }
    } catch { /* bukan JSON */ }
    // Pairing QR — tetasco://claim?id=X&token=Y
    if (s.startsWith('tetasco://') || s.startsWith('https://tetasco')) {
      try {
        const url = new URL(s.replace('tetasco://', 'https://tetasco.my.id/'));
        const id  = parseInt(url.searchParams.get('id') ?? '');
        const tok = url.searchParams.get('token') ?? '';
        if (id && tok) return { type: 'claim', id, token: tok.toUpperCase() };
      } catch { /* */ }
    }
    if (s.includes(':')) {
      const [a, b] = s.split(':');
      const id = parseInt(a);
      if (id && b) return { type: 'claim', id, token: b.toUpperCase() };
    }
    return null;
  };

  // ── Handle scan result ─────────────────────────────────────────
  const handleScanResult = (raw: string) => {
    setShowCamera(false);
    const p = parseQR(raw);
    if (!p) { setErrMsg('QR tidak dikenal. Scan QR dari monitor lemari atau QR Berbagi.'); return; }
    if (p.type === 'share') {
      setShareData(p);
      setStep(1); setErrMsg('');
    } else {
      setParsed({ id: p.id, token: p.token });
      setLemariName(`Lemari #${p.id}`);
      setStep(1); setErrMsg('');
    }
  };


  const handleManualScan = () => {
    const p = parseQR(code);
    if (!p) { setErrMsg('Format tidak dikenal. Salin kode dari monitor lemari.'); return; }
    if (p.type === 'share') {
      setShareData(p); setStep(1); setErrMsg('');
    } else {
      setParsed({ id: p.id, token: p.token });
      setLemariName(`Lemari #${p.id}`);
      setStep(1); setErrMsg('');
    }
  };

  // ── Join via share token (guest) ───────────────────────────────
  const handleJoin = async () => {
    if (!shareData) return;
    setLoading(true); setErrMsg('');
    try {
      const sv = shareData.sv || 'https://tetasco.my.id';
      const res = await fetch(`${sv}/api/join/${shareData.tok}`);
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail ?? `HTTP ${res.status}`);
      }
      const info = await res.json();
      addMyDevice({ tetascoId: info.tetascoId, name: info.name, serverUrl: sv, claimedAt: Date.now() });
      addIncubator({
        name: info.name, species: 'ayam', totalEggs: 50,
        startDate: new Date(),
        estimatedHatchDate: new Date(Date.now() + 21 * 864e5),
        isActive: true,
        iotData: { temperature: info.temperature ?? 37.5, humidity: info.humidity ?? 60, heaterOn: false, heater2On: false, fanOn: false, motorActive: false, humidifierOn: false, uvLightOn: false, nextTurningAt: new Date(Date.now() + 2 * 36e5), lastUpdated: new Date() },
        backendId: info.tetascoId,
      });
      setJoinedInfo({ name: info.name, tetascoId: info.tetascoId });
      setStep(4);
    } catch (e: any) {
      setErrMsg(e.message ?? 'Gagal join');
    } finally { setLoading(false); }
  };


  const handleClaim = async () => {
    if (!parsed) return;
    setLoading(true);
    try {
      await claimDevice(backendUrl, {
        tetascoId: parsed.id, claimToken: parsed.token, appId,
        farmName: lemariName || `Lemari #${parsed.id}`,
      });
      setStep(2);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setErrMsg(msg.includes('403') ? 'Token tidak valid. Cek kode di monitor lemari.' : `Gagal: ${msg}`);
    } finally { setLoading(false); }
  };

  const handleSetup = async () => {
    if (!parsed) return;
    setLoading(true);
    try {
      const finalName = lemariName || `Lemari #${parsed.id}`;
      const count     = parseInt(eggCount) || 48;
      const prog      = IncubationPrograms[species];
      const now       = new Date();
      addMyDevice({ tetascoId: parsed.id, name: finalName, serverUrl: backendUrl, claimedAt: Date.now() });
      addIncubator({
        name: finalName, species, totalEggs: count,
        startDate: now, estimatedHatchDate: new Date(now.getTime() + prog.durationDays * 864e5),
        isActive: true,
        iotData: { temperature: 37.5, humidity: 60, heaterOn: false, heater2On: false, fanOn: false, motorActive: false, humidifierOn: false, uvLightOn: false, nextTurningAt: new Date(now.getTime() + 2 * 36e5), lastUpdated: now },
        backendId: parsed.id,
      });
      await syncMyDevices().catch(() => {});
      setStep(3);
    } finally { setLoading(false); }
  };

  // ── Camera overlay ────────────────────────────────────────────
  if (showCamera) {
    return <QRScanner onScan={handleScanResult} onClose={() => setShowCamera(false)} />;
  }

  // ── Step 4: Joined via share (guest success) ──────────────────
  if (step === 4) {
    return (
      <div style={{ padding: '32px 0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20, textAlign: 'center' }}>
        <div style={{ width: 88, height: 88, borderRadius: 28, background: 'rgba(59,130,246,0.08)', border: '2px solid rgba(59,130,246,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 44 }}>
          🤝
        </div>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 800, color: '#1A2B1C', marginBottom: 6 }}>Bergabung! 🎉</h2>
          <p style={{ fontSize: 14, color: '#8A9E8C', lineHeight: 1.6 }}>
            Kamu sekarang bisa memantau dan mengontrol<br/><b>{joinedInfo?.name}</b>.
          </p>
        </div>
        <div style={{ width: '100%', background: '#EFF6FF', borderRadius: 16, padding: '14px 20px', border: '1px solid rgba(59,130,246,0.15)', textAlign: 'left' }}>
          <p style={{ fontSize: 12, color: '#1E40AF', lineHeight: 1.6 }}>
            📡 Terhubung ke <b>tetasco.my.id</b><br/>
            Akses bisa dicabut kapan saja oleh pemilik.
          </p>
        </div>
        <button onClick={() => navigate('/')} style={btnPrimary}>Lihat Dashboard</button>
      </div>
    );
  }

  // ── Step 3: Done ─────────────────────────────────────────────
  if (step === 3) {
    return (
      <div style={{ padding: '32px 0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20, textAlign: 'center' }}>
        <div style={{ width: 88, height: 88, borderRadius: 28, background: 'rgba(34,197,94,0.08)', border: '2px solid rgba(34,197,94,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <IconCheck s={44} />
        </div>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 800, color: '#1A2B1C', marginBottom: 6 }}>Berhasil! 🎉</h2>
          <p style={{ fontSize: 14, color: '#8A9E8C', lineHeight: 1.6 }}>
            <b>{lemariName}</b> aktif dan siap dipantau.<br/>Data sensor muncul otomatis.
          </p>
        </div>
        <div style={{ width: '100%', background: '#FFF', borderRadius: 16, padding: '16px 20px', border: '1px solid rgba(0,0,0,0.06)', textAlign: 'left' }}>
          {([
            ['Lemari', lemariName],
            ['Jenis Telur', `${SPECIES_LIST.find(s => s.key === species)?.emoji} ${SPECIES_LIST.find(s => s.key === species)?.name}`],
            ['Jumlah Telur', `${eggCount} butir`],
            ['ID Perangkat', `lemari-${parsed?.id}`],
          ] as [string,string][]).map(([k, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(0,0,0,0.04)' }}>
              <span style={{ fontSize: 12, color: '#8A9E8C' }}>{k}</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#1A2B1C' }}>{v}</span>
            </div>
          ))}
        </div>
        <button onClick={() => navigate('/')} style={btnPrimary}>Lihat Dashboard</button>
        <button onClick={() => { setStep(0); setCode(''); setParsed(null); setErrMsg(''); }} style={{ background: 'transparent', border: 'none', color: '#8A9E8C', fontSize: 14, cursor: 'pointer' }}>
          Tambah Lemari Lagi
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: '16px 0' }}>
      {/* Step indicator */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 24, alignItems: 'center' }}>
        {['Scan QR', 'Konfirmasi', 'Setup'].map((label, i) => (
          <React.Fragment key={i}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <div style={{ width: 20, height: 20, borderRadius: '50%', background: i <= step ? '#2F6B3F' : '#E2E8F0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {i < step ? <IconCheck s={11} c="#FFF"/> : <span style={{ fontSize: 9, fontWeight: 700, color: i === step ? '#FFF' : '#94A3B8' }}>{i+1}</span>}
              </div>
              <span style={{ fontSize: 10, color: i <= step ? '#2F6B3F' : '#94A3B8', fontWeight: i === step ? 700 : 400 }}>{label}</span>
            </div>
            {i < 2 && <div style={{ flex: 1, height: 1.5, background: i < step ? '#2F6B3F' : '#E2E8F0' }}/>}
          </React.Fragment>
        ))}
      </div>

      {/* ── Step 0: Input ── */}
      {step === 0 && (
        <>
          {/* FOTO QR — tombol utama, 100% works di Android */}
          <label style={{ display: 'block', marginBottom: 10 }}>
            <div style={{
              width: '100%', padding: '18px', borderRadius: 18,
              background: 'linear-gradient(135deg,#2F6B3F,#3D8A52)',
              cursor: 'pointer', display: 'flex', alignItems: 'center',
              justifyContent: 'center', gap: 12,
            }}>
              <div style={{ width: 48, height: 48, borderRadius: 14, background: 'rgba(255,255,255,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26 }}>📸</div>
              <div style={{ textAlign: 'left' }}>
                <p style={{ fontSize: 15, fontWeight: 700, color: '#FFF', marginBottom: 2 }}>Foto QR Code</p>
                <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.75)' }}>Foto QR di monitor lemari → scan otomatis</p>
              </div>
            </div>
            <input
              type="file"
              accept="image/*"
              capture="environment"
              style={{ display: 'none' }}
              onChange={async (e) => {
                const file = e.target.files?.[0];
                e.target.value = '';
                if (!file) return;
                setErrMsg('');
                const result = await decodeQRFromFile(file);
                if (result) { handleScanResult(result); }
                else { setErrMsg('QR tidak terbaca di foto. Coba ambil foto lebih dekat dan pastikan QR terlihat jelas.'); }
              }}
            />
          </label>

          {/* Live Scan — opsi kedua */}
          <button
            onClick={() => setShowCamera(true)}
            style={{
              width: '100%', padding: '14px', borderRadius: 18, border: '2px solid rgba(47,107,63,0.2)',
              background: 'rgba(47,107,63,0.05)',
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
              gap: 12, marginBottom: 16,
            }}
          >
            <div style={{ width: 42, height: 42, borderRadius: 12, background: 'rgba(47,107,63,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <IconCamera s={22} />
            </div>
            <div style={{ textAlign: 'left' }}>
              <p style={{ fontSize: 14, fontWeight: 600, color: '#2F6B3F', marginBottom: 2 }}>Live Scan (Viewfinder)</p>
              <p style={{ fontSize: 12, color: '#8A9E8C' }}>Scan langsung tanpa foto</p>
            </div>
          </button>

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <div style={{ flex: 1, height: 1, background: 'rgba(0,0,0,0.08)' }}/>
            <span style={{ fontSize: 12, color: '#94A3B8', fontWeight: 500 }}>atau ketik manual</span>
            <div style={{ flex: 1, height: 1, background: 'rgba(0,0,0,0.08)' }}/>
          </div>

          <label style={labelStyle}>Kode / Token dari Monitor</label>
          <textarea value={code} onChange={e => setCode(e.target.value)}
            placeholder={'tetasco://claim?id=3&token=F5E7820E\natau: 3:F5E7820E'} rows={3}
            style={{ width: '100%', padding: '12px 14px', borderRadius: 12, border: '1.5px solid rgba(0,0,0,0.1)', background: '#F8F9FA', fontSize: 13, color: '#1A2B1C', outline: 'none', fontFamily: 'monospace', resize: 'none', boxSizing: 'border-box' }}
          />
          {errMsg && <p style={errStyle}>{errMsg}</p>}
          <button onClick={handleManualScan} disabled={!code.trim()} style={{ ...btnPrimary, opacity: code.trim() ? 1 : 0.5 }}>Lanjut →</button>
        </>
      )}

      {/* ── Step 1: Confirm ── */}
      {step === 1 && (
        <>
          {/* Share QR — konfirmasi join */}
          {shareData && (
            <>
              <div style={{ background: 'rgba(59,130,246,0.06)', borderRadius: 16, padding: 20, marginBottom: 16, border: '1.5px solid rgba(59,130,246,0.15)', textAlign: 'center' }}>
                <div style={{ fontSize: 44, marginBottom: 8 }}>🤝</div>
                <p style={{ fontSize: 12, color: '#64748B', marginBottom: 4 }}>Undangan berbagi lemari dari:</p>
                <p style={{ fontSize: 22, fontWeight: 800, color: '#1A2B1C', marginBottom: 2 }}>{shareData.nm}</p>
                <p style={{ fontSize: 11, color: '#94A3B8' }}>via {shareData.sv}</p>
              </div>
              <div style={{ background: 'rgba(245,158,11,0.06)', borderRadius: 12, padding: '10px 14px', marginBottom: 16, border: '1px solid rgba(245,158,11,0.2)' }}>
                <p style={{ fontSize: 12, color: '#92400E', lineHeight: 1.6 }}>
                  ⚠️ Kamu akan bisa melihat dan mengontrol lemari ini. Akses dapat dicabut oleh pemilik kapan saja.
                </p>
              </div>
              {errMsg && <p style={errStyle}>{errMsg}</p>}
              <button onClick={handleJoin} disabled={loading} style={btnPrimary}>
                {loading ? 'Bergabung...' : '🤝 Gabung ke Lemari Ini'}
              </button>
              <button onClick={() => { setStep(0); setShareData(null); setErrMsg(''); }} style={btnGhost}>← Batal</button>
            </>
          )}
          {/* Pairing QR — konfirmasi claim */}
          {parsed && !shareData && (
            <>
              <div style={{ background: 'rgba(47,107,63,0.06)', borderRadius: 16, padding: 20, marginBottom: 20, border: '1.5px solid rgba(47,107,63,0.12)', textAlign: 'center' }}>
                <div style={{ fontSize: 40, marginBottom: 8 }}>📡</div>
                <p style={{ fontSize: 12, color: '#8A9E8C', marginBottom: 2 }}>Lemari ditemukan:</p>
                <p style={{ fontSize: 24, fontWeight: 800, color: '#1A2B1C' }}>Lemari #{parsed.id}</p>
                <code style={{ fontSize: 12, color: '#8A9E8C' }}>Token: {parsed.token}</code>
              </div>
              {errMsg && <p style={errStyle}>{errMsg}</p>}
              <button onClick={handleClaim} disabled={loading} style={btnPrimary}>
                {loading ? 'Menghubungi server...' : '🔗 Konfirmasi & Lanjut'}
              </button>
              <button onClick={() => { setStep(0); setErrMsg(''); }} style={btnGhost}>← Kembali</button>
            </>
          )}
        </>
      )}


      {/* ── Step 2: Setup ── */}
      {step === 2 && (
        <>
          <div style={{ background: 'rgba(34,197,94,0.06)', borderRadius: 12, padding: '10px 14px', marginBottom: 20, border: '1px solid rgba(34,197,94,0.15)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <IconCheck s={16} c="#22C55E"/>
            <span style={{ fontSize: 13, color: '#166534', fontWeight: 600 }}>Lemari #{parsed?.id} berhasil terhubung!</span>
          </div>

          <label style={labelStyle}>Nama Lemari</label>
          <input value={lemariName} onChange={e => setLemariName(e.target.value)}
            placeholder="Contoh: Lemari Kandang Belakang" style={inputStyle}/>

          <label style={{ ...labelStyle, marginTop: 18 }}>Jenis Telur</label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {SPECIES_LIST.map(sp => (
              <button key={sp.key} onClick={() => setSpecies(sp.key)} style={{
                padding: '14px 8px', borderRadius: 14,
                border: `2px solid ${species === sp.key ? '#2F6B3F' : 'rgba(0,0,0,0.08)'}`,
                background: species === sp.key ? 'rgba(47,107,63,0.07)' : '#FFF',
                cursor: 'pointer', textAlign: 'center', transition: 'all 0.15s',
              }}>
                <div style={{ fontSize: 32, marginBottom: 4 }}>{sp.emoji}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: species === sp.key ? '#2F6B3F' : '#1A2B1C' }}>{sp.name}</div>
                <div style={{ fontSize: 11, color: '#8A9E8C' }}>{sp.days} hari</div>
              </button>
            ))}
          </div>

          <label style={{ ...labelStyle, marginTop: 18 }}>Jumlah Telur (butir)</label>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button onClick={() => setEggCount(v => String(Math.max(1, parseInt(v||'1') - 1)))}
              style={{ width: 44, height: 44, borderRadius: 12, border: '1.5px solid rgba(0,0,0,0.1)', background: '#F8F9FA', fontSize: 22, cursor: 'pointer', color: '#2F6B3F', fontWeight: 700, display:'flex', alignItems:'center', justifyContent:'center' }}>−</button>
            <input type="number" value={eggCount} onChange={e => setEggCount(e.target.value)} min="1" max="500"
              style={{ flex: 1, ...inputStyle, textAlign: 'center', fontSize: 22, fontWeight: 800, padding: '10px' }}/>
            <button onClick={() => setEggCount(v => String(parseInt(v||'0') + 1))}
              style={{ width: 44, height: 44, borderRadius: 12, border: '1.5px solid rgba(0,0,0,0.1)', background: '#F8F9FA', fontSize: 22, cursor: 'pointer', color: '#2F6B3F', fontWeight: 700, display:'flex', alignItems:'center', justifyContent:'center' }}>+</button>
          </div>

          <button onClick={handleSetup} disabled={loading || !lemariName.trim()} style={{ ...btnPrimary, marginTop: 24, opacity: lemariName.trim() ? 1 : 0.5 }}>
            {loading ? 'Menyimpan...' : '✅ Selesai — Mulai Inkubasi'}
          </button>
        </>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// Browse Online Tab
// ─────────────────────────────────────────────────────────────────
function BrowseTab() {
  const { backendUrl, appId, myDevices, addMyDevice, addIncubator } = useAppStore();
  const [devices, setDevices]   = useState<DeviceInfo[]>([]);
  const [loading, setLoading]   = useState(true);
  const [claiming, setClaiming] = useState<number | null>(null);
  const [codes, setCodes]       = useState<Record<number, string>>({});
  const [claimSteps, setClaimSteps] = useState<Record<number, 'idle'|'input'|'setup'|'done'>>({});
  const [names, setNames]       = useState<Record<number, string>>({});
  const [species, setSpecies]   = useState<Record<number, EggSpecies>>({});
  const [err, setErr]           = useState<Record<number, string>>({});

  useEffect(() => {
    fetchAllDevices(backendUrl)
      .then(r => setDevices(r.devices ?? []))
      .catch(() => setDevices([]))
      .finally(() => setLoading(false));
  }, [backendUrl]);

  const isMine = (id: number) => myDevices.some(d => d.tetascoId === id);

  const doConfirm = async (dev: DeviceInfo) => {
    const id    = dev.tetasco_id;
    const token = (codes[id] ?? '').trim().toUpperCase();
    if (!token) { setErr(e => ({ ...e, [id]: 'Masukkan kode token dari monitor' })); return; }
    setClaiming(id);
    try {
      await claimDevice(backendUrl, { tetascoId: id, claimToken: token, appId, farmName: `Lemari #${id}` });
      setClaimSteps(s => ({ ...s, [id]: 'setup' }));
      setNames(n => ({ ...n, [id]: `Lemari #${id}` }));
      setSpecies(s => ({ ...s, [id]: 'ayam' }));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setErr(ev => ({ ...ev, [id]: msg.includes('403') ? 'Token salah' : `Gagal: ${msg}` }));
    } finally { setClaiming(null); }
  };

  const doSetup = (id: number) => {
    const finalName = names[id] || `Lemari #${id}`;
    const sp        = species[id] || 'ayam';
    const prog      = IncubationPrograms[sp];
    const now       = new Date();
    addMyDevice({ tetascoId: id, name: finalName, serverUrl: backendUrl, claimedAt: Date.now() });
    addIncubator({ name: finalName, species: sp, totalEggs: 48, startDate: now,
      estimatedHatchDate: new Date(now.getTime() + prog.durationDays * 864e5), isActive: true,
      iotData: { temperature: 37.5, humidity: 60, heaterOn: false, heater2On: false, fanOn: false, motorActive: false, humidifierOn: false, uvLightOn: false, nextTurningAt: new Date(now.getTime() + 2 * 36e5), lastUpdated: now },
      backendId: id });
    setClaimSteps(s => ({ ...s, [id]: 'done' }));
  };

  if (loading) return (
    <div style={{ textAlign: 'center', padding: 40 }}>
      <div style={{ width: 40, height: 40, borderRadius: '50%', border: '3px solid rgba(47,107,63,0.15)', borderTopColor: '#2F6B3F', margin: '0 auto 12px', animation: 'spin 0.8s linear infinite' }}/>
      <p style={{ color: '#8A9E8C', fontSize: 14 }}>Mencari lemari online...</p>
    </div>
  );

  if (!devices.length) return (
    <div style={{ textAlign: 'center', padding: '40px 20px' }}>
      <IconWifi s={48} c="#CBD5E1"/>
      <p style={{ color: '#8A9E8C', marginTop: 12 }}>Tidak ada lemari online saat ini.</p>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, paddingTop: 8 }}>
      {devices.map(dev => {
        const id  = dev.tetasco_id;
        const st  = claimSteps[id] ?? 'idle';
        const mine = isMine(id);

        return (
          <div key={id} style={{ background: '#FFF', borderRadius: 16, padding: 16, border: `1.5px solid ${mine || st === 'done' ? 'rgba(34,197,94,0.2)' : 'rgba(0,0,0,0.06)'}` }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: st !== 'idle' && st !== 'done' ? 12 : 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 36, height: 36, borderRadius: 10, background: dev.online ? 'rgba(34,197,94,0.1)' : 'rgba(148,163,184,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <IconWifi s={18} c={dev.online ? '#22C55E' : '#94A3B8'}/>
                </div>
                <div>
                  <p style={{ fontSize: 14, fontWeight: 600, color: '#1A2B1C' }}>Lemari #{id}</p>
                  <p style={{ fontSize: 11, color: '#8A9E8C' }}>
                    {dev.online ? `${dev.temperature ?? '--'}°C · ${dev.humidity ?? '--'}%` : 'Offline'}
                  </p>
                </div>
              </div>
              {mine || st === 'done'
                ? <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#22C55E', fontSize: 12, fontWeight: 600 }}><IconCheck s={16}/> Milik Saya</div>
                : st === 'idle'
                  ? <button onClick={() => setClaimSteps(s => ({ ...s, [id]: 'input' }))} style={{ padding: '8px 14px', borderRadius: 10, border: 'none', background: 'rgba(47,107,63,0.1)', color: '#2F6B3F', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>+ Tambah</button>
                  : null
              }
            </div>

            {st === 'input' && (
              <div>
                <p style={{ fontSize: 12, color: '#8A9E8C', marginBottom: 8 }}>Kode token dari monitor HDMI:</p>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input value={codes[id] ?? ''} onChange={e => setCodes(c => ({ ...c, [id]: e.target.value.toUpperCase() }))}
                    placeholder="37E7EAAF" maxLength={8}
                    style={{ flex: 1, padding: '10px 12px', borderRadius: 10, border: '1.5px solid rgba(0,0,0,0.1)', fontFamily: 'monospace', fontSize: 15, letterSpacing: 3, outline: 'none', textAlign: 'center' }}/>
                  <button onClick={() => doConfirm(dev)} disabled={claiming === id}
                    style={{ padding: '10px 14px', borderRadius: 10, border: 'none', background: '#2F6B3F', color: '#FFF', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
                    {claiming === id ? '...' : 'OK'}
                  </button>
                </div>
                {err[id] && <p style={errStyle}>{err[id]}</p>}
              </div>
            )}

            {st === 'setup' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <input value={names[id] ?? `Lemari #${id}`} onChange={e => setNames(n => ({ ...n, [id]: e.target.value }))}
                  placeholder="Nama lemari" style={inputStyle}/>
                <div style={{ display: 'flex', gap: 6 }}>
                  {SPECIES_LIST.map(sp => (
                    <button key={sp.key} onClick={() => setSpecies(s => ({ ...s, [id]: sp.key }))}
                      style={{ flex: 1, padding: '8px 4px', borderRadius: 10, border: `2px solid ${(species[id] || 'ayam') === sp.key ? '#2F6B3F' : 'rgba(0,0,0,0.08)'}`, background: (species[id] || 'ayam') === sp.key ? 'rgba(47,107,63,0.07)' : '#FFF', cursor: 'pointer', fontSize: 10, textAlign: 'center' }}>
                      <div style={{ fontSize: 20 }}>{sp.emoji}</div>
                      <div style={{ fontWeight: 700 }}>{sp.name}</div>
                    </button>
                  ))}
                </div>
                <button onClick={() => doSetup(id)} style={{ ...btnPrimary, marginTop: 4 }}>✅ Selesai</button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// Main Screen
// ─────────────────────────────────────────────────────────────────
export function AddDevice() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<'qr' | 'browse'>('qr');

  return (
    <div className="screen anim-fade-in" style={{ background: '#F2F4F6' }}>
      <div style={{ paddingTop: 'env(safe-area-inset-top, 44px)', background: '#FFFFFF', borderBottom: '1px solid rgba(0,0,0,0.06)', position: 'sticky', top: 0, zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px' }}>
          <button onClick={() => navigate(-1)} style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(0,0,0,0.06)', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <IconBack/>
          </button>
          <div>
            <h1 style={{ fontSize: 18, fontWeight: 700, color: '#1A2B1C' }}>Tambah Inkubator</h1>
            <p style={{ fontSize: 12, color: '#8A9E8C' }}>Hubungkan lemari ke app kamu</p>
          </div>
        </div>
        <div style={{ display: 'flex', padding: '0 16px', gap: 4, borderTop: '1px solid rgba(0,0,0,0.04)' }}>
          {([['qr', 'Scan QR / Kode', <IconQR s={14}/>], ['browse', 'Cari Online', <IconSearch s={14}/>]] as const).map(([key, label, icon]) => (
            <button key={key} onClick={() => setTab(key)} style={{ flex: 1, padding: '10px 0', border: 'none', background: 'transparent', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5, fontSize: 12, fontWeight: tab === key ? 700 : 500, color: tab === key ? '#2F6B3F' : '#8A9E8C', borderBottom: `2.5px solid ${tab === key ? '#2F6B3F' : 'transparent'}`, transition: 'all 0.2s' }}>
              {icon}{label}
            </button>
          ))}
        </div>
      </div>
      <div className="screen-scroll" style={{ padding: '0 16px 40px' }}>
        {tab === 'qr' ? <QRInputTab /> : <BrowseTab />}
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
