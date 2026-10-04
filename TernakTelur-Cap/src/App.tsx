import React, { useEffect, useState, useCallback } from 'react';
import { HashRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { useAppStore } from './store/appStore';
import { TabLayout } from './layouts/TabLayout';
import { Onboarding } from './screens/Onboarding';
import { ProfileSetup } from './screens/ProfileSetup';
import { Home } from './screens/Home';
import { Incubators } from './screens/Incubators';
import { Profile } from './screens/Profile';
import { DeviceControl } from './screens/DeviceControl';
import { EggSelect } from './screens/EggSelect';
import { IncubatorMonitor } from './screens/IncubatorMonitor';
import { Notifications } from './screens/Notifications';
import { SplashScreen } from './screens/SplashScreen';
import { AddDevice } from './screens/AddDevice';
import { CameraStream } from './screens/CameraStream';
import { ShareDevice } from './screens/ShareDevice';

import { fetchHealth } from './services/api';


/** Redirect ke onboarding / profile-setup jika belum selesai */
function Guard() {
  const { farmer } = useAppStore();
  if (!farmer.hasSeenOnboarding) return <Navigate to="/onboarding" replace />;
  if (!farmer.isProfileComplete) return <Navigate to="/profile-setup" replace />;
  return <Outlet />;
}

/**
 * Hanya aktif saat app berjalan di Raspi (hostname = 127.0.0.1)
 * Poll /api/claim-status setiap 45 detik.
 * Jika lemari di-unclaim dari HP → redirect ke /pair (welcome screen).
 */
function useRaspiUnclaimWatcher() {
  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        // Cek via relative URL — hanya berhasil jika running di Raspi (port 5001)
        // Di Android (capacitor://localhost), fetch ini akan gagal dan di-catch
        const res = await fetch('/api/claim-status', { cache: 'no-store' });
        if (res.ok) {
          const d = await res.json();
          if (!d.claimed && !cancelled) {
            console.log('[Tetasco] Lemari di-unclaim dari HP → redirect ke /pair');
            window.location.replace('/pair');
          }
        }
      } catch { /* Android/offline: fetch gagal, abaikan */ }
    };

    // Cek pertama kali setelah 8 detik, lalu setiap 30 detik
    const timeout = setTimeout(check, 8000);
    const interval = setInterval(check, 30_000);
    return () => { cancelled = true; clearTimeout(timeout); clearInterval(interval); };
  }, []);
}

export default function App() {
  const { startSim, stopSim, startRealtime, stopRealtime, backendUrl, farmer } = useAppStore();
  const [showSplash, setShowSplash] = useState(true);
  const hideSplash = useCallback(() => setShowSplash(false), []);

  // Deteksi unclaim dari HP saat running di Raspi
  useRaspiUnclaimWatcher();

  useEffect(() => {
    /**
     * Auto-detect: coba koneksi real ke https://tetasco.my.id
     * Jika berhasil → startRealtime() (data dari SHT20 via MQTT)
     * Jika gagal    → startSim() (simulasi untuk demo/offline)
     */
    let cancelled = false;
    const init = async () => {
      try {
        const online = await fetchHealth(backendUrl);
        if (cancelled) return;
        if (online) {
          console.log('[Tetasco] ✅ Backend MQTT online → startRealtime()');
          startRealtime();
        } else {
          console.log('[Tetasco] ⚠️ Backend offline → startSim()');
          startSim();
        }
      } catch {
        if (!cancelled) {
          console.log('[Tetasco] ❌ Koneksi gagal → startSim()');
          startSim();
        }
      }
    };
    init();
    return () => {
      cancelled = true;
      stopSim();
      stopRealtime();
    };
  }, []);

  if (showSplash) {
    return (
      <div className="app-shell">
        <SplashScreen onFinish={hideSplash} />
      </div>
    );
  }

  return (
    <div className="app-shell">
      <HashRouter>
        <Routes>
          {/* Halaman publik — tidak perlu guard */}
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/profile-setup" element={<ProfileSetup />} />

          {/* Halaman yang butuh guard */}
          <Route element={<Guard />}>
            <Route path="/notifications"       element={<Notifications />} />
            <Route path="/incubator/egg-select" element={<EggSelect />} />
            <Route path="/incubator/add-device" element={<AddDevice />} />
            <Route path="/incubator/:id"        element={<IncubatorMonitor />} />
            <Route path="/camera"              element={<CameraStream />} />
            <Route path="/share/:id"           element={<ShareDevice />} />


            <Route element={<TabLayout />}>
              <Route path="/" element={<Home />} />
              <Route path="/incubators" element={<Incubators />} />
              <Route path="/control" element={<DeviceControl />} />
              <Route path="/profile" element={<Profile />} />
            </Route>
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to={farmer.hasSeenOnboarding ? '/' : '/onboarding'} replace />} />
        </Routes>
      </HashRouter>
    </div>
  );
}
