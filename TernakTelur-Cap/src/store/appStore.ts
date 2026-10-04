import { create } from 'zustand';
import { EggSpecies, IncubationPrograms, getIncubationPhase, getSystemStatus, SystemStatus, IncubationPhase } from '../constants/incubation';
import {
  fetchMqttSensor,
  fetchDeviceStates,
  fetchMyDevices,
  unclaimDevice,
  controlDevice,
  type DeviceName,
  type MyClaimedDevice,
} from '../services/api';

/** Lemari yang sudah di-claim oleh HP ini (disimpan lokal) */
export interface MyDevice {
  tetascoId: number;     // 1-15
  name: string;          // "Lemari #3" atau nama custom
  serverUrl: string;     // "https://tetasco.my.id"
  claimedAt: number;     // timestamp ms
}


export interface FarmerProfile {
  name: string; farmName: string; desa: string;
  kecamatan: string; kabupaten: string; provinsi: string;
  isProfileComplete: boolean; hasSeenOnboarding: boolean;
}

export interface TurningSchedule {
  enabled: boolean;
  intervalHours: number;   // balik tiap X jam (2–12)
  activeDays: number[];    // 0=Min, 1=Sen, ..., 6=Sab
  startHour: number;       // jam mulai operasional (0–23)
  endHour: number;         // jam selesai operasional (0–23)
  nextTurningAt: Date;
}
export interface IoTData {
  temperature: number; humidity: number;
  heaterOn: boolean; heater2On: boolean; fanOn: boolean; motorActive: boolean; humidifierOn: boolean;
  uvLightOn: boolean;
  nextTurningAt: Date; lastUpdated: Date;
}
export interface Incubator {
  id: string; name: string; species: EggSpecies;
  totalEggs: number; startDate: Date; estimatedHatchDate: Date;
  currentDay: number; phase: IncubationPhase; status: SystemStatus;
  iotData: IoTData; isActive: boolean; notes?: string;
  turningSchedule: TurningSchedule;
  /** ID integer dari tabel `tetasco` di PostgreSQL backend */
  backendId?: number;
}
export interface HistoryRecord {
  id: string; incubatorId: string; incubatorName: string;
  species: EggSpecies; totalEggs: number; hatchedEggs: number;
  startDate: Date; endDate: Date; success: boolean; notes?: string;
}
export interface Notification {
  id: string; type: 'info' | 'warning' | 'danger';
  title: string; message: string; timestamp: Date;
  read: boolean; incubatorId?: string;
}



interface AppState {
  farmer: FarmerProfile;
  setFarmer: (p: Partial<FarmerProfile>) => void;
  incubators: Incubator[];
  addIncubator: (inc: Omit<Incubator, 'id' | 'currentDay' | 'phase' | 'status' | 'turningSchedule'>) => void;
  updateIoTData: (id: string, data: Partial<IoTData>) => void;
  updateTurningSchedule: (id: string, patch: Partial<TurningSchedule>) => void;
  removeIncubator: (id: string) => void;
  finishIncubation: (id: string, hatched: number) => void;
  history: HistoryRecord[];
  notifications: Notification[];
  markRead: (id: string) => void;
  markAllRead: () => void;
  addNotification: (n: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  backendUrl: string;
  setBackendUrl: (url: string) => void;
  /** ID integer dari tabel `tetasco` di PostgreSQL (default 1) */
  tetascoId: number;
  setTetascoId: (id: number) => void;
  isConnected: boolean;    // server reachable
  deviceOnline: boolean;   // raspi lemari online (kirim heartbeat MQTT)
  setConnected: (v: boolean) => void;
  setDeviceOnline: (v: boolean) => void;

  manualModes: Record<string, boolean>;
  setManualMode: (id: string, manual: boolean) => void;
  /** Kontrol satu perangkat relay via backend (fire-and-forget) */
  sendDeviceCommand: (incId: string, device: DeviceName, on: boolean) => Promise<void>;
  _simInterval: ReturnType<typeof setInterval> | null;
  _sensorInterval: ReturnType<typeof setInterval> | null;
  /** Timestamp (ms) kapan terakhir user mengontrol device — skip poll selama 6 detik */
  _lastControlledAt: Record<string, number>;
  startSim: () => void;
  stopSim: () => void;
  startRealtime: () => void;
  stopRealtime: () => void;
  // ── Multi-Device Claim System ──────────────────────────────────
  /** UUID unik yang di-generate sekali saat install app */
  appId: string;
  /** Daftar lemari yang sudah diklaim oleh HP ini */
  myDevices: MyDevice[];
  addMyDevice: (device: MyDevice) => void;
  removeMyDevice: (tetascoId: number) => void;
  /** Sync daftar myDevices dari server (panggil setelah claim) */
  syncMyDevices: () => Promise<void>;
}


/** Generate UUID v4 sederhana */
function genUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
  });
}

// ── localStorage persistence keys ────────────────────────────────────────────
const STORAGE_APP_ID_KEY       = 'tetasco_app_id';
const STORAGE_DEVICES_KEY      = 'tetasco_my_devices';
const STORAGE_FARMER_KEY       = 'tetasco_farmer';
const STORAGE_INCUBATORS_KEY   = 'tetasco_incubators';

const persistedAppId      = localStorage.getItem(STORAGE_APP_ID_KEY) ?? genUUID();
if (!localStorage.getItem(STORAGE_APP_ID_KEY)) localStorage.setItem(STORAGE_APP_ID_KEY, persistedAppId);
const persistedDevices: MyDevice[] = JSON.parse(localStorage.getItem(STORAGE_DEVICES_KEY) ?? '[]');

// Farmer — persist agar onboarding tidak muncul lagi
const _defaultFarmer = { name: '', farmName: '', desa: '', kecamatan: '', kabupaten: '', provinsi: '', isProfileComplete: false, hasSeenOnboarding: false };
const persistedFarmer: typeof _defaultFarmer = {
  ..._defaultFarmer,
  ...JSON.parse(localStorage.getItem(STORAGE_FARMER_KEY) ?? '{}'),
};

// Incubators — persist agar tidak hilang saat reload
function _hydrateIncubator(raw: Record<string, unknown>): Incubator {
  return {
    ...raw,
    startDate:             new Date(raw.startDate as string),
    estimatedHatchDate:    new Date(raw.estimatedHatchDate as string),
    iotData: {
      ...(raw.iotData as Record<string, unknown>),
      nextTurningAt: new Date((raw.iotData as Record<string, unknown>).nextTurningAt as string),
      lastUpdated:   new Date((raw.iotData as Record<string, unknown>).lastUpdated   as string),
    },
    turningSchedule: {
      ...(raw.turningSchedule as Record<string, unknown>),
      nextTurningAt: new Date((raw.turningSchedule as Record<string, unknown>).nextTurningAt as string),
    },
  } as Incubator;
}
const persistedIncubators: Incubator[] = (
  JSON.parse(localStorage.getItem(STORAGE_INCUBATORS_KEY) ?? '[]') as Record<string, unknown>[]
).map(_hydrateIncubator);

export const useAppStore = create<AppState>((set, get) => ({

  farmer: persistedFarmer,
  setFarmer: (p) => set((s) => {
    const next = { ...s.farmer, ...p };
    localStorage.setItem(STORAGE_FARMER_KEY, JSON.stringify(next));
    return { farmer: next };
  }),

  backendUrl: 'https://tetasco.my.id',
  setBackendUrl: (url) => set({ backendUrl: url.replace(/\/$/, '') }),
  tetascoId: 1,
  setTetascoId: (id) => set({ tetascoId: id }),
  isConnected: false,
  deviceOnline: false,
  setConnected:     (v) => set({ isConnected: v }),
  setDeviceOnline:  (v) => set({ deviceOnline: v }),


  // ── Multi-Device Claim System ────────────────────────────────────────────
  appId:     persistedAppId,
  myDevices: persistedDevices,

  addMyDevice: (device) => set((s) => {
    const exists = s.myDevices.some(d => d.tetascoId === device.tetascoId);
    const next = exists
      ? s.myDevices.map(d => d.tetascoId === device.tetascoId ? device : d)
      : [...s.myDevices, device];
    localStorage.setItem(STORAGE_DEVICES_KEY, JSON.stringify(next));
    return { myDevices: next };
  }),

  removeMyDevice: (tetascoId) => {
    const { backendUrl, appId } = get();
    // Hapus dari lokal dulu (optimistic)
    set((s) => {
      const next = s.myDevices.filter(d => d.tetascoId !== tetascoId);
      localStorage.setItem(STORAGE_DEVICES_KEY, JSON.stringify(next));
      return { myDevices: next };
    });
    // Unclaim dari server (fire & forget)
    unclaimDevice(backendUrl, tetascoId, appId).catch(() => {});
  },

  syncMyDevices: async () => {
    const { backendUrl, appId, myDevices, addMyDevice } = get();
    try {
      const resp = await fetchMyDevices(backendUrl, appId);
      for (const d of resp.devices) {
        // Merge server data ke local (jika belum ada di lokal, tambah)
        const local = myDevices.find(m => m.tetascoId === d.tetascoId);
        if (!local) {
          addMyDevice({ tetascoId: d.tetascoId, name: d.name, serverUrl: backendUrl, claimedAt: d.claimedAt ?? Date.now() });
        }
      }
    } catch { /* silent */ }
  },

  manualModes: {},
  setManualMode: (id, manual) => {
    // 1. Update lokal state
    set((s) => ({ manualModes: { ...s.manualModes, [id]: manual } }));
    
    // 2. Beri tahu backend
    const { backendUrl, tetascoId } = get();
    if (backendUrl && tetascoId > 0) {
      fetch(`${backendUrl.replace(/\/$/, '')}/api/tetasco/${tetascoId}/auto-control/mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !manual }), // Jika manual = true, auto_control = false
      }).catch(() => { /* silent fail */ });
    }
  },

  sendDeviceCommand: async (incId, device, on) => {
    const { backendUrl, tetascoId, incubators, updateIoTData, _lastControlledAt } = get();
    // Optimistic UI update
    const deviceMap: Record<DeviceName, keyof import('../store/appStore').IoTData> = {
      'fan':        'fanOn',
      'heater-1':  'heaterOn',
      'heater-2':  'heater2On',
      'humidifier':'humidifierOn',
      'motor':     'motorActive',
      'uv':        'uvLightOn',
    };
    const field = deviceMap[device];
    if (field) updateIoTData(incId, { [field]: on } as Partial<import('../store/appStore').IoTData>);
    // Tandai waktu kontrol — pollDevices skip device ini selama 6 detik
    set({ _lastControlledAt: { ..._lastControlledAt, [device]: Date.now() } });
    try {
      await controlDevice(backendUrl, tetascoId, device, on);
    } catch (e) {
      console.warn('[API] controlDevice failed:', e);
      // Revert optimistic update on error
      if (field) updateIoTData(incId, { [field]: !on } as Partial<import('../store/appStore').IoTData>);
    }
  },

  incubators: persistedIncubators,
  addIncubator: (data) => {
    const p = IncubationPrograms[data.species];
    const nextTurn = new Date(Date.now() + p.turningFrequencyHours * 36e5);
    const schedule: TurningSchedule = {
      enabled: true,
      intervalHours: p.turningFrequencyHours,
      activeDays: [1, 2, 3, 4, 5, 6],
      startHour: 6,
      endHour: 20,
      nextTurningAt: nextTurn,
    };
    set((s) => {
      const next = [...s.incubators, {
        ...data, id: `inc-${Date.now()}`,
        currentDay: 0, phase: 'inkubasi' as IncubationPhase,
        status: 'normal' as SystemStatus, turningSchedule: schedule,
      }];
      localStorage.setItem(STORAGE_INCUBATORS_KEY, JSON.stringify(next));
      return { incubators: next };
    });

    const { backendUrl, tetascoId } = get();
    if (backendUrl && tetascoId > 0) {
      fetch(`${backendUrl.replace(/\/$/, '')}/api/tetasco/${tetascoId}/auto-control/species`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ species: data.species }),
      }).catch(() => {});
    }
  },
  updateTurningSchedule: (id, patch) => set((s) => ({
    incubators: s.incubators.map((inc) => {
      if (inc.id !== id) return inc;
      const updated = { ...inc.turningSchedule, ...patch };
      // Recalculate nextTurningAt if intervalHours changed
      if (patch.intervalHours !== undefined) {
        updated.nextTurningAt = new Date(Date.now() + patch.intervalHours * 36e5);
      }
      return { ...inc, turningSchedule: updated };
    }),
  })),
  updateIoTData: (id, data) => set((s) => ({
    incubators: s.incubators.map((inc) => {
      if (inc.id !== id) return inc;
      const iotData = { ...inc.iotData, ...data, lastUpdated: new Date() };
      const phase = getIncubationPhase(inc.currentDay, inc.species);
      const status = getSystemStatus(iotData.temperature, iotData.humidity, inc.species, phase);
      return { ...inc, iotData, status, phase };
    }),
  })),
  removeIncubator: (id) => {
    const { backendUrl, appId } = get();
    set((s) => {
      const inc = s.incubators.find(i => i.id === id);
      const next = s.incubators.filter(i => i.id !== id);
      localStorage.setItem(STORAGE_INCUBATORS_KEY, JSON.stringify(next));
      // Unclaim di server + hapus dari myDevices jika ada backendId
      if (inc?.backendId) {
        unclaimDevice(backendUrl, inc.backendId!, appId).catch(() => {});
        const nextDevices = s.myDevices.filter(d => d.tetascoId !== inc.backendId);
        localStorage.setItem(STORAGE_DEVICES_KEY, JSON.stringify(nextDevices));
        return { incubators: next, myDevices: nextDevices };
      }
      return { incubators: next };
    });
  },
  finishIncubation: (id, hatched) => {
    const inc = get().incubators.find((i) => i.id === id);
    if (!inc) return;
    const record: HistoryRecord = { id: `h-${Date.now()}`, incubatorId: id, incubatorName: inc.name, species: inc.species, totalEggs: inc.totalEggs, hatchedEggs: hatched, startDate: inc.startDate, endDate: new Date(), success: hatched / inc.totalEggs >= 0.7 };
    set((s) => ({ incubators: s.incubators.filter((i) => i.id !== id), history: [record, ...s.history] }));
  },

  history: [],
  notifications: [],

  markRead: (id) => set((s) => ({ notifications: s.notifications.map((n) => n.id === id ? { ...n, read: true } : n) })),
  markAllRead: () => set((s) => ({ notifications: s.notifications.map((n) => ({ ...n, read: true })) })),
  addNotification: (n) => set((s) => ({ notifications: [{ ...n, id: `n-${Date.now()}`, timestamp: new Date(), read: false }, ...s.notifications] })),

  _lastControlledAt: {},
  _simInterval: null,
  _sensorInterval: null,

  startSim: () => {
    get().stopSim();
    const interval = setInterval(() => {
      const { incubators, updateIoTData, updateTurningSchedule, addNotification } = get();
      const nowMs = Date.now();
      incubators.forEach((inc) => {
        if (!inc.isActive) return;
        const p = IncubationPrograms[inc.species];
        const phase = getIncubationPhase(inc.currentDay, inc.species);
        const tTarget = phase === 'hatching' ? p.targetTempHatching : p.targetTemp;
        const hTarget = phase === 'hatching' ? p.targetHumidityHatching : p.targetHumidity;
        const newTemp = +Math.max(tTarget - 1.5, Math.min(tTarget + 1.5, inc.iotData.temperature + (Math.random() - 0.5) * 0.2)).toFixed(1);
        const newHumid = Math.round(Math.max(hTarget - 10, Math.min(hTarget + 10, inc.iotData.humidity + (Math.random() - 0.5) * 1.5)));
        const oldStatus = inc.status;
        updateIoTData(inc.id, { temperature: newTemp, humidity: newHumid });
        const newStatus = getSystemStatus(newTemp, newHumid, inc.species, phase);
        if (oldStatus === 'normal' && newStatus === 'perlu_perhatian') {
          addNotification({ type: 'warning', title: 'Perlu Perhatian', message: `${inc.name} — kondisi mulai tidak ideal.`, incubatorId: inc.id });
        } else if (newStatus === 'berbahaya') {
          addNotification({ type: 'danger', title: '⚠️ Kondisi Berbahaya!', message: `${inc.name} — suhu atau kelembaban di luar batas aman!`, incubatorId: inc.id });
        }

        // Auto turning simulation
        const sched = inc.turningSchedule;
        if (sched.enabled && phase !== 'hatching') {
          const nowDate = new Date(nowMs);
          const dayOfWeek = nowDate.getDay();
          const hour = nowDate.getHours();
          const isDayActive = sched.activeDays.includes(dayOfWeek);
          const isHourActive = hour >= sched.startHour && hour < sched.endHour;
          const isDue = nowMs >= new Date(sched.nextTurningAt).getTime();
          if (isDue && isDayActive && isHourActive) {
            updateIoTData(inc.id, { motorActive: true });
            addNotification({ type: 'info', title: 'Pembalik Telur Aktif', message: `${inc.name} — motor sedang membalik telur.`, incubatorId: inc.id });
            const nextMs = nowMs + sched.intervalHours * 36e5;
            updateTurningSchedule(inc.id, { nextTurningAt: new Date(nextMs) });
            // Stop motor after 3 seconds (simulation)
            setTimeout(() => updateIoTData(inc.id, { motorActive: false }), 3000);
          }
        }
      });
    }, 5000);
    set({ _simInterval: interval });
  },
  stopSim: () => {
    const { _simInterval } = get();
    if (_simInterval) { clearInterval(_simInterval); set({ _simInterval: null }); }
  },

  /* ── Real-time polling dari Tetasco MQTT backend ── */
  startRealtime: () => {
    get().stopRealtime();
    get().stopSim();

    /**
     * Poll sensor MQTT real-time (tiap 5 detik)
     * Endpoint: GET /api/tetasco/{id}/sensor
     * Data update dari SHT20 tiap 10 detik via MQTT bridge.
     */
    const pollSensor = async () => {
      const { backendUrl, tetascoId, incubators, updateIoTData, setConnected, setDeviceOnline } = get();
      try {
        const sensor = await fetchMqttSensor(backendUrl, tetascoId);
        // Server reachable → connected = true, apapun status device
        setConnected(true);
        setDeviceOnline(!!sensor.online);
        if (!sensor.online) return;  // device offline, tapi server OK
        const inc = incubators.find(i => i.backendId === tetascoId) ?? incubators.find(i => i.isActive);
        if (inc && typeof sensor.temperature === 'number') {
          updateIoTData(inc.id, {
            temperature: sensor.temperature,
            humidity:    sensor.humidity ?? inc.iotData.humidity,
          });
        }
      } catch {
        // Server unreachable
        get().setConnected(false);
        get().setDeviceOnline(false);
      }
    };


    /**
     * Poll status aktuator (tiap 8 detik)
     * Endpoint: GET /api/tetasco/{id}/status
     */
    const pollDevices = async () => {
      const { backendUrl, tetascoId, incubators, updateIoTData, _lastControlledAt } = get();
      try {
        const states = await fetchDeviceStates(backendUrl, tetascoId);
        const inc = incubators.find(i => i.backendId === tetascoId) ?? incubators.find(i => i.isActive);
        if (inc) {
          const now = Date.now();
          const COOLDOWN_MS = 6000; // skip device yg baru dikontrol 6 detik lalu
          // Map device API name → field IoTData
          const deviceFieldMap: Record<string, { field: keyof typeof inc.iotData; value: boolean }> = {
            'fan':        { field: 'fanOn',        value: states.fan },
            'heater-1':   { field: 'heaterOn',     value: states.heater_1 },
            'heater-2':   { field: 'heater2On',    value: states.heater_2 },
            'humidifier': { field: 'humidifierOn', value: states.humidifier },
            'motor':      { field: 'motorActive',  value: states.motor },
            'uv':         { field: 'uvLightOn',    value: states.uv },
          };
          const patch: Partial<typeof inc.iotData> = {};
          for (const [dev, { field, value }] of Object.entries(deviceFieldMap)) {
            const lastCtrl = _lastControlledAt[dev] ?? 0;
            if (now - lastCtrl > COOLDOWN_MS) {
              // Tidak dikontrol baru-baru ini → boleh di-update dari server
              (patch as Record<string, boolean>)[field] = value;
            }
            // Jika baru dikontrol (< 6 detik) → skip, pertahankan optimistic state
          }
          if (Object.keys(patch).length > 0) updateIoTData(inc.id, patch);
        }
      } catch { /* silent — jangan putuskan koneksi jika hanya actuator gagal */ }
    };

    // Poll langsung lalu set interval
    pollSensor();
    pollDevices();
    const sensorInterval = setInterval(pollSensor,  5000);  // tiap 5 detik
    const deviceInterval = setInterval(pollDevices, 8000);  // tiap 8 detik
    set({ _sensorInterval: sensorInterval as ReturnType<typeof setInterval> });
    set({ _simInterval:    deviceInterval  as ReturnType<typeof setInterval> });
  },

  stopRealtime: () => {
    const { _simInterval, _sensorInterval } = get();
    if (_sensorInterval) { clearInterval(_sensorInterval); set({ _sensorInterval: null }); }
    if (_simInterval)    { clearInterval(_simInterval);    set({ _simInterval: null }); }
    set({ isConnected: false });
  },
}));
