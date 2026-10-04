import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSensorData, getActuators, setActuator, getFarmerProfile, getControlMode } from '../api/tetascoApi';

/* ================================================
   Slider Toggle — Ramah Layar Sentuh 7 Inci
   ================================================ */
const SliderToggle = ({ value, onChange, labelOff = 'MATI', labelOn = 'AKTIF', disabled = false }) => {
  const W = 42, H = 22, THUMB = 16, INSET = (H - THUMB) / 2;
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      opacity: disabled ? 0.4 : 1,
      pointerEvents: disabled ? 'none' : 'auto',
    }}>
      {/* Label status di sebelah kiri tombol slider */}
      <span style={{
        fontSize: 10, fontWeight: 900, letterSpacing: '0.05em',
        textTransform: 'uppercase',
        color: value ? '#FFFFFF' : 'rgba(255,255,255,0.85)',
        fontFamily: "'JetBrains Mono', monospace",
        textAlign: 'right',
        minWidth: 32,
        transition: 'color 0.25s',
      }}>
        {value ? labelOn : labelOff}
      </span>
      <button
        onClick={e => { e.stopPropagation(); onChange(!value); }}
        style={{
          position: 'relative',
          width: W, height: H,
          borderRadius: 999,
          border: 'none', cursor: 'pointer',
          background: value ? 'rgba(255,255,255,0.48)' : 'rgba(0,0,0,0.32)',
          boxShadow: value
            ? 'inset 0 1px 3px rgba(0,0,0,0.1), 0 0 0 2px rgba(255,255,255,0.85)'
            : 'inset 0 1px 3px rgba(0,0,0,0.4)',
          transition: 'all 0.25s cubic-bezier(0.34,1.3,0.64,1)',
          flexShrink: 0, padding: 0,
        }}
      >
        <div style={{
          position: 'absolute',
          top: INSET,
          left: value ? W - THUMB - INSET : INSET,
          width: THUMB, height: THUMB,
          borderRadius: '50%',
          background: '#FFFFFF',
          boxShadow: '0 2px 5px rgba(0,0,0,0.35)',
          transition: 'left 0.25s cubic-bezier(0.34,1.3,0.64,1)',
        }} />
      </button>
    </div>
  );
};

/* ================================================
   Control Card — Icon Jelas, Tipografi Pas & Corak Batik
   ================================================ */
const ControlCard = ({ icon, label, sublabel, gradient, colorOn, children }) => (
  <div
    className="batik-panel-white"
    style={{
      background: gradient,
      borderRadius: 14,
      display: 'flex',
      alignItems: 'stretch',
      position: 'relative',
      overflow: 'hidden',
      boxShadow: `0 3px 12px ${colorOn}24`,
      boxSizing: 'border-box',
      height: '100%',
    }}
  >
    {/* Indonesian Batik Kawung Component Overlay */}
    <div className="batik-overlay batik-overlay-white" />

    {/* Sisi Paling Kiri: Icon Full Mengisi Secara Vertikal */}
    <div
      style={{
        width: 46,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(255, 255, 255, 0.18)',
        borderRight: '1.5px solid rgba(255, 255, 255, 0.25)',
        flexShrink: 0,
        position: 'relative',
        zIndex: 1,
      }}
    >
      <span
        className="material-symbols-rounded"
        style={{
          fontSize: 24,
          color: '#FFFFFF',
          filter: 'drop-shadow(0 2px 5px rgba(0,0,0,0.2))',
        }}
      >
        {icon}
      </span>
    </div>

    {/* Sisi Kanan: Title, Subtitle, dan Slider */}
    <div
      style={{
        flex: 1,
        minWidth: 0,
        padding: '0 8px 0 10px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 6,
        position: 'relative',
        zIndex: 1,
      }}
    >
      <div style={{ minWidth: 0, flex: 1, paddingRight: 4 }}>
        <div
          style={{
            fontSize: 12,
            fontWeight: 900,
            color: '#FFFFFF',
            letterSpacing: '-0.01em',
            lineHeight: 1.15,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {label}
        </div>
        <div
          style={{
            fontSize: 8.5,
            fontWeight: 700,
            color: 'rgba(255, 255, 255, 0.92)',
            marginTop: 2,
            lineHeight: 1.25,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            wordBreak: 'break-word',
          }}
        >
          {sublabel}
        </div>
      </div>

      {/* Slider Section */}
      <div style={{ flexShrink: 0 }}>
        {children}
      </div>
    </div>
  </div>
);

/* ================================================
   DASBOR UTAMA — Font Terkalibrasi & Icon Jelas
   ================================================ */
const DasborUtama = () => {
  const [lampu1,   setLampu1]   = useState(false);
  const [lampu2,   setLampu2]   = useState(false);
  const [kipas,    setKipas]    = useState(false);
  const [pelembab, setPelembab] = useState(false);
  const [sinarUV,  setSinarUV]  = useState(false);
  const [rakGerak, setRakGerak] = useState(false);

  const navigate = useNavigate();
  const lastActionTimeRef = useRef({});

  const [tempVal, setTempVal] = useState(37.8);
  const [humVal, setHumVal] = useState(55.0);
  const [targetTemp, setTargetTemp] = useState(37.8);
  const [targetHum, setTargetHum] = useState(55.0);
  const [isHardware, setIsHardware] = useState(false);
  const [deviceStatus, setDeviceStatus] = useState('STANDBY');
  const [activeProfile, setActiveProfile] = useState('AYAM');
  const [farmerProfile, setFarmerProfile] = useState({
    nama_lemari: 'Tetasco 01',
    nama_peternak: 'Peternak Tetasco',
    tetasco_id: 1,
  });

  // Sinkronisasi data real-time dari backend lokal setiap 1.2 detik
  useEffect(() => {
    let isMounted = true;
    let pollCount = 0;

    const fetchData = async () => {
      try {
        pollCount++;
        // Ambil profil setiap 5x polling (~6 detik)
        const promises = [getSensorData(), getActuators(), getControlMode()];
        if (pollCount % 5 === 1) {
          promises.push(getFarmerProfile());
        }

        const [sensor, acts, mode, profile] = await Promise.all(promises);
        if (!isMounted) return;

        if (profile) {
          setFarmerProfile(prev => ({ ...prev, ...profile }));
        }

        if (mode) {
          if (mode.device_status) setDeviceStatus(mode.device_status);
          if (mode.profile) setActiveProfile(mode.profile);
        }

        if (sensor) {
          if (sensor.temperature !== undefined) setTempVal(sensor.temperature);
          if (sensor.humidity !== undefined) setHumVal(sensor.humidity);
          if (sensor.target_temp !== undefined) setTargetTemp(sensor.target_temp);
          if (sensor.target_hum !== undefined) setTargetHum(sensor.target_hum);
          if (sensor.is_hardware !== undefined) setIsHardware(sensor.is_hardware);
          if (sensor.sensor !== undefined) setSensorType(sensor.sensor);
        }

        // KUNCI STABILITAS SLIDER: Hanya perbarui state dari polling jika tidak ada aksi manual dalam 2.5 detik terakhir
        const now = Date.now();
        const guardTime = 2500; // ms

        if (acts) {
          if (acts.lamp_1 !== undefined && (now - (lastActionTimeRef.current['lamp_1'] || 0) > guardTime)) {
            setLampu1(acts.lamp_1);
          }
          if (acts.lamp_2 !== undefined && (now - (lastActionTimeRef.current['lamp_2'] || 0) > guardTime)) {
            setLampu2(acts.lamp_2);
          }
          if (acts.fan !== undefined && (now - (lastActionTimeRef.current['fan'] || 0) > guardTime)) {
            setKipas(acts.fan);
          }
          if (acts.mist_maker !== undefined && (now - (lastActionTimeRef.current['mist_maker'] || 0) > guardTime)) {
            setPelembab(acts.mist_maker);
          }
          if (acts.uv_light !== undefined && (now - (lastActionTimeRef.current['uv_light'] || 0) > guardTime)) {
            setSinarUV(acts.uv_light);
          }
          if (acts.motor !== undefined && (now - (lastActionTimeRef.current['motor'] || 0) > guardTime)) {
            setRakGerak(acts.motor);
          }
        }
      } catch (err) {
        // Safe failover
      }
    };

    fetchData();
    const timer = setInterval(fetchData, 1200);
    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  }, []);

  const handleToggleLampu1 = async (val) => {
    lastActionTimeRef.current['lamp_1'] = Date.now();
    setLampu1(val);
    await setActuator('lamp_1', val);
  };

  const handleToggleLampu2 = async (val) => {
    lastActionTimeRef.current['lamp_2'] = Date.now();
    setLampu2(val);
    await setActuator('lamp_2', val);
  };

  const handleToggleFan = async (val) => {
    lastActionTimeRef.current['fan'] = Date.now();
    setKipas(val);
    await setActuator('fan', val);
  };

  const handleToggleHumidifier = async (val) => {
    lastActionTimeRef.current['mist_maker'] = Date.now();
    setPelembab(val);
    await setActuator('mist_maker', val);
  };

  const handleToggleUV = async (val) => {
    lastActionTimeRef.current['uv_light'] = Date.now();
    setSinarUV(val);
    await setActuator('uv_light', val);
  };

  const handleToggleRak = async (val) => {
    lastActionTimeRef.current['motor'] = Date.now();
    setRakGerak(val);
    await setActuator('motor', val);
  };

  const pemanasAktif = lampu1 || lampu2;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: 12,
      height: '100%',
      boxSizing: 'border-box',
    }}>

      {/* ===== 3 SENSOR CARDS (50% TINGGI) ===== */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1.15fr 1.15fr 1.6fr',
        gap: 12,
        flex: 1,                    /* 50% tinggi layar seimbang */
        minHeight: 0,
      }}>

        {/* SUHU INTERNAL */}
        <div
          style={{
            background: 'linear-gradient(145deg, #FFFDF9 0%, #FFEDD5 100%)',
            borderRadius: 18,
            padding: '12px 15px',
            border: '2px solid #FED7AA',
            position: 'relative',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxShadow: '0 4px 14px rgba(249,115,22,0.10)',
          }}
        >
          {/* Indonesian Batik Kawung Motif */}
          <div className="batik-overlay batik-overlay-warm" />

          {/* Background Icon — Halus & Lega */}
          <span className="material-symbols-rounded" style={{
            position: 'absolute',
            right: 8,
            top: '50%',
            transform: 'translateY(-50%)',
            fontSize: 75,
            color: 'rgba(249,115,22,0.11)',
            pointerEvents: 'none',
            lineHeight: 1,
            userSelect: 'none',
          }}>
            device_thermostat
          </span>

          {/* 1. Atas: Header dengan Icon Badge */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative', zIndex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: 24, height: 24, borderRadius: 6,
                background: '#FFEDD5', border: '1.5px solid #FED7AA',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>
                <span className="material-symbols-rounded" style={{ fontSize: 14, color: '#EA580C' }}>
                  device_thermostat
                </span>
              </div>
              <span style={{ fontSize: 11, fontWeight: 900, color: '#C2410C', letterSpacing: '0.04em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>
                Suhu Internal
              </span>
            </div>
            <span style={{
              fontSize: 9.5, fontWeight: 800,
              background: '#FFEDD5', color: '#EA580C',
              padding: '2px 7px', borderRadius: 999,
              fontFamily: "'JetBrains Mono', monospace",
              border: '1.5px solid #FED7AA',
              whiteSpace: 'nowrap',
            }}>
              TARGET {targetTemp.toFixed(1)}°C
            </span>
          </div>

          {/* 2. Tengah Vertikal: Nilai Jelas Terbaca */}
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', position: 'relative', zIndex: 1, my: 'auto' }}>
            {/* Angka Suhu */}
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
              <span style={{
                fontSize: 38,
                fontWeight: 900,
                color: '#EA580C',
                lineHeight: 1,
                fontFamily: "'JetBrains Mono', monospace",
                letterSpacing: '-0.02em',
              }}>
                {tempVal.toFixed(1)}
              </span>
              <span style={{ fontSize: 16, fontWeight: 900, color: '#FB923C' }}>°C</span>
            </div>
          </div>

          {/* 3. Bawah: Status Pill */}
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              background: pemanasAktif ? 'rgba(34,197,94,0.18)' : 'rgba(148,163,184,0.2)',
              padding: '2.5px 9px', borderRadius: 999,
            }}>
              <div style={{
                width: 6, height: 6, borderRadius: '50%',
                background: pemanasAktif ? '#22C55E' : '#94A3B8',
                boxShadow: pemanasAktif ? '0 0 6px #22C55E' : 'none',
              }} />
              <span style={{
                fontSize: 10, fontWeight: 800,
                color: pemanasAktif ? '#15803D' : '#475569',
              }}>
                {pemanasAktif
                  ? (lampu1 && lampu2 ? 'Lampu 1 & 2 Aktif' : (lampu1 ? 'Lampu 1 Aktif' : 'Lampu 2 Aktif'))
                  : 'Pemanas Siaga · Stabil'}
              </span>
            </div>
          </div>
        </div>

        {/* KELEMBABAN */}
        <div
          style={{
            background: 'linear-gradient(145deg, #F8FAFF 0%, #DBEAFE 100%)',
            borderRadius: 18,
            padding: '12px 15px',
            border: '2px solid #BFDBFE',
            position: 'relative',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxShadow: '0 4px 14px rgba(59,130,246,0.10)',
          }}
        >
          {/* Indonesian Batik Kawung Motif */}
          <div className="batik-overlay batik-overlay-blue" />

          {/* Background Icon — Halus & Lega */}
          <span className="material-symbols-rounded" style={{
            position: 'absolute',
            right: 8,
            top: '50%',
            transform: 'translateY(-50%)',
            fontSize: 75,
            color: 'rgba(59,130,246,0.11)',
            pointerEvents: 'none',
            lineHeight: 1,
            userSelect: 'none',
          }}>
            humidity_mid
          </span>

          {/* 1. Atas: Header dengan Icon Badge */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative', zIndex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: 24, height: 24, borderRadius: 6,
                background: '#DBEAFE', border: '1.5px solid #BFDBFE',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>
                <span className="material-symbols-rounded" style={{ fontSize: 14, color: '#2563EB' }}>
                  humidity_mid
                </span>
              </div>
              <span style={{ fontSize: 11, fontWeight: 900, color: '#1D4ED8', letterSpacing: '0.04em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>
                Kelembaban
              </span>
            </div>
            <span style={{
              fontSize: 9.5, fontWeight: 800,
              background: '#DBEAFE', color: '#2563EB',
              padding: '2px 7px', borderRadius: 999,
              fontFamily: "'JetBrains Mono', monospace",
              border: '1.5px solid #BFDBFE',
              whiteSpace: 'nowrap',
            }}>
              TARGET {Math.round(targetHum)}%
            </span>
          </div>

          {/* 2. Tengah Vertikal: Nilai Jelas Terbaca */}
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', position: 'relative', zIndex: 1, my: 'auto' }}>
            {/* Angka Kelembaban */}
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
              <span style={{
                fontSize: 38,
                fontWeight: 900,
                color: '#2563EB',
                lineHeight: 1,
                fontFamily: "'JetBrains Mono', monospace",
                letterSpacing: '-0.02em',
              }}>
                {Math.round(humVal)}
              </span>
              <span style={{ fontSize: 15, fontWeight: 900, color: '#60A5FA' }}>% RH</span>
            </div>
          </div>

          {/* 3. Bawah: Status Pill */}
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              background: pelembab ? 'rgba(34,197,94,0.18)' : 'rgba(148,163,184,0.2)',
              padding: '2.5px 9px', borderRadius: 999,
            }}>
              <div style={{
                width: 6, height: 6, borderRadius: '50%',
                background: pelembab ? '#22C55E' : '#94A3B8',
                boxShadow: pelembab ? '0 0 6px #22C55E' : 'none',
              }} />
              <span style={{
                fontSize: 10, fontWeight: 800,
                color: pelembab ? '#15803D' : '#475569',
              }}>
                {pelembab ? 'Pelembab Aktif · Spray ON' : 'Pelembab Siaga · Stabil'}
              </span>
            </div>
          </div>
        </div>

        {/* LEMARI & AKUN PETERNAK (1 Lemari = 1 Akun) */}
        <div
          onClick={() => navigate('/profil')}
          title="Klik untuk membuka profil peternak & lemari inkubator"
          style={{
            background: 'linear-gradient(140deg, #4F46E5 0%, #6366F1 55%, #8B5CF6 100%)',
            borderRadius: 18,
            padding: '12px 15px',
            boxShadow: '0 6px 20px rgba(99,102,241,0.28)',
            position: 'relative',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            cursor: 'pointer',
            transition: 'transform 0.2s ease',
          }}
        >
          {/* Indonesian Batik Kawung Motif */}
          <div className="batik-overlay batik-overlay-white" />

          {/* Background Icon */}
          <span className="material-symbols-rounded" style={{
            position: 'absolute',
            right: 8,
            top: '50%',
            transform: 'translateY(-50%)',
            fontSize: 75,
            color: 'rgba(255,255,255,0.14)',
            pointerEvents: 'none',
            lineHeight: 1,
            userSelect: 'none',
          }}>
            badge
          </span>

          {/* 1. Atas: Header dengan Icon Badge */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'relative', zIndex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: 24, height: 24, borderRadius: 6,
                background: 'rgba(255,255,255,0.22)', border: '1.5px solid rgba(255,255,255,0.4)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>
                <span className="material-symbols-rounded" style={{ fontSize: 14, color: '#FFFFFF' }}>
                  person
                </span>
              </div>
              <span style={{ fontSize: 11, fontWeight: 900, color: '#FFFFFF', letterSpacing: '0.04em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>
                Lemari & Akun
              </span>
            </div>
            <span style={{
              fontSize: 9.5, fontWeight: 800,
              background: 'rgba(255,255,255,0.25)', color: '#FFFFFF',
              padding: '2px 7px', borderRadius: 999,
              fontFamily: "'JetBrains Mono', monospace",
              border: '1px solid rgba(255,255,255,0.4)',
              whiteSpace: 'nowrap',
            }}>
              ID #{farmerProfile.tetasco_id || 1}
            </span>
          </div>

          {/* 2. Tengah: Nama Lemari & Nama Peternak */}
          <div style={{ position: 'relative', zIndex: 1, my: 'auto' }}>
            <div style={{
              fontSize: 18,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.15,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}>
              {farmerProfile.nama_lemari || 'Tetasco 01'}
            </div>
            <div style={{
              fontSize: 12,
              fontWeight: 700,
              color: 'rgba(255,255,255,0.9)',
              marginTop: 2,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}>
              {farmerProfile.nama_peternak || 'Peternak Tetasco'}
            </div>
          </div>

          {/* 3. Bawah: Status Pill */}
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              background: deviceStatus === 'RUNNING' ? 'rgba(34,197,94,0.3)' : 'rgba(245,158,11,0.3)',
              padding: '3px 9px', borderRadius: 999,
              border: `1px solid ${deviceStatus === 'RUNNING' ? 'rgba(74,222,128,0.5)' : 'rgba(252,211,77,0.5)'}`,
            }}>
              <div style={{
                width: 6, height: 6, borderRadius: '50%',
                background: deviceStatus === 'RUNNING' ? '#4ADE80' : '#FCD34D',
                boxShadow: deviceStatus === 'RUNNING' ? '0 0 6px #4ADE80' : '0 0 6px #FCD34D',
              }} />
              <span style={{
                fontSize: 9.5, fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: '0.03em',
              }}>
                {deviceStatus === 'RUNNING' && activeProfile ? `AKTIF · TELUR ${activeProfile}` : 'STATUS: SIAGA'}
              </span>
            </div>
          </div>
        </div>

      </div>

      {/* Banner Siaga Jika Mesin Belum Aktif */}
      {deviceStatus === 'STANDBY' && (
        <div style={{
          background: 'linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%)',
          border: '1.5px solid #FCD34D',
          borderRadius: 12,
          padding: '8px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
          boxShadow: '0 2px 8px rgba(245,158,11,0.15)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="material-symbols-rounded" style={{ fontSize: 22, color: '#D97706' }}>
              pause_circle
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 11, fontWeight: 900, color: '#92400E', letterSpacing: '0.04em' }}>
                STATUS: MESIN SIAGA
              </span>
              <span style={{ fontSize: 10.5, fontWeight: 700, color: '#B45309' }}>
                Belum ada penetasan aktif. Pilih jenis telur untuk memulai inkubasi.
              </span>
            </div>
          </div>
          <button
            onClick={() => navigate('/control')}
            style={{
              background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: 8,
              padding: '6px 14px',
              fontSize: 10.5,
              fontWeight: 900,
              fontFamily: "'JetBrains Mono', monospace",
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              boxShadow: '0 2px 6px rgba(217,119,6,0.3)',
            }}
          >
            <span className="material-symbols-rounded" style={{ fontSize: 16 }}>egg_alt</span>
            PILIH TELUR
          </button>
        </div>
      )}

      {/* ===== 6 CONTROL CARDS (3 KOLOM × 2 BARIS) ===== */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gridTemplateRows: 'repeat(2, 1fr)',
        gap: 10,
        flex: 1,                    /* 50% tinggi layar seimbang */
        minHeight: 0,
      }}>

        {/* 1. PEMANAS 1 (Lampu 1) */}
        <ControlCard
          icon="local_fire_department"
          label="Pemanas 1"
          sublabel="Lampu Pemanas Utama"
          gradient="linear-gradient(135deg, #F97316 0%, #EF4444 100%)"
          colorOn="#EF4444"
        >
          <SliderToggle value={lampu1} onChange={handleToggleLampu1} labelOff="MATI" labelOn="AKTIF" />
        </ControlCard>

        {/* 2. PEMANAS 2 (Lampu 2) */}
        <ControlCard
          icon="wb_incandescent"
          label="Pemanas 2"
          sublabel="Lampu Booster Suhu"
          gradient="linear-gradient(135deg, #FB923C 0%, #EA580C 100%)"
          colorOn="#EA580C"
        >
          <SliderToggle value={lampu2} onChange={handleToggleLampu2} labelOff="MATI" labelOn="AKTIF" />
        </ControlCard>

        {/* 3. SIRKULASI KIPAS */}
        <ControlCard
          icon="mode_fan"
          label="Kipas Sirkulasi"
          sublabel="Exhaust Sirkulasi Udara"
          gradient="linear-gradient(135deg, #38BDF8 0%, #3B82F6 100%)"
          colorOn="#3B82F6"
        >
          <SliderToggle value={kipas} onChange={handleToggleFan} labelOff="MATI" labelOn="AKTIF" />
        </ControlCard>

        {/* 4. PELEMBAB UDARA */}
        <ControlCard
          icon="water_drop"
          label="Pelembab Udara"
          sublabel={`Mist Maker Target ${Math.round(targetHum)}%`}
          gradient="linear-gradient(135deg, #34D399 0%, #14B8A6 100%)"
          colorOn="#14B8A6"
        >
          <SliderToggle value={pelembab} onChange={handleToggleHumidifier} labelOff="MATI" labelOn="AKTIF" />
        </ControlCard>

        {/* 5. SINAR UV */}
        <ControlCard
          icon="sanitizer"
          label="Sinar UV"
          sublabel="Sterilisasi Ruang Kabinet"
          gradient="linear-gradient(135deg, #818CF8 0%, #6366F1 100%)"
          colorOn="#6366F1"
        >
          <SliderToggle value={sinarUV} onChange={handleToggleUV} labelOff="MATI" labelOn="AKTIF" />
        </ControlCard>

        {/* 6. PEMBALIK RAK */}
        <ControlCard
          icon="sync"
          label={
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span>Pembalik Rak</span>
              {rakGerak && (
                <span
                  className="material-symbols-rounded animate-spin-slow"
                  style={{ fontSize: 16, color: '#FFFFFF' }}
                >
                  rotate_90_degrees_ccw
                </span>
              )}
            </div>
          }
          sublabel={rakGerak ? "Rak berputar aktif" : "Rak posisi diam standby"}
          gradient="linear-gradient(135deg, #A78BFA 0%, #8B5CF6 100%)"
          colorOn="#8B5CF6"
        >
          <SliderToggle
            value={rakGerak}
            onChange={handleToggleRak}
            labelOff="MATI"
            labelOn="AKTIF"
          />
        </ControlCard>

      </div>

    </div>
  );
};

export default DasborUtama;
