import { useState, useEffect } from 'react';

/**
 * Splash screen with animated logo reveal.
 * Sequence: fade-in → scale up with bounce → shimmer → fade-out
 */
export function SplashScreen({ onFinish }: { onFinish: () => void }) {
  const [phase, setPhase] = useState<'enter' | 'shimmer' | 'exit'>('enter');

  useEffect(() => {
    // Phase 1: Logo enters (0 → 800ms)
    const t1 = setTimeout(() => setPhase('shimmer'), 800);
    // Phase 2: Shimmer / hold (800 → 2000ms)
    const t2 = setTimeout(() => setPhase('exit'), 2000);
    // Phase 3: Fade out then finish (2000 → 2600ms)
    const t3 = setTimeout(() => onFinish(), 2600);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, [onFinish]);

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: '#FFFFFF',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      opacity: phase === 'exit' ? 0 : 1,
      transition: 'opacity 0.6s ease-out',
    }}>
      {/* Soft radial glow behind logo */}
      <div style={{
        position: 'absolute',
        width: 280, height: 280, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(47,107,63,0.08) 0%, transparent 70%)',
        opacity: phase === 'enter' ? 0 : 1,
        transform: phase === 'enter' ? 'scale(0.5)' : 'scale(1)',
        transition: 'all 1s ease-out',
        pointerEvents: 'none',
      }} />

      {/* Logo */}
      <div style={{
        position: 'relative',
        opacity: phase === 'enter' ? 0 : 1,
        transform: phase === 'enter'
          ? 'scale(0.6) translateY(20px)'
          : 'scale(1) translateY(0px)',
        transition: 'all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)',
      }}>
        <img
          src="/logo-tetasco.png"
          alt="Tetasco Connect"
          style={{
            width: 140, height: 140,
            objectFit: 'contain',
            filter: 'drop-shadow(0 8px 24px rgba(47,107,63,0.15))',
          }}
        />

        {/* Shimmer overlay */}
        <div style={{
          position: 'absolute', inset: -10,
          overflow: 'hidden', borderRadius: 30,
          pointerEvents: 'none',
        }}>
          <div style={{
            position: 'absolute', top: 0, left: '-100%',
            width: '60%', height: '100%',
            background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent)',
            animation: phase === 'shimmer' ? 'splashShimmer 0.8s ease-in-out forwards' : 'none',
          }} />
        </div>
      </div>

      {/* App name — fades in after logo */}
      <div style={{
        marginTop: 20,
        opacity: phase === 'enter' ? 0 : 1,
        transform: phase === 'enter' ? 'translateY(12px)' : 'translateY(0)',
        transition: 'all 0.6s ease-out 0.3s',
        textAlign: 'center',
      }}>
        <h1 style={{
          fontSize: 22, fontWeight: 800, color: '#1A2B1C',
          letterSpacing: -0.5, lineHeight: 1.2,
        }}>
          Tetasco Connect
        </h1>
        <p style={{
          fontSize: 12, color: '#8A9E8C', fontWeight: 500,
          marginTop: 4, letterSpacing: 0.5,
        }}>
          Penetas Telur Cerdas
        </p>
      </div>

      {/* Bottom branding */}
      <div style={{
        position: 'absolute', bottom: 40,
        opacity: phase === 'enter' ? 0 : 0.4,
        transition: 'opacity 0.6s ease-out 0.5s',
        textAlign: 'center',
      }}>
        <p style={{ fontSize: 10, color: '#8A9E8C', letterSpacing: 1 }}>
          Smart Incubator System
        </p>
      </div>
    </div>
  );
}
