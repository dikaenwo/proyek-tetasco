import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore, Notification } from '../store/appStore';
import { IconChevronLeft, IconBell, IconAlertTriangle, IconAlertCircle, IconInfo, IconCheck } from '../components/Icons';

const CFG = {
  info:    { Icon: IconInfo,          color: '#2F6B3F', bg: '#EAF3EC', stripe: '#2F6B3F', label: 'Info' },
  warning: { Icon: IconAlertTriangle, color: '#D98B4A', bg: '#FDF0E3', stripe: '#D98B4A', label: 'Peringatan' },
  danger:  { Icon: IconAlertCircle,  color: '#C0392B', bg: '#FDEDEB', stripe: '#C0392B', label: 'Berbahaya' },
};

function relTime(d: Date) {
  const m = Math.floor((Date.now() - new Date(d).getTime()) / 6e4);
  const h = Math.floor(m / 60);
  const dy = Math.floor(h / 24);
  if (m < 1) return 'Baru saja';
  if (m < 60) return `${m} menit lalu`;
  if (h < 24) return `${h} jam lalu`;
  return `${dy} hari lalu`;
}

export function Notifications() {
  const navigate = useNavigate();
  const { notifications, markRead, markAllRead } = useAppStore();
  const unread = notifications.filter((n) => !n.read).length;
  const danger = notifications.filter((n) => n.type === 'danger' && !n.read).length;
  const warn   = notifications.filter((n) => n.type === 'warning' && !n.read).length;

  return (
    <div className="screen anim-fade-in">
      {/* Header */}
      <div className="grad-primary safe-top" style={{ padding: '8px 16px 16px' }}>
        <button
          onClick={() => navigate(-1)}
          style={{ background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 10, width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', marginBottom: 10 }}
        >
          <IconChevronLeft size={22} color="rgba(255,255,255,0.9)" strokeWidth={2.2} />
        </button>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 className="t-h2 c-white">Notifikasi</h1>
            <p className="t-body" style={{ color: 'rgba(255,255,255,0.75)', marginTop: 2 }}>
              {unread > 0 ? `${unread} belum dibaca` : 'Semua sudah dibaca'}
            </p>
          </div>
          {unread > 0 && (
            <button
              onClick={markAllRead}
              style={{ background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 999, padding: '6px 14px', display: 'flex', alignItems: 'center', gap: 5, cursor: 'pointer', marginTop: 4 }}
            >
              <IconCheck size={14} color="rgba(255,255,255,0.9)" strokeWidth={2.5} />
              <span style={{ fontSize: 12, fontWeight: 500, color: 'rgba(255,255,255,0.9)' }}>Tandai semua</span>
            </button>
          )}
        </div>

        {/* Alert summary chips */}
        {(danger > 0 || warn > 0) && (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
            {danger > 0 && (
              <div style={{ background: '#FDEDEB', borderRadius: 999, padding: '4px 12px', display: 'flex', alignItems: 'center', gap: 5, border: '1px solid rgba(192,57,43,0.3)' }}>
                <IconAlertCircle size={13} color="#C0392B" />
                <span style={{ fontSize: 12, fontWeight: 600, color: '#C0392B' }}>{danger} Berbahaya</span>
              </div>
            )}
            {warn > 0 && (
              <div style={{ background: '#FDF0E3', borderRadius: 999, padding: '4px 12px', display: 'flex', alignItems: 'center', gap: 5, border: '1px solid rgba(217,139,74,0.3)' }}>
                <IconAlertTriangle size={13} color="#D98B4A" />
                <span style={{ fontSize: 12, fontWeight: 600, color: '#D98B4A' }}>{warn} Peringatan</span>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="screen-scroll flex-1">
        <div style={{ padding: '14px 14px 32px', display: 'flex', flexDirection: 'column', gap: 8 }}>
          {notifications.length === 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '64px 24px', gap: 14 }}>
              <div style={{ width: 72, height: 72, borderRadius: 22, background: '#EAF3EC', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <IconBell size={32} color="#2F6B3F" />
              </div>
              <h3 className="t-h3 c-text text-center">Tidak ada notifikasi</h3>
              <p className="t-body c-text-muted text-center">Semua kondisi inkubator berjalan normal</p>
            </div>
          ) : (
            notifications.map((n) => <NotifCard key={n.id} n={n} onRead={() => markRead(n.id)} />)
          )}
        </div>
      </div>
    </div>
  );
}

function NotifCard({ n, onRead }: { n: Notification; onRead: () => void }) {
  const cfg = CFG[n.type];
  const cardBg    = n.type === 'danger' && !n.read ? '#FFF8F8' : n.type === 'warning' && !n.read ? '#FFFBF7' : !n.read ? '#FAFFFE' : '#FFFFFF';
  const bdrColor  = n.type === 'danger' ? 'rgba(192,57,43,0.3)' : n.type === 'warning' ? 'rgba(217,139,74,0.3)' : n.read ? '#E8E4D8' : 'rgba(47,107,63,0.2)';

  return (
    <div className="notif-card" style={{ background: cardBg, borderColor: bdrColor }} onClick={onRead}>
      {!n.read && <div className="notif-stripe" style={{ background: cfg.stripe }} />}
      <div className="notif-content">
        <div className="notif-icon-box" style={{ background: cfg.bg }}>
          <cfg.Icon size={22} color={cfg.color} />
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
            <p className="t-body-m" style={{ color: n.read ? '#5A6B5C' : '#29332B', flex: 1 }}>{n.title}</p>
            <span style={{ background: cfg.bg, color: cfg.color, padding: '2px 8px', borderRadius: 999, fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap', letterSpacing: 0.3 }}>
              {cfg.label}
            </span>
          </div>
          <p className="t-sm" style={{ color: n.read ? '#8A9E8C' : '#5A6B5C' }}>{n.message}</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#ADADAD" strokeWidth="1.8"/><polyline points="12,6 12,12 16,14" stroke="#ADADAD" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            <p className="t-sm" style={{ color: '#ADADAD' }}>{relTime(n.timestamp)}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
