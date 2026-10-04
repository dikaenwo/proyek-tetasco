import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import QRCode from 'qrcode';
import { useAppStore } from '../store/appStore';
import { IconChevronLeft } from '../components/Icons';

export function ShareDevice() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { incubators, myDevices, backendUrl, appId } = useAppStore();

  const inc    = incubators.find(i => i.id === id) ?? incubators.find(i => i.isActive);
  const device = myDevices.find(d => d.tetascoId === inc?.backendId);
  const SERVER = 'https://tetasco.my.id';

  const [qrDataUrl,  setQrDataUrl]  = useState('');
  const [shareToken, setShareToken] = useState('');
  const [expires,    setExpires]    = useState('');
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState('');
  const [copied,     setCopied]     = useState(false);

  const tetascoId = inc?.backendId ?? device?.tetascoId ?? 1;
  const name      = inc?.name ?? device?.name ?? 'Lemari';

  useEffect(() => {
    generateToken();
  }, [tetascoId]);

  const generateToken = async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`${SERVER}/api/tetasco/${tetascoId}/share-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ appId }),
      });
      if (!res.ok) throw new Error(await res.text());
      const d = await res.json();
      setShareToken(d.token);
      const payload = JSON.stringify(d.qrPayload);
      const url = await QRCode.toDataURL(payload, {
        width: 280, margin: 2,
        color: { dark: '#000000', light: '#FFFFFF' },
        errorCorrectionLevel: 'H',
      });
      setQrDataUrl(url);
      const h = Math.round(d.expiresIn / 3600);
      setExpires(`${h} jam`);
    } catch (e: any) {
      setError(e.message ?? 'Gagal generate QR');
    } finally {
      setLoading(false);
    }
  };

  const copyLink = () => {
    const link = `tetasco://join/${shareToken}`;
    navigator.clipboard?.writeText(link).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="screen anim-fade-in" style={{ background: '#F2F4F6', display: 'flex', flexDirection: 'column' }}>

      {/* Header */}
      <div className="safe-top" style={{ display:'flex', alignItems:'center', gap:12, padding:'10px 16px 14px', background:'#FFF', borderBottom:'1px solid rgba(0,0,0,0.06)' }}>
        <button onClick={() => navigate(-1)} style={{ width:36, height:36, borderRadius:10, background:'rgba(0,0,0,0.05)', border:'none', display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer' }}>
          <IconChevronLeft size={22} color="#1A2B1C" strokeWidth={2.2} />
        </button>
        <div style={{ flex:1 }}>
          <p style={{ fontSize:11, color:'#8A9E8C', fontWeight:500, marginBottom:1 }}>Berbagi Perangkat</p>
          <h1 style={{ fontSize:17, fontWeight:700, color:'#1A2B1C' }}>{name}</h1>
        </div>
      </div>

      <div className="screen-scroll flex-1" style={{ padding:24, display:'flex', flexDirection:'column', gap:20 }}>

        {/* Info card */}
        <div style={{ background:'linear-gradient(135deg,#2F6B3F,#3D8A52)', borderRadius:20, padding:20, color:'#FFF' }}>
          <p style={{ fontSize:13, opacity:0.8, marginBottom:6 }}>📲 Cara Berbagi</p>
          <p style={{ fontSize:14, lineHeight:1.6 }}>
            Minta pengguna lain buka aplikasi Tetasco → <strong>Tambah Lemari</strong> → <strong>Scan QR Berbagi</strong> → kamera diarahkan ke QR ini.
          </p>
          {expires && (
            <div style={{ marginTop:12, background:'rgba(255,255,255,0.15)', borderRadius:10, padding:'6px 12px', display:'inline-block' }}>
              <span style={{ fontSize:12, fontWeight:600 }}>⏱ QR berlaku {expires}</span>
            </div>
          )}
        </div>

        {/* QR Code */}
        <div style={{ background:'#FFF', borderRadius:24, padding:24, boxShadow:'0 4px 20px rgba(0,0,0,0.08)', display:'flex', flexDirection:'column', alignItems:'center', gap:16 }}>
          {loading ? (
            <div style={{ width:280, height:280, display:'flex', alignItems:'center', justifyContent:'center', background:'#F8F9FA', borderRadius:16 }}>
              <div style={{ fontSize:40 }}>⏳</div>
            </div>
          ) : error ? (
            <div style={{ width:280, padding:40, textAlign:'center', background:'#FFF0F0', borderRadius:16 }}>
              <div style={{ fontSize:40, marginBottom:12 }}>❌</div>
              <p style={{ fontSize:13, color:'#EF4444', marginBottom:16 }}>{error}</p>
              <button onClick={generateToken} style={{ padding:'8px 20px', borderRadius:10, background:'#2F6B3F', border:'none', color:'#FFF', cursor:'pointer' }}>
                Coba Lagi
              </button>
            </div>
          ) : (
            <>
              <div style={{ padding:12, background:'#FFF', borderRadius:16, boxShadow:'0 2px 12px rgba(0,0,0,0.1)' }}>
                <img src={qrDataUrl} alt="Share QR" style={{ width:256, height:256, display:'block' }} />
              </div>
              <p style={{ fontSize:12, color:'#8A9E8C', textAlign:'center' }}>
                QR ini berisi akses ke <strong>{name}</strong>
              </p>
            </>
          )}
        </div>

        {/* Actions */}
        {!loading && !error && (
          <div style={{ display:'flex', gap:10 }}>
            <button
              onClick={generateToken}
              style={{ flex:1, padding:'14px', borderRadius:16, border:'1.5px solid rgba(47,107,63,0.2)', background:'rgba(47,107,63,0.05)', color:'#2F6B3F', fontSize:14, fontWeight:600, cursor:'pointer' }}
            >
              🔄 Refresh QR
            </button>
          </div>
        )}

        {/* Warning */}
        <div style={{ background:'rgba(245,158,11,0.08)', border:'1px solid rgba(245,158,11,0.2)', borderRadius:14, padding:14 }}>
          <p style={{ fontSize:12, color:'#92400E', lineHeight:1.6 }}>
            ⚠️ Siapapun yang punya QR ini bisa mengakses dan mengontrol <strong>{name}</strong>. Refresh QR jika tidak ingin dibagikan lagi.
          </p>
        </div>
      </div>
    </div>
  );
}
