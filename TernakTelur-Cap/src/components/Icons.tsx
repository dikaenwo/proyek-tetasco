import React from 'react';

interface IconProps {
  size?: number;
  color?: string;
  strokeWidth?: number;
}

export const IconBell = ({ size = 22, color = '#FFFFFF', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M18 8.5A6 6 0 0 0 6 8.5C6 12.5 4 14 4 14H20C20 14 18 12.5 18 8.5Z" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M13.73 21A2 2 0 0 1 10.27 21" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
  </svg>
);

export const IconBellFilled = ({ size = 22, color = '#FFFFFF', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M18 8.5A6 6 0 0 0 6 8.5C6 12.5 4 14 4 14H20C20 14 18 12.5 18 8.5Z" fill={color} stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M13.73 21A2 2 0 0 1 10.27 21" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
  </svg>
);

export const IconTrash = ({ size = 20, color = 'rgba(255,255,255,0.7)', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <polyline points="3,6 5,6 21,6" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M19 6L18.1 19.1C18.05 19.6 17.6 20 17.1 20H6.9C6.4 20 5.95 19.6 5.9 19.1L5 6" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M10 11V17M14 11V17" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <path d="M9 6V4C9 3.45 9.45 3 10 3H14C14.55 3 15 3.45 15 4V6" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconChevronRight = ({ size = 18, color = '#A5B5A7', strokeWidth = 2 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <polyline points="9,18 15,12 9,6" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconChevronLeft = ({ size = 24, color = 'rgba(255,255,255,0.85)', strokeWidth = 2.2 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <polyline points="15,18 9,12 15,6" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconThermometer = ({ size = 18, color = '#EF4444', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M14 14.76V4.5A2.5 2.5 0 0 0 9 4.5V14.76A4 4 0 1 0 14 14.76Z" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <line x1="11.5" y1="11" x2="11.5" y2="6" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
  </svg>
);

export const IconDroplet = ({ size = 18, color = '#3B82F6', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M12 2.69L17.66 8.35A8 8 0 1 1 6.34 8.35L12 2.69Z" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconRefresh = ({ size = 18, color = '#2F6B3F', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <polyline points="23,4 23,10 17,10" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <polyline points="1,20 1,14 7,14" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M3.51 9A9 9 0 0 1 20.49 9M20.49 15A9 9 0 0 1 3.51 15" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconFan = ({ size = 18, color = '#10B981', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="3" stroke={color} strokeWidth={strokeWidth}/>
    <path d="M12 9C12 9 13 5 16 5C18 5 19 7 19 9C19 11 17 12 15 12" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <path d="M15 12C15 12 19 13 19 16C19 18 17 19 15 19C13 19 12 17 12 15" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <path d="M12 15C12 15 11 19 8 19C6 19 5 17 5 15C5 13 7 12 9 12" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <path d="M9 12C9 12 5 11 5 8C5 6 7 5 9 5C11 5 12 7 12 9" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
  </svg>
);

export const IconFlame = ({ size = 20, color = '#EF4444', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M8.5 14.5C8.5 14.5 7 13 7 10.5C7 7 10 4 12 2C12 2 11.5 6 14 8C14 8 16 5.5 15.5 3C17.5 5 19 8 19 11C19 15.42 15.87 19 12 19C10.14 19 8.5 17.5 8.5 16C8.5 14.5 9.5 14 9.5 14" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M12 22C10.07 22 8.5 20.43 8.5 18.5C8.5 16 12 14 12 14C12 14 15.5 16 15.5 18.5C15.5 20.43 13.93 22 12 22Z" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconCheckCircle = ({ size = 20, color = '#22C55E', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="10" stroke={color} strokeWidth={strokeWidth}/>
    <polyline points="9,12 11,14 15,10" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconAlertTriangle = ({ size = 20, color = '#F59E0B', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M10.29 3.86L1.82 18C1.64 18.31 1.55 18.65 1.55 19C1.55 20.1 2.45 21 3.55 21H20.45C21.55 21 22.45 20.1 22.45 19C22.45 18.65 22.36 18.31 22.18 18L13.71 3.86A2 2 0 0 0 10.29 3.86Z" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <line x1="12" y1="9" x2="12" y2="13" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="12" y1="17" x2="12.01" y2="17" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
  </svg>
);

export const IconAlertCircle = ({ size = 20, color = '#EF4444', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="10" stroke={color} strokeWidth={strokeWidth}/>
    <line x1="12" y1="8" x2="12" y2="12" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="12" y1="16" x2="12.01" y2="16" stroke={color} strokeWidth={strokeWidth + 0.5} strokeLinecap="round"/>
  </svg>
);

export const IconInfo = ({ size = 20, color = '#3B82F6', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="10" stroke={color} strokeWidth={strokeWidth}/>
    <line x1="12" y1="16" x2="12" y2="12" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="12" y1="8" x2="12.01" y2="8" stroke={color} strokeWidth={strokeWidth + 0.5} strokeLinecap="round"/>
  </svg>
);

export const IconEdit = ({ size = 20, color = '#5A6B5C', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5Z" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconList = ({ size = 20, color = '#5A6B5C', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <line x1="8" y1="6"  x2="21" y2="6"  stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="8" y1="12" x2="21" y2="12" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="8" y1="18" x2="21" y2="18" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="3" y1="6"  x2="3.01" y2="6"  stroke={color} strokeWidth={strokeWidth + 0.5} strokeLinecap="round"/>
    <line x1="3" y1="12" x2="3.01" y2="12" stroke={color} strokeWidth={strokeWidth + 0.5} strokeLinecap="round"/>
    <line x1="3" y1="18" x2="3.01" y2="18" stroke={color} strokeWidth={strokeWidth + 0.5} strokeLinecap="round"/>
  </svg>
);

export const IconHelpCircle = ({ size = 20, color = '#5A6B5C', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="10" stroke={color} strokeWidth={strokeWidth}/>
    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <line x1="12" y1="17" x2="12.01" y2="17" stroke={color} strokeWidth={strokeWidth + 0.5} strokeLinecap="round"/>
  </svg>
);

export const IconAbout = ({ size = 20, color = '#5A6B5C', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="10" stroke={color} strokeWidth={strokeWidth}/>
    <line x1="12" y1="8" x2="12" y2="8.01" stroke={color} strokeWidth={strokeWidth + 0.5} strokeLinecap="round"/>
    <polyline points="11,11 12,11 12,16 13,16" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconSettings = ({ size = 20, color = '#5A6B5C', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="3" stroke={color} strokeWidth={strokeWidth}/>
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z" stroke={color} strokeWidth={strokeWidth}/>
  </svg>
);

export const IconPlus = ({ size = 20, color = '#FFFFFF', strokeWidth = 2.2 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <line x1="12" y1="5" x2="12" y2="19" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="5"  y1="12" x2="19" y2="12" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
  </svg>
);

export const IconCheck = ({ size = 18, color = '#22C55E', strokeWidth = 2.5 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <polyline points="20,6 9,17 4,12" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconMapPin = ({ size = 15, color = 'rgba(255,255,255,0.75)', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0Z" stroke={color} strokeWidth={strokeWidth}/>
    <circle cx="12" cy="10" r="3" stroke={color} strokeWidth={strokeWidth}/>
  </svg>
);

export const IconStar = ({ size = 15, color = 'rgba(255,255,255,0.9)', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26 12,2" stroke={color} fill={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconClock = ({ size = 13, color = '#9CAAA0', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="10" stroke={color} strokeWidth={strokeWidth}/>
    <polyline points="12,6 12,12 16,14" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconArrowRight = ({ size = 16, color = '#FFFFFF', strokeWidth = 2 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <line x1="5" y1="12" x2="19" y2="12" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <polyline points="12,5 19,12 12,19" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconWifi = ({ size = 20, color = '#22C55E', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M5 12.55a11 11 0 0 1 14.08 0" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M1.42 9a16 16 0 0 1 21.16 0" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M8.53 16.11a6 6 0 0 1 6.95 0" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <circle cx="12" cy="20" r="1" fill={color}/>
  </svg>
);

export const IconLightbulb = ({ size = 20, color = '#F59E0B', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M9 21h6M12 3a6 6 0 0 1 6 6c0 2.22-1.21 4.16-3 5.2V17a1 1 0 0 1-1 1H10a1 1 0 0 1-1-1v-2.8C7.21 13.16 6 11.22 6 9a6 6 0 0 1 6-6Z" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconSpray = ({ size = 20, color = '#3B82F6', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <rect x="2" y="3" width="5" height="5" rx="1" stroke={color} strokeWidth={strokeWidth} strokeLinejoin="round"/>
    <path d="M7 5.5h3a2 2 0 0 1 2 2V9" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <path d="M12 8h8" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <circle cx="17" cy="16" r="1.5" fill={color} opacity="0.7"/>
    <circle cx="20" cy="13" r="1.3" fill={color} opacity="0.6"/>
    <circle cx="21" cy="17" r="1" fill={color} opacity="0.4"/>
    <circle cx="14" cy="20" r="1" fill={color} opacity="0.4"/>
  </svg>
);

export const IconRotate = ({ size = 20, color = '#8B5CF6', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M2 12C2 6.48 6.48 2 12 2c3.31 0 6.24 1.56 8.16 4" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <path d="M22 12c0 5.52-4.48 10-10 10-3.31 0-6.24-1.56-8.16-4" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <polyline points="17,2 20,6 16,6" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <polyline points="7,22 4,18 8,18" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconEgg = ({ size = 20, color = '#2F6B3F', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <ellipse cx="12" cy="13.5" rx="6.5" ry="8.5" stroke={color} strokeWidth={strokeWidth}/>
    <path d="M8.5 10 Q12 7 15.5 10" stroke={color} strokeWidth={strokeWidth - 0.3} strokeLinecap="round" fill="none"/>
  </svg>
);

export const IconEggFilled = ({ size = 20, color = '#2F6B3F' }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <ellipse cx="12" cy="13.5" rx="6.5" ry="8.5" fill={color}/>
    <path d="M8.5 10 Q12 7 15.5 10" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
  </svg>
);

export const IconCalendar = ({ size = 18, color = '#5A6B5C', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <rect x="3" y="4" width="18" height="18" rx="3" stroke={color} strokeWidth={strokeWidth}/>
    <line x1="16" y1="2" x2="16" y2="6" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="8"  y1="2" x2="8"  y2="6" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="3"  y1="10" x2="21" y2="10" stroke={color} strokeWidth={strokeWidth}/>
  </svg>
);

export const IconCamera = ({ size = 20, color = '#52C97F', strokeWidth = 1.6 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <rect x="2" y="7" width="20" height="14" rx="3" stroke={color} strokeWidth={strokeWidth}/>
    <circle cx="12" cy="14" r="3.5" stroke={color} strokeWidth={strokeWidth}/>
    <path d="M8 7V5.5A1.5 1.5 0 0 1 9.5 4h5A1.5 1.5 0 0 1 16 5.5V7" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
  </svg>
);

export const IconWind = ({ size = 20, color = '#10B981', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M9.59 4.59A2 2 0 1 1 11 8H2" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M12.59 19.41A2 2 0 1 0 14 16H2" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M6.59 10.59A2 2 0 1 1 8 14H2" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconShield = ({ size = 20, color = '#2F6B3F', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" stroke={color} strokeWidth={strokeWidth} strokeLinejoin="round"/>
    <polyline points="9,12 11,14 15,10" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const IconTrendUp = ({ size = 16, color = '#22C55E', strokeWidth = 2 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <polyline points="23,6 13.5,15.5 8.5,10.5 1,18" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
    <polyline points="17,6 23,6 23,12" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

// ── Animal SVG Icons (zero emoji) ─────────────────────────────
export const IconChicken = ({ size = 36 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
    <ellipse cx="24" cy="32" rx="13" ry="10" fill="#D97706"/>
    <circle cx="24" cy="18" r="9" fill="#D97706"/>
    <ellipse cx="21" cy="27" rx="4" ry="5" fill="rgba(255,255,255,0.14)"/>
    <circle cx="21" cy="16" r="2.5" fill="white"/>
    <circle cx="21.8" cy="16.5" r="1" fill="#1A2B1C"/>
    <path d="M29 14 C32 10 36 13 33 17" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" fill="none"/>
    <path d="M19 28 L15 35 L19 32" fill="#B45309"/>
    <path d="M29 28 L33 35 L29 32" fill="#B45309"/>
    <ellipse cx="24" cy="41" rx="7" ry="2.5" fill="#F59E0B" opacity="0.5"/>
  </svg>
);

export const IconQuail = ({ size = 36 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
    <ellipse cx="24" cy="33" rx="11" ry="9" fill="#92400E"/>
    <circle cx="24" cy="18" r="8" fill="#92400E"/>
    <path d="M24 10 Q27 5 25 10" stroke="#92400E" strokeWidth="2.5" fill="#92400E" strokeLinecap="round"/>
    <circle cx="28" cy="9" r="2" fill="#78350F"/>
    <circle cx="21.5" cy="17" r="2.2" fill="white"/>
    <circle cx="22.2" cy="17.4" r="0.9" fill="#1A2B1C"/>
    <path d="M18 30 L14 37 L18 34" fill="#78350F"/>
    <path d="M30 30 L34 37 L30 34" fill="#78350F"/>
    <ellipse cx="24" cy="41" rx="6" ry="2" fill="#92400E" opacity="0.4"/>
  </svg>
);

export const IconDuck = ({ size = 36 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
    <ellipse cx="24" cy="34" rx="14" ry="9" fill="#1D4ED8"/>
    <circle cx="20" cy="18" r="8.5" fill="#1D4ED8"/>
    <ellipse cx="30" cy="21" rx="7" ry="4" fill="#1E40AF"/>
    <path d="M36 19.5 L43 21 L36 22.5" fill="#F59E0B"/>
    <circle cx="17.5" cy="16" r="2.5" fill="white"/>
    <circle cx="18.3" cy="16.4" r="1" fill="#1A2B1C"/>
    <path d="M17 31 L13 38 L17 35" fill="#1E40AF"/>
    <ellipse cx="24" cy="42" rx="8" ry="2.5" fill="#1D4ED8" opacity="0.4"/>
  </svg>
);

export const IconGoose = ({ size = 36 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
    <ellipse cx="24" cy="35" rx="13" ry="8" fill="#CBD5E1"/>
    <rect x="20" y="18" width="6" height="16" rx="3" fill="#CBD5E1"/>
    <circle cx="23" cy="14" r="7" fill="#CBD5E1"/>
    <path d="M27 12 L35 9 L29 14" fill="#F59E0B"/>
    <circle cx="20" cy="13" r="2.2" fill="white"/>
    <circle cx="20.8" cy="13.5" r="0.9" fill="#1A2B1C"/>
    <ellipse cx="18" cy="37" rx="5" ry="3" fill="#94A3B8" opacity="0.6"/>
    <ellipse cx="30" cy="37" rx="5" ry="3" fill="#94A3B8" opacity="0.6"/>
    <ellipse cx="24" cy="42" rx="8" ry="2" fill="#94A3B8" opacity="0.35"/>
  </svg>
);

export const IconTurkey = ({ size = 36 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
    <ellipse cx="24" cy="33" rx="12" ry="9" fill="#92400E"/>
    <circle cx="24" cy="19" r="8" fill="#92400E"/>
    <path d="M30 24 Q38 16 38 10" stroke="#D97706" strokeWidth="3.5" strokeLinecap="round" fill="none"/>
    <path d="M31 26 Q40 20 42 15" stroke="#EF4444" strokeWidth="3" strokeLinecap="round" fill="none"/>
    <path d="M29 28 Q38 26 40 22" stroke="#10B981" strokeWidth="3" strokeLinecap="round" fill="none"/>
    <circle cx="21.5" cy="17.5" r="2.2" fill="white"/>
    <circle cx="22.3" cy="18" r="0.9" fill="#1A2B1C"/>
    <path d="M26 14 C29 11 31 13 29 17" stroke="#EF4444" strokeWidth="1.8" strokeLinecap="round" fill="#EF4444" fillOpacity="0.7"/>
    <ellipse cx="24" cy="41" rx="7" ry="2" fill="#78350F" opacity="0.4"/>
  </svg>
);

export const IconUVLight = ({ size = 20, color = '#7C3AED', strokeWidth = 1.8 }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="4" stroke={color} strokeWidth={strokeWidth}/>
    <line x1="12" y1="2" x2="12" y2="5" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="12" y1="19" x2="12" y2="22" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="4.22" y1="4.22" x2="6.34" y2="6.34" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="17.66" y1="17.66" x2="19.78" y2="19.78" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="2" y1="12" x2="5" y2="12" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="19" y1="12" x2="22" y2="12" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="4.22" y1="19.78" x2="6.34" y2="17.66" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
    <line x1="17.66" y1="6.34" x2="19.78" y2="4.22" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"/>
  </svg>
);
