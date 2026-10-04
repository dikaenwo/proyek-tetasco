/* ──────────────────────────────────────────────────────────────
   Tetasco Connect — Backend API Service  (v2 — MQTT Backend)
   Base URL : https://tetasco.my.id  (Cloudflare → Nginx → FastAPI)
   Sensor   : Real-time via MQTT broker (SHT20 tiap 10 detik)
   Control  : POST /api/tetasco/{id}/devices/{actuator}/{on|off}
   ────────────────────────────────────────────────────────────── */

const TIMEOUT_MS = 8000;

// ─── Low-level fetch with timeout ───────────────────────────────
async function apiFetch<T = unknown>(
  baseUrl: string,
  path: string,
  options?: RequestInit,
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(`${baseUrl}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers ?? {}),
      },
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`HTTP ${res.status}: ${text}`);
    }
    if (res.status === 204) return {} as T;
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

// ═══════════════════════════════════════════════════════════════
//  TYPES
// ═══════════════════════════════════════════════════════════════

export interface TetascoDevice {
  id: number;
  name: string;
  status: string;
  user_id: number;
  created_at: string;
  user?: { id: number; name: string; email: string };
}

export interface SensorReading {
  temperature: number;
  humidity: number;
  recorded_at?: string;
}

export interface SensorHistory {
  id: number;
  tetasco_id: number;
  temperature: number;
  humidity: number;
  recorded_at: string;
}

/** Response dari /api/tetasco/{id}/sensor (MQTT real-time) */
export interface MqttSensorResponse {
  device_id: string;
  tetasco_id: number;
  online: boolean;
  temperature: number | null;
  humidity: number | null;
  sensor_type: string;
  is_hardware: boolean;
  sensor_status: string;   // "hardware_ok" | "unknown"
  actuators: Record<string, boolean | string>;
  ts: number;
  last_updated: number;
  message?: string;        // ada jika offline
}

/** Response dari /api/devices */
export interface DeviceInfo {
  device_id: string;
  tetasco_id: number;
  online: boolean;
  ip: string;
  last_seen: number;
  temperature: number | null;
  humidity: number | null;
  sensor_type: string;
}

export interface AllDevicesResponse {
  total: number;
  devices: DeviceInfo[];
}

/** Status device lengkap dari /api/tetasco/{id}/status */
export interface DeviceStatusResponse {
  device_id: string;
  tetasco_id: number;
  online: boolean;
  last_seen: number;
  ip: string;
  actuators: Record<string, boolean | string>;
  sensor: {
    temperature: number | null;
    humidity: number | null;
    sensor_type: string;
    is_hardware: boolean;
  } | null;
}

/** Logical device states (normalized) */
export interface DeviceStates {
  heater_1: boolean;
  heater_2: boolean;
  fan: boolean;
  humidifier: boolean;
  motor: boolean;
  uv: boolean;
}

export interface HardwareStates {
  heater_1?: boolean;
  fan?: boolean;
  humidifier?: boolean;
  motor?: boolean;
  [key: string]: boolean | undefined;
}

/**
 * Device names sesuai VALID_ACTUATORS di server MQTT:
 * fan | heater | heater2 | humidifier | motor | uv_light
 */
export type DeviceName = 'fan' | 'heater-1' | 'heater-2' | 'humidifier' | 'motor' | 'uv';

/** Map DeviceName (internal) → actuator string (server API) */
const DEVICE_NAME_MAP: Record<DeviceName, string> = {
  'fan':        'fan',
  'heater-1':  'heater',    // server: heater
  'heater-2':  'heater2',   // server: heater2
  'humidifier':'humidifier',
  'motor':     'motor',
  'uv':        'uv_light',  // server: uv_light
};

// ═══════════════════════════════════════════════════════════════
//  HEALTH
// ═══════════════════════════════════════════════════════════════

/** GET /api/health — returns true jika API + MQTT online */
export async function fetchHealth(baseUrl: string): Promise<boolean> {
  try {
    const r = await apiFetch<{ status: string; mqtt_connected: boolean }>(baseUrl, '/api/health');
    return r.status === 'ok' && r.mqtt_connected === true;
  } catch {
    return false;
  }
}

/** GET /api/database/health — legacy, tidak dipakai di MQTT backend */
export async function fetchDbHealth(baseUrl: string): Promise<boolean> {
  return fetchHealth(baseUrl);
}

// ═══════════════════════════════════════════════════════════════
//  SENSOR — MQTT real-time
// ═══════════════════════════════════════════════════════════════

/**
 * GET /api/tetasco/{id}/sensor
 * Sensor MQTT real-time — update tiap 10 detik dari SHT20 Raspi.
 * Ini endpoint utama untuk monitoring suhu & kelembaban.
 */
export async function fetchMqttSensor(
  baseUrl: string,
  tetascoId: number,
): Promise<MqttSensorResponse> {
  return apiFetch<MqttSensorResponse>(baseUrl, `/api/tetasco/${tetascoId}/sensor`);
}

/**
 * Alias: readSensorFromHardware → sekarang pakai MQTT endpoint
 * Tetap diexport agar kompatibel dengan kode lama di appStore.
 */
export async function readSensorFromHardware(
  baseUrl: string,
  tetascoId: number,
): Promise<SensorReading> {
  const data = await fetchMqttSensor(baseUrl, tetascoId);
  if (!data.online || data.temperature === null) {
    throw new Error('Lemari offline atau belum ada data sensor');
  }
  return {
    temperature: data.temperature,
    humidity: data.humidity ?? 0,
  };
}

/** GET /api/tetasco/{id}/sensors — legacy alias */
export async function fetchLatestSensor(
  baseUrl: string,
  tetascoId: number,
): Promise<SensorReading> {
  return readSensorFromHardware(baseUrl, tetascoId);
}

/** GET /api/sensors — data sensor semua lemari online */
export async function fetchAllSensors(
  baseUrl: string,
): Promise<MqttSensorResponse[]> {
  return apiFetch<MqttSensorResponse[]>(baseUrl, '/api/sensors');
}

/** POST /api/tetasco/{id}/sensors/history — legacy, simpan ke DB jika ada */
export async function saveSensorHistory(
  baseUrl: string,
  tetascoId: number,
  data: { temperature: number; humidity: number },
): Promise<SensorHistory> {
  return apiFetch<SensorHistory>(baseUrl, `/api/tetasco/${tetascoId}/sensors/history`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/** GET /api/tetasco/{id}/sensors/history — histori sensor dari DB */
export async function fetchSensorHistory(
  baseUrl: string,
  tetascoId: number,
): Promise<SensorHistory[]> {
  return apiFetch<SensorHistory[]>(baseUrl, `/api/tetasco/${tetascoId}/sensors/history`);
}

// ═══════════════════════════════════════════════════════════════
//  DEVICE STATUS & CONTROL
// ═══════════════════════════════════════════════════════════════

/**
 * GET /api/tetasco/{id}/status
 * Status lengkap device: actuators + sensor terbaru
 */
export async function fetchDeviceStatus(
  baseUrl: string,
  tetascoId: number,
): Promise<DeviceStatusResponse> {
  return apiFetch<DeviceStatusResponse>(baseUrl, `/api/tetasco/${tetascoId}/status`);
}

/**
 * GET /api/tetasco/{id}/status → extract DeviceStates (normalized)
 * Alias agar kompatibel dengan kode lama yang pakai fetchDeviceStates.
 */
export async function fetchDeviceStates(
  baseUrl: string,
  tetascoId: number,
): Promise<DeviceStates> {
  const status = await fetchDeviceStatus(baseUrl, tetascoId);
  const acts = status.actuators ?? {};
  return {
    heater_1:   Boolean(acts['heater']   ?? acts['heater_1'] ?? acts['heater1'] ?? false),
    heater_2:   Boolean(acts['heater2']  ?? acts['heater_2'] ?? false),
    fan:        Boolean(acts['fan']      ?? false),
    humidifier: Boolean(acts['humidifier'] ?? false),
    motor:      Boolean(acts['motor']    ?? false),
    uv:         Boolean(acts['uv_light'] ?? acts['uv'] ?? false),
  };
}

/** GET /api/tetasco/{id}/hardware — legacy alias */
export async function fetchHardwareStates(
  baseUrl: string,
  tetascoId: number,
): Promise<HardwareStates> {
  const states = await fetchDeviceStates(baseUrl, tetascoId);
  return {
    heater_1:   states.heater_1,
    fan:        states.fan,
    humidifier: states.humidifier,
    motor:      states.motor,
  };
}

/**
 * GET /api/devices — daftar semua lemari beserta sensor terbaru
 */
export async function fetchAllDevices(
  baseUrl: string,
): Promise<AllDevicesResponse> {
  return apiFetch<AllDevicesResponse>(baseUrl, '/api/devices');
}

// ═══════════════════════════════════════════════════════════════
//  ACTUATOR CONTROL (via MQTT)
// ═══════════════════════════════════════════════════════════════

/**
 * POST /api/tetasco/{id}/devices/{actuator}/{on|off}
 * Kirim perintah ON/OFF ke relay Raspi via MQTT broker.
 * device: 'fan'|'heater-1'|'heater-2'|'humidifier'|'motor'|'uv'
 */
export async function controlDevice(
  baseUrl: string,
  tetascoId: number,
  device: DeviceName,
  state: boolean,
): Promise<void> {
  const action   = state ? 'on' : 'off';
  const apiName  = DEVICE_NAME_MAP[device] ?? device;  // normalize ke nama API server
  await apiFetch(baseUrl, `/api/tetasco/${tetascoId}/devices/${apiName}/${action}`, {
    method: 'POST',
    body: '{}',
  });
}

/** Shorthand helpers */
export const controlFan        = (url: string, id: number, on: boolean) => controlDevice(url, id, 'fan', on);
export const controlHeater1    = (url: string, id: number, on: boolean) => controlDevice(url, id, 'heater-1', on);
export const controlHeater2    = (url: string, id: number, on: boolean) => controlDevice(url, id, 'heater-2', on);
export const controlHumidifier = (url: string, id: number, on: boolean) => controlDevice(url, id, 'humidifier', on);
export const controlMotor      = (url: string, id: number, on: boolean) => controlDevice(url, id, 'motor', on);
export const controlUV         = (url: string, id: number, on: boolean) => controlDevice(url, id, 'uv', on);

/**
 * POST /api/tetasco/{id}/devices/emergency-stop
 * Matikan SEMUA relay sekaligus
 */
export async function emergencyStop(
  baseUrl: string,
  tetascoId: number,
): Promise<void> {
  await apiFetch(baseUrl, `/api/tetasco/${tetascoId}/devices/emergency-stop`, {
    method: 'POST',
    body: '{}',
  });
}

/**
 * POST /api/emergency-stop-all
 * Matikan relay SEMUA lemari sekaligus
 */
export async function emergencyStopAll(baseUrl: string): Promise<void> {
  await apiFetch(baseUrl, '/api/emergency-stop-all', { method: 'POST', body: '{}' });
}

// ═══════════════════════════════════════════════════════════════
//  LEGACY — endpoint lama (kept for backward compat)
// ═══════════════════════════════════════════════════════════════

export async function fetchAllTetasco(baseUrl: string): Promise<TetascoDevice[]> {
  // Tidak ada di MQTT backend — return kosong
  console.warn('[API] fetchAllTetasco: endpoint tidak tersedia di MQTT backend');
  return [];
}

export async function fetchTetasco(baseUrl: string, tetascoId: number): Promise<TetascoDevice> {
  console.warn('[API] fetchTetasco: endpoint tidak tersedia di MQTT backend');
  return { id: tetascoId, name: `Lemari ${tetascoId}`, status: 'active', user_id: 1, created_at: '' };
}

// ═══════════════════════════════════════════════════════════════
//  CLAIM SYSTEM — Multi-Tenant Pairing via QR Code
// ═══════════════════════════════════════════════════════════════

export interface ClaimTokenResponse {
  tetascoId: number;
  token: string;
  qrData: string;   // "tetasco://claim?id=1&token=37E7EAAF"
}

export interface MyClaimedDevice {
  tetascoId: number;
  deviceId: string;      // "lemari-3"
  name: string;
  claimedAt: number;
  online: boolean;
  temperature: number | null;
  humidity: number | null;
  ip: string | null;
}

export interface MyDevicesResponse {
  total: number;
  devices: MyClaimedDevice[];
}

/**
 * GET /api/tetasco/{id}/claim-token
 * Ambil claim token + QR data untuk lemari tertentu.
 * Dipanggil oleh Raspi untuk generate QR di layar HDMI.
 */
export async function fetchClaimToken(
  baseUrl: string,
  tetascoId: number,
): Promise<ClaimTokenResponse> {
  return apiFetch<ClaimTokenResponse>(baseUrl, `/api/tetasco/${tetascoId}/claim-token`);
}

/**
 * POST /api/claim
 * Klaim lemari ke app ini (appId = UUID dari HP).
 * Dipanggil setelah scan QR di Raspi.
 */
export async function claimDevice(
  baseUrl: string,
  payload: {
    tetascoId: number;
    claimToken: string;   // dari QR code
    appId: string;        // UUID unik HP
    farmName?: string;
  },
): Promise<{ ok: boolean; deviceId: string; name: string; message: string }> {
  return apiFetch(baseUrl, '/api/claim', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * GET /api/my-devices?appId=xxx
 * Daftar semua lemari yang diklaim oleh HP ini (appId).
 */
export async function fetchMyDevices(
  baseUrl: string,
  appId: string,
): Promise<MyDevicesResponse> {
  return apiFetch<MyDevicesResponse>(baseUrl, `/api/my-devices?appId=${encodeURIComponent(appId)}`);
}

/**
 * DELETE /api/claim/{tetascoId}?appId=xxx
 * Lepas klaim lemari dari app ini.
 */
export async function unclaimDevice(
  baseUrl: string,
  tetascoId: number,
  appId: string,
): Promise<{ ok: boolean; message: string }> {
  return apiFetch(baseUrl, `/api/claim/${tetascoId}?appId=${encodeURIComponent(appId)}`, {
    method: 'DELETE',
  });
}

