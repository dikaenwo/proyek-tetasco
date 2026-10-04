import React from 'react';

interface ProgressRingProps {
  progress: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
  trackColor?: string;
  label?: string;
  sublabel?: string;
}

export function ProgressRing({ progress, size = 100, strokeWidth = 9, color = '#2F6B3F', trackColor = '#EDE9D8', label, sublabel }: ProgressRingProps) {
  const r = (size - strokeWidth) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - Math.min(1, Math.max(0, progress)));
  const cx = size / 2;

  return (
    <div className="progress-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} style={{ position: 'absolute' }}>
        <defs>
          <linearGradient id="rg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={color} stopOpacity="1" />
            <stop offset="100%" stopColor={color} stopOpacity="0.7" />
          </linearGradient>
        </defs>
        <circle cx={cx} cy={cx} r={r} fill="none" stroke={trackColor} strokeWidth={strokeWidth} />
        <circle
          cx={cx} cy={cx} r={r} fill="none"
          stroke="url(#rg)" strokeWidth={strokeWidth}
          strokeDasharray={`${circ} ${circ}`}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${cx} ${cx})`}
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      <div className="progress-ring-center" style={{ width: '100%', height: '100%' }}>
        {label && <span style={{ fontSize: size < 90 ? 14 : 18, fontWeight: 700, color: color === '#FFFFFF' ? '#FFFFFF' : '#29332B', letterSpacing: -0.5 }}>{label}</span>}
        {sublabel && <span style={{ fontSize: 10, color: color === '#FFFFFF' ? 'rgba(255,255,255,0.7)' : '#8A9E8C' }}>{sublabel}</span>}
      </div>
    </div>
  );
}
