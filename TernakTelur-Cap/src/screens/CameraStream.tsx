import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/appStore';
import { IconChevronLeft } from '../components/Icons';

const SERVER_BASE     = 'https://tetasco.my.id';
const POLL_MS         = 100; // ~10 FPS snapshot polling

export function CameraStream() {
  const navigate = useNavigate();
  const { incubators, myDevices, backendUrl } = useAppStore();

  // ── Resolusi device & tetascoId ──────────────────────────────────
  const active     = incubators.find(i => i.isActive);
  const device     = myDevices.find(d => d.tetascoId === active?.backendId)
                  ?? myDevices[0]; // fallback ke device pertama yang di-claim
  const tetascoId  = device?.tetascoId ?? active?.backendId
                  ?? (myDevices.length > 0 ? myDevices[0].tetascoId : null);
  const localUrl   = (backendUrl ?? '').replace(/\/$/, '');

  // ── Snapshot URLs ─────────────────────────────────────────────────
  // Gunakan snapshot polling — MJPEG tidak reliable di Android WebView & Cloudflare
  const serverSnap  = tetascoId ? `${SERVER_BASE}/api/tetasco/${tetascoId}/camera/snapshot` : null;
  const serverStats = tetascoId ? `${SERVER_BASE}/api/tetasco/${tetascoId}/camera/stats`    : null;
  const localSnap   = localUrl  ? `${localUrl}/api/camera/snapshot` : null;
  const localStats  = localUrl  ? `${localUrl}/api/camera/stats`    : null;

  const [imgSrc,    setImgSrc]    = useState<string | null>(null);
  const [imgError,  setImgError]  = useState(false);
  const [srcFps,    setSrcFps]    = useState<number | null>(null);  // FPS dari Raspi
  const [pollFps,   setPollFps]   = useState(0);                    // FPS polling aktual
  const [useServer, setUseServer] = useState(!!tetascoId);

  const pollRef    = useRef<ReturnType<typeof setInterval> | null>(null);
  const fpsRef     = useRef<ReturnType<typeof setInterval> | null>(null);
  const frameCount = useRef(0);

  const snapUrl  = useServer ? serverSnap  : localSnap;
  const statsUrl = useServer ? serverStats : localStats;
  const incubatorName = active?.name ?? 'Kamera Inkubator';

  // ── Snapshot polling loop ──────────────────────────────────────────
  useEffect(() => {
    if (!snapUrl) return;
    setImgError(false);
    frameCount.current = 0;

    const poll = () => {
      const url = `${snapUrl}?t=${Date.now()}`; // cache-bust
      const img = new Image();
      img.onload  = () => { setImgSrc(url); setImgError(false); frameCount.current++; };
      img.onerror = () => setImgError(true);
      img.src = url;
    };

    poll();
    pollRef.current = setInterval(poll, POLL_MS);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [snapUrl]);

  // ── Hitung FPS polling aktual (tiap 1 detik) ──────────────────────
  useEffect(() => {
    frameCount.current = 0;
    fpsRef.current = setInterval(() => {
      setPollFps(frameCount.current);
      frameCount.current = 0;
    }, 1000);
    return () => { if (fpsRef.current) clearInterval(fpsRef.current); };
  }, [snapUrl]);

  // ── Poll stats endpoint (FPS sumber dari Raspi) ───────────────────
  useEffect(() => {
    if (!statsUrl) return;
    const poll = async () => {
      try {
        const r = await fetch(statsUrl, { cache: 'no-store' });
        if (r.ok) { const d = await r.json(); if (d.fps != null) setSrcFps(Math.round(d.fps)); }
      } catch { /* ignore */ }
    };
    poll();
    const t = setInterval(poll, 3000);
    return () => clearInterval(t);
  }, [statsUrl]);

  const handleSwitch = () => { setImgSrc(null); setImgError(false); setUseServer(u => !u); };
  const handleRetry  = () => { setImgError(false); setImgSrc(null); };

  const isLive = !!imgSrc && !imgError;

  return (
    <div className="screen anim-fade-in"
      style={{ background:'#0D1117', display:'flex', flexDirection:'column', height:'100%' }}>

      {/* ── Header ── */}
      <div className="safe-top"
        style={{ display:'flex', alignItems:'center', gap:12, padding:'10px 16px 14px',
                 background:'linear-gradient(135deg,#0D1117,#1A2B1C)', flexShrink:0 }}>
        <button onClick={() => navigate(-1)}
          style={{ width:36, height:36, borderRadius:10, background:'rgba(255,255,255,0.08)',
                   border:'1px solid rgba(255,255,255,0.12)', display:'flex', alignItems:'center',
                   justifyContent:'center', cursor:'pointer', flexShrink:0 }}>
          <IconChevronLeft size={22} color="rgba(255,255,255,0.85)" strokeWidth={2.2} />
        </button>

        <div style={{ flex:1, minWidth:0 }}>
          <p style={{ fontSize:10, color:'rgba(255,255,255,0.4)', fontWeight:500,
                      letterSpacing:0.8, textTransform:'uppercase', marginBottom:1 }}>Live Stream</p>
          <h1 style={{ fontSize:17, fontWeight:700, color:'#FFF', overflow:'hidden',
                       textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{incubatorName}</h1>
        </div>

        {/* LIVE / OFFLINE badge */}
        <div style={{ display:'flex', alignItems:'center', gap:5,
                      background: isLive ? 'rgba(239,68,68,0.15)' : 'rgba(80,80,80,0.2)',
                      border:`1px solid ${isLive ? 'rgba(239,68,68,0.35)' : 'rgba(80,80,80,0.3)'}`,
                      borderRadius:999, padding:'4px 10px' }}>
          <div style={{ width:6, height:6, borderRadius:'50%',
                        background: isLive ? '#EF4444' : '#555',
                        animation: isLive ? 'pulse 1.5s infinite' : 'none' }} />
          <span style={{ fontSize:11, color: isLive ? '#FCA5A5' : '#888',
                         fontWeight:700, letterSpacing:0.5 }}>
            {isLive ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>
      </div>

      {/* ── Network toggle ── */}
      {serverSnap && localSnap && (
        <div style={{ background:'rgba(255,255,255,0.03)', borderBottom:'1px solid rgba(255,255,255,0.06)',
                      padding:'8px 16px', display:'flex', alignItems:'center', gap:8 }}>
          <span style={{ fontSize:12, color:'rgba(255,255,255,0.4)', flex:1 }}>
            {useServer ? '🌐 Server (semua jaringan)' : `📶 Lokal (${localUrl.replace('http://','').split(':')[0]})`}
          </span>
          <button onClick={handleSwitch}
            style={{ padding:'5px 12px', borderRadius:8, border:'1px solid rgba(255,255,255,0.15)',
                     background:'rgba(255,255,255,0.07)', color:'rgba(255,255,255,0.7)',
                     fontSize:11, cursor:'pointer' }}>
            {useServer ? '📶 Lokal' : '🌐 Server'}
          </button>
        </div>
      )}

      {/* ── Stream area ── */}
      <div style={{ flex:1, display:'flex', alignItems:'center', justifyContent:'center',
                    background:'#000', position:'relative', overflow:'hidden' }}>

        {/* Belum ada URL */}
        {!snapUrl && (
          <div style={{ textAlign:'center', color:'rgba(255,255,255,0.4)', padding:32 }}>
            <div style={{ fontSize:56, marginBottom:16 }}>📡</div>
            <p style={{ fontSize:16, fontWeight:600, marginBottom:8, color:'rgba(255,255,255,0.7)' }}>
              Belum Terhubung
            </p>
            <p style={{ fontSize:13, lineHeight:1.6 }}>
              Tambahkan inkubator terlebih dahulu<br/>untuk melihat kamera live.
            </p>
          </div>
        )}

        {/* Error */}
        {snapUrl && imgError && (
          <div style={{ textAlign:'center', color:'rgba(255,255,255,0.4)', padding:32 }}>
            <div style={{ fontSize:56, marginBottom:16 }}>📷</div>
            <p style={{ fontSize:16, fontWeight:600, marginBottom:8, color:'rgba(255,255,255,0.7)' }}>
              Kamera Tidak Tersedia
            </p>
            <p style={{ fontSize:13, lineHeight:1.6, marginBottom:6 }}>
              Pastikan Raspi menyala dan webcam terhubung.
            </p>
            <p style={{ fontSize:10, color:'rgba(255,255,255,0.2)', marginBottom:24, wordBreak:'break-all', padding:'0 16px' }}>
              {snapUrl}
            </p>
            <button onClick={handleRetry}
              style={{ padding:'10px 24px', borderRadius:12, background:'#2F6B3F',
                       border:'none', color:'#FFF', fontSize:14, cursor:'pointer' }}>
              🔄 Coba Lagi
            </button>
          </div>
        )}

        {/* Live image */}
        {snapUrl && !imgError && (
          <>
            {imgSrc
              ? <img src={imgSrc} alt={`Kamera — ${incubatorName}`}
                  style={{ width:'100%', height:'100%', objectFit:'contain', display:'block' }} />
              : <div style={{ color:'rgba(255,255,255,0.3)', fontSize:13 }}>Memuat kamera...</div>
            }

            {/* Stats overlay */}
            <div style={{ position:'absolute', bottom:12, left:12, display:'flex', gap:6, flexWrap:'wrap' }}>
              <div style={{ background:'rgba(0,0,0,0.7)', backdropFilter:'blur(6px)',
                            borderRadius:8, padding:'4px 10px', border:'1px solid rgba(255,255,255,0.08)' }}>
                <span style={{ fontSize:11, fontFamily:'monospace', fontWeight:700,
                                color: pollFps >= 8 ? '#52C97F' : pollFps > 0 ? '#F59E0B' : 'rgba(255,255,255,0.3)' }}>
                  {pollFps > 0 ? `${pollFps} FPS` : '-- FPS'}
                </span>
              </div>
              {srcFps != null && (
                <div style={{ background:'rgba(0,0,0,0.7)', backdropFilter:'blur(6px)',
                              borderRadius:8, padding:'4px 10px', border:'1px solid rgba(255,255,255,0.08)' }}>
                  <span style={{ fontSize:11, fontFamily:'monospace', color:'rgba(255,255,255,0.4)' }}>
                    src {srcFps}fps
                  </span>
                </div>
              )}
              <div style={{ background:'rgba(0,0,0,0.7)', backdropFilter:'blur(6px)',
                            borderRadius:8, padding:'4px 10px', border:'1px solid rgba(255,255,255,0.08)' }}>
                <span style={{ fontSize:11, color:'rgba(255,255,255,0.4)' }}>🎥 {incubatorName}</span>
              </div>
            </div>

            {/* Network badge */}
            <div style={{ position:'absolute', top:12, right:12, background:'rgba(0,0,0,0.7)',
                          backdropFilter:'blur(6px)', borderRadius:8, padding:'4px 10px',
                          border:'1px solid rgba(255,255,255,0.08)' }}>
              <span style={{ fontSize:10, fontWeight:600, color: useServer ? '#60A5FA' : '#52C97F' }}>
                {useServer ? '🌐 Server' : '📶 Lokal'}
              </span>
            </div>
          </>
        )}
      </div>

      {/* ── Footer ── */}
      {isLive && snapUrl && (
        <div style={{ background:'#0D1117', padding:'14px 16px 32px',
                      borderTop:'1px solid rgba(255,255,255,0.06)', display:'flex', gap:10, flexShrink:0 }}>
          <a href={snapUrl} download={`snapshot-${incubatorName}.jpg`}
            style={{ flex:1, padding:'12px', borderRadius:14,
                     background:'linear-gradient(135deg,#2F6B3F,#3D8A52)',
                     color:'#FFF', fontSize:13, fontWeight:700, textAlign:'center',
                     textDecoration:'none', display:'block' }}>
            📷 Simpan Foto
          </a>
          <button onClick={handleRetry}
            style={{ padding:'12px 20px', borderRadius:14,
                     border:'1.5px solid rgba(255,255,255,0.12)',
                     background:'transparent', color:'rgba(255,255,255,0.7)',
                     fontSize:13, cursor:'pointer' }}>
            🔄
          </button>
        </div>
      )}

      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }`}</style>
    </div>
  );
}
