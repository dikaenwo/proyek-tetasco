import React, { useState } from 'react';
import { useAppStore, HistoryRecord } from '../store/appStore';
import { IncubationPrograms, EggSpecies } from '../constants/incubation';

const FILTERS: { label: string; value: EggSpecies | 'all' }[] = [
  { label: 'Semua',  value: 'all' },
  { label: 'Ayam',  value: 'ayam' },
  { label: 'Puyuh', value: 'puyuh' },
  { label: 'Bebek', value: 'bebek' },
  { label: 'Angsa', value: 'angsa' },
  { label: 'Kalkun', value: 'kalkun' },
];

// Inline SVG icons for stats
const EggIcon    = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><ellipse cx="12" cy="13" rx="6" ry="8" stroke="#2F6B3F" strokeWidth="1.8"/></svg>;
const HatchIcon  = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M12 2C9.24 2 7 6.13 7 10.5C7 14.87 9.24 19 12 19c2.76 0 5-4.13 5-8.5C17 6.13 14.76 2 12 2Z" stroke="#D98B4A" strokeWidth="1.8"/><path d="M9 15l3 4 3-4" stroke="#D98B4A" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>;
const ChartIcon  = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><polyline points="22,12 18,12 15,21 9,3 6,12 2,12" stroke="#27AE60" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>;
const CheckIcon  = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#2F6B3F" strokeWidth="1.8"/><polyline points="9,12 11,14 15,10" stroke="#2F6B3F" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>;
const CalIcon    = () => <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><rect x="3" y="4" width="18" height="18" rx="2" stroke="#8A9E8C" strokeWidth="1.8"/><line x1="16" y1="2" x2="16" y2="6" stroke="#8A9E8C" strokeWidth="1.8" strokeLinecap="round"/><line x1="8" y1="2" x2="8" y2="6" stroke="#8A9E8C" strokeWidth="1.8" strokeLinecap="round"/><line x1="3" y1="10" x2="21" y2="10" stroke="#8A9E8C" strokeWidth="1.8"/></svg>;
const NoteIcon   = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="#8A9E8C" strokeWidth="1.8" strokeLinejoin="round"/><polyline points="14,2 14,8 20,8" stroke="#8A9E8C" strokeWidth="1.8" strokeLinejoin="round"/><line x1="16" y1="13" x2="8" y2="13" stroke="#8A9E8C" strokeWidth="1.8" strokeLinecap="round"/><line x1="16" y1="17" x2="8" y2="17" stroke="#8A9E8C" strokeWidth="1.8" strokeLinecap="round"/></svg>;

export function History() {
  const { history } = useAppStore();
  const [filter, setFilter] = useState<EggSpecies | 'all'>('all');
  const filtered     = filter === 'all' ? history : history.filter((h) => h.species === filter);
  const totalHatched = history.reduce((s, h) => s + h.hatchedEggs, 0);
  const totalEggs    = history.reduce((s, h) => s + h.totalEggs, 0);
  const avgRate      = totalEggs > 0 ? Math.round((totalHatched / totalEggs) * 100) : 0;
  const fmtDate      = (d: Date) => new Date(d).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });

  return (
    <div className="screen anim-fade-in">
      <div className="grad-primary safe-top" style={{ padding: '8px 20px 20px' }}>
        <h1 className="t-h2 c-white">Riwayat Inkubasi</h1>
        <p className="t-body" style={{ color: 'rgba(255,255,255,0.75)', marginTop: 4 }}>{history.length} siklus selesai</p>
      </div>

      <div className="screen-scroll flex-1">
        <div style={{ padding: '16px 16px 32px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Stats */}
          <div style={{ display: 'flex', gap: 8 }}>
            {[
              { Icon: <EggIcon />,   label: 'Siklus',   val: `${history.length}`,                              bg: '#EAF3EC', color: '#2F6B3F' },
              { Icon: <HatchIcon />, label: 'Menetas',  val: `${totalHatched}`,                                bg: '#FDF0E3', color: '#D98B4A' },
              { Icon: <ChartIcon />, label: 'Rata-rata', val: `${avgRate}%`,                                   bg: '#E8F8F0', color: '#27AE60' },
              { Icon: <CheckIcon />, label: 'Sukses',   val: `${history.filter((h) => h.success).length}`,    bg: '#EAF3EC', color: '#2F6B3F' },
            ].map((s) => (
              <div key={s.label} className="card" style={{ flex: 1, padding: '10px 6px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                <div style={{ width: 30, height: 30, borderRadius: 8, background: s.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{s.Icon}</div>
                <span style={{ fontSize: 16, fontWeight: 700, color: s.color, letterSpacing: -0.3 }}>{s.val}</span>
                <span className="t-sm c-text-muted text-center">{s.label}</span>
              </div>
            ))}
          </div>

          {/* Filters */}
          <div className="filter-scroll">
            {FILTERS.map((f) => (
              <button key={f.value} className={`filter-chip ${filter === f.value ? 'active' : ''}`} onClick={() => setFilter(f.value)}>
                {f.label}
              </button>
            ))}
          </div>

          {/* Records */}
          {filtered.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '48px 16px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 64, height: 64, borderRadius: 20, background: '#EAF3EC', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="#2F6B3F" strokeWidth="1.8" strokeLinejoin="round"/><polyline points="14,2 14,8 20,8" stroke="#2F6B3F" strokeWidth="1.8" strokeLinejoin="round"/></svg>
              </div>
              <h3 className="t-h4 c-text">Belum ada riwayat</h3>
              <p className="t-sm c-text-muted">Riwayat inkubasi akan muncul di sini</p>
            </div>
          ) : (
            <div className="list">
              {filtered.map((r) => <HistCard key={r.id} r={r} fmtDate={fmtDate} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function HistCard({ r, fmtDate }: { r: HistoryRecord; fmtDate: (d: Date) => string }) {
  const prog  = IncubationPrograms[r.species];
  const rate  = Math.round((r.hatchedEggs / r.totalEggs) * 100);
  const days  = Math.round((new Date(r.endDate).getTime() - new Date(r.startDate).getTime()) / 864e5);
  const accentColor = r.success ? '#27AE60' : '#D98B4A';

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden', borderLeft: `4px solid ${accentColor}` }}>
      {/* Header */}
      <div style={{ padding: '14px 14px 10px', display: 'flex', gap: 12, alignItems: 'center' }}>
        <div style={{ width: 44, height: 44, borderRadius: 12, background: prog.bgColor, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, flexShrink: 0 }}>
          {prog.emoji}
        </div>
        <div style={{ flex: 1 }}>
          <p className="t-h4 c-text">{r.incubatorName}</p>
          <p className="t-sm c-text-muted">{prog.nameId} · {days} hari inkubasi</p>
        </div>
        <div style={{ background: r.success ? '#E8F8F0' : '#FDF0E3', borderRadius: 10, padding: '6px 10px', textAlign: 'center', minWidth: 50 }}>
          <span style={{ fontSize: 16, fontWeight: 700, color: accentColor, letterSpacing: -0.3 }}>{rate}%</span>
        </div>
      </div>

      {/* Stats row */}
      <div style={{ display: 'flex', borderTop: '1px solid #EEEAD8', padding: '10px 14px', gap: 0 }}>
        {[
          { Icon: <EggIcon />,   l: 'Telur',   v: `${r.totalEggs}` },
          { Icon: <HatchIcon />, l: 'Menetas',  v: `${r.hatchedEggs}` },
          { Icon: <CalIcon />,   l: 'Mulai',   v: fmtDate(r.startDate) },
          { Icon: <CalIcon />,   l: 'Selesai', v: fmtDate(r.endDate) },
        ].map((s, i) => (
          <React.Fragment key={i}>
            {i > 0 && <div className="divider-v" style={{ margin: '0 8px' }} />}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
              <span className="t-sm-m c-text">{s.v}</span>
              <span className="t-sm c-text-muted">{s.l}</span>
            </div>
          </React.Fragment>
        ))}
      </div>

      {/* Progress bar */}
      <div style={{ padding: '0 14px 12px' }}>
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${rate}%`, background: accentColor }} />
        </div>
      </div>

      {/* Notes */}
      {r.notes && (
        <div style={{ padding: '0 14px 12px', display: 'flex', gap: 6, alignItems: 'flex-start', borderTop: '1px solid #EEEAD8', paddingTop: 10 }}>
          <NoteIcon />
          <p className="t-sm c-text-sec" style={{ flex: 1 }}>{r.notes}</p>
        </div>
      )}
    </div>
  );
}
