"""
mqtt_bridge.py — MQTT Bridge untuk Tetasco Lemari (Non-invasif)
================================================================
Module ini TIDAK mengganti app.py yang sudah ada.
Ia hanya menambahkan MQTT subscriber di background thread,
menggunakan gpio_controller dan sensor yang sudah ada.

Cara pakai di app.py (tambahkan di bagian bawah import):
    from hardware.mqtt_bridge import mqtt_bridge
    mqtt_bridge.start(gpio_controller, sensor_manager=None)

Atau jalankan standalone:
    MQTT_PASS=lem1-xxx python -m hardware.mqtt_bridge
"""

import json
import logging
import os
import socket
import threading
import time

import paho.mqtt.client as mqtt

logger = logging.getLogger("MQTTBridge")

# ─── Konfigurasi dibaca LAZY di dalam start() agar .env dari app.py sudah dimuat ──
# Nilai default dipakai hanya saat standalone
_DEFAULT_DEVICE_ID = "lemari-1"
_DEFAULT_BROKER    = "tetasco.my.id"
_DEFAULT_PORT      = "443"
_DEFAULT_TRANSPORT = "websockets"


def _get_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


class MQTTBridge:
    """
    MQTT Bridge yang menggunakan gpio_controller yang sudah ada.
    Tidak mengganti Flask app — hanya menambah MQTT di background.
    """

    def __init__(self):
        self._client: mqtt.Client = None
        self._connected = False
        self._gpio = None
        self._sensor = None
        self._lock = threading.Lock()
        self._started = False
        # Diisi oleh start() setelah .env dimuat
        self._device_id       = _DEFAULT_DEVICE_ID
        self._topic_cmd_all   = f"tetasco/{_DEFAULT_DEVICE_ID}/command/#"
        self._topic_emstop    = "tetasco/ALL/command/emergency_stop"
        self._topic_status    = f"tetasco/{_DEFAULT_DEVICE_ID}/status"
        self._topic_sensor    = f"tetasco/{_DEFAULT_DEVICE_ID}/sensor"
        self._topic_heartbeat = f"tetasco/{_DEFAULT_DEVICE_ID}/heartbeat"
        self._sensor_interval    = 15
        self._heartbeat_interval = 30

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self, gpio_controller=None, sensor_manager=None):
        """
        Mulai MQTT bridge. Dipanggil dari app.py SETELAH .env dimuat.
        Semua config dibaca di sini agar env vars dari .env sudah aktif.
        """
        if self._started:
            logger.warning("[MQTTBridge] Sudah berjalan, skip start.")
            return
        self._gpio   = gpio_controller
        self._sensor = sensor_manager
        self._started = True

        # ── Baca konfigurasi SEKARANG (setelah .env dimuat oleh app.py) ──────
        device_id  = os.getenv("DEVICE_ID",           _DEFAULT_DEVICE_ID)
        broker     = os.getenv("MQTT_BROKER",         _DEFAULT_BROKER)
        port       = int(os.getenv("MQTT_PORT",       _DEFAULT_PORT))
        transport  = os.getenv("MQTT_TRANSPORT",      _DEFAULT_TRANSPORT)
        use_tls    = os.getenv("MQTT_USE_TLS",        "true").lower() == "true"
        user       = os.getenv("MQTT_USER",           device_id)
        password   = os.getenv("MQTT_PASS",           "change-me")
        ws_path    = os.getenv("MQTT_WEBSOCKET_PATH", "/mqtt")
        self._sensor_interval    = int(os.getenv("SENSOR_INTERVAL",    "15"))
        self._heartbeat_interval = int(os.getenv("HEARTBEAT_INTERVAL", "30"))

        # Simpan topics sebagai instance vars
        self._device_id      = device_id
        self._topic_cmd_all  = f"tetasco/{device_id}/command/#"
        self._topic_emstop   = "tetasco/ALL/command/emergency_stop"
        self._topic_status   = f"tetasco/{device_id}/status"
        self._topic_sensor   = f"tetasco/{device_id}/sensor"
        self._topic_heartbeat= f"tetasco/{device_id}/heartbeat"

        # ── Buat MQTT client ─────────────────────────────────────────────────
        client = mqtt.Client(
            client_id=f"{device_id}-bridge-{int(time.time())}",
            transport=transport,
            protocol=mqtt.MQTTv5,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )

        if transport == "websockets":
            client.ws_set_options(path=ws_path)

        if use_tls:
            import ssl
            client.tls_set(cert_reqs=ssl.CERT_REQUIRED)

        client.username_pw_set(user, password)
        client.on_connect    = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message    = self._on_message

        self._client = client
        self._broker = broker
        self._port   = port
        self._proto  = ("wss" if (transport == "websockets" and use_tls) else
                        "ws"  if transport == "websockets" else "tcp")

        # Background threads
        threading.Thread(target=self._sensor_loop,    daemon=True, name="mqtt-sensor").start()
        threading.Thread(target=self._heartbeat_loop, daemon=True, name="mqtt-heartbeat").start()
        threading.Thread(target=self._reconnect_watchdog, daemon=True, name="mqtt-watchdog").start()

        # Mulai koneksi MQTT (non-blocking) — SAMA seperti versi pertama yang berhasil
        client.connect_async(broker, port, keepalive=60)
        client.loop_start()
        logger.info("[MQTTBridge] Connecting → %s://%s:%d as %s (transport=%s)",
                    self._proto, broker, port, device_id, transport)

    @property
    def connected(self) -> bool:
        return self._connected

    def publish_status(self):
        """Publish status aktuator saat ini ke MQTT."""
        if not self._connected or not self._client:
            return
        try:
            if self._gpio:
                payload = self._gpio.get_all_actuators()
            else:
                payload = {}
            payload["ts"]        = int(time.time())
            payload["device_id"] = self._device_id
            self._client.publish(self._topic_status, json.dumps(payload), qos=1)
        except Exception as e:
            logger.error("[MQTTBridge] publish_status error: %s", e)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, rc, props=None):
        if rc == 0:
            self._connected = True
            logger.info("[MQTTBridge] Connected ke broker sebagai '%s'", self._device_id)
            client.subscribe(self._topic_cmd_all, qos=1)
            client.subscribe(self._topic_emstop,  qos=1)
            logger.info("[MQTTBridge] Subscribe: %s | %s", self._topic_cmd_all, self._topic_emstop)
            # JANGAN panggil publish_status() atau _publish_heartbeat() di sini!
            # Memanggil gpio.get_all_actuators() dari MQTT event loop thread bisa deadlock
            # dengan Flask request thread yang memegang GPIO lock.
            # Heartbeat & status loop di background thread yang handle ini.
        else:
            self._connected = False
            logger.warning("[MQTTBridge] Koneksi gagal rc=%d", rc)

    def _on_disconnect(self, client, userdata, flags, rc, props=None):
        self._connected = False
        logger.warning("[MQTTBridge] Terputus rc=%d, akan reconnect...", rc)

    def _on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        """Proses perintah dari server pusat → gpio_controller."""
        try:
            topic   = msg.topic
            payload = {}
            if msg.payload:
                try:
                    payload = json.loads(msg.payload.decode())
                except Exception:
                    payload = {}

            logger.info("[MQTTBridge] Terima: %s → %s", topic, payload)

            # Emergency stop SEMUA lemari
            if topic == self._topic_emstop or topic.endswith("/emergency_stop"):
                if self._gpio:
                    self._gpio.emergency_stop()
                    logger.warning("[MQTTBridge] EMERGENCY STOP!")
                self.publish_status()
                return

            # Command spesifik: tetasco/{id}/command/{actuator}
            parts = topic.split("/")
            if len(parts) == 4 and parts[0] == "tetasco" and parts[2] == "command":
                actuator = parts[3]
                state    = bool(payload.get("state", False))
                self._handle_command(actuator, state)
                self.publish_status()

        except Exception as e:
            logger.error("[MQTTBridge] Error proses pesan: %s", e)

    # ── Command Handler ───────────────────────────────────────────────────────

    def _handle_command(self, actuator: str, state: bool):
        """Kirim perintah ke gpio_controller yang sudah ada."""
        if not self._gpio:
            logger.warning("[MQTTBridge] gpio_controller belum di-inject, skip command '%s'", actuator)
            return

        # Daftar aktuator valid (termasuk alias)
        VALID = {
            "lamp_1", "lamp_2", "fan", "mist_maker", "uv_light",
            "heater",  # alias → lamp_1 + lamp_2
            "heater_1", "heater1", "lamp1",
            "heater_2", "heater2", "lamp2",
            "motor", "aux",        # → hydraulic_controller
            "humidifier", "mist",  # → mist_maker
            "uv", "lamp_uv",       # → uv_light
        }
        if actuator not in VALID:
            logger.warning("[MQTTBridge] Aktuator tidak dikenal: '%s'", actuator)
            return

        try:
            self._gpio.set_actuator(actuator, state)
            logger.info("[MQTTBridge] %s → %s", actuator, "ON" if state else "OFF")
        except Exception as e:
            logger.error("[MQTTBridge] Error set_actuator '%s': %s", actuator, e)

    # ── Background Loops ──────────────────────────────────────────────────────

    def _reconnect_watchdog(self):
        """Watchdog: reconnect jika koneksi terputus."""
        time.sleep(15)  # tunggu koneksi pertama
        retry_delay = 10
        while True:
            time.sleep(retry_delay)
            if self._client and not self._connected:
                logger.warning("[MQTTBridge] Terputus, mencoba reconnect ke %s:%d...",
                               self._broker, self._port)
                try:
                    self._client.reconnect()
                    retry_delay = min(retry_delay * 2, 120)
                except Exception as e:
                    logger.error("[MQTTBridge] Reconnect gagal: %s", e)
                    # Fallback: connect fresh
                    try:
                        self._client.connect_async(self._broker, self._port, 60)
                    except Exception:
                        pass
            else:
                retry_delay = 10

    def _sensor_loop(self):
        """Thread: kirim data sensor tiap interval detik."""
        time.sleep(10)  # tunggu koneksi established
        while True:
            try:
                if self._connected and self._client:
                    payload = self._build_sensor_payload()
                    if "temperature" in payload:
                        self._client.publish(self._topic_sensor, json.dumps(payload), qos=0)
            except Exception as e:
                logger.error("[MQTTBridge] sensor_loop error: %s", e)
            time.sleep(getattr(self, '_sensor_interval', 15))

    def _heartbeat_loop(self):
        """Thread: kirim heartbeat + status aktuator tiap interval."""
        time.sleep(5)
        while True:
            try:
                if self._connected and self._client:
                    self._publish_heartbeat()
                    # publish_status() aman di sini (bukan MQTT event loop thread)
                    self.publish_status()
            except Exception as e:
                logger.error("[MQTTBridge] heartbeat_loop error: %s", e)
            time.sleep(getattr(self, '_heartbeat_interval', 30))

    def _publish_heartbeat(self):
        if not self._connected or not self._client:
            return
        payload = {
            "ts":        int(time.time()),
            "device_id": self._device_id,
            "ip":        _get_ip(),
        }
        self._client.publish(self._topic_heartbeat, json.dumps(payload), qos=0)

    def _build_sensor_payload(self) -> dict:
        """
        Ambil data suhu & kelembaban dari sensor_manager.
        Mendukung SensorManager dari proyek Tetasco Lemari (SHT20 / DHT11).
        """
        payload = {
            "ts":        int(time.time()),
            "device_id": self._device_id,
        }

        if self._sensor:
            try:
                # Tambah sensor_type dari active_sensor_type attribute
                if hasattr(self._sensor, "active_sensor_type"):
                    payload["sensor_type"] = self._sensor.active_sensor_type

                # Coba dari sensor_manager (berbeda tiap proyek)
                if hasattr(self._sensor, "get_latest"):
                    data = self._sensor.get_latest()
                    payload.update(data)
                elif hasattr(self._sensor, "read"):
                    data = self._sensor.read()
                    payload.update(data)
                elif hasattr(self._sensor, "temperature") and hasattr(self._sensor, "humidity"):
                    payload["temperature"] = self._sensor.temperature
                    payload["humidity"]    = self._sensor.humidity
            except Exception as e:
                logger.debug("[MQTTBridge] Sensor read error: %s", e)
        # Fallback: kirim setidaknya status aktuator
        if "temperature" not in payload and self._gpio:
            payload["actuators"] = self._gpio.get_all_actuators()
        return payload


# Singleton
mqtt_bridge = MQTTBridge()


# ── Jalankan standalone (untuk test) ──────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    print("=" * 55)
    print(f"  MQTT Bridge Standalone Test")
    print(f"  Device ID : {DEVICE_ID}")
    print(f"  Broker    : wss://{MQTT_BROKER}:{MQTT_PORT}{MQTT_WS_PATH}")
    print(f"  User      : {MQTT_USER}")
    print("=" * 55)

    # Import gpio_controller dari proyek yang ada
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from hardware.gpio_controller import gpio_controller
        print("[OK] gpio_controller loaded (hardware mode)")
    except Exception as e:
        gpio_controller = None
        print(f"[WARN] gpio_controller tidak tersedia: {e} (simulasi)")

    mqtt_bridge.start(gpio_controller=gpio_controller)

    print("[INFO] MQTT Bridge berjalan. Ctrl+C untuk berhenti.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Stop.")
