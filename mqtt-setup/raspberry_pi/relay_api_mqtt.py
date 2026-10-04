"""
relay_api_mqtt.py — TernakTelur Raspi Lemari (Flask + gpiozero + MQTT)
=======================================================================
Versi baru relay_api.py yang ditambahkan MQTT subscriber.

MQTT:
  - Connect ke wss://tetasco.my.id/mqtt (Nginx → Mosquitto WebSocket, GRATIS!)
  - Subscribe: tetasco/{DEVICE_ID}/command/#
  - Publish:   tetasco/{DEVICE_ID}/status    (setelah eksekusi command)
               tetasco/{DEVICE_ID}/sensor    (tiap SENSOR_INTERVAL detik)
               tetasco/{DEVICE_ID}/heartbeat (tiap HEARTBEAT_INTERVAL detik)

Cara pakai:
  DEVICE_ID=lemari-1 MQTT_PASS=secret python relay_api_mqtt.py

Hardware (VCC Relay = 3.3V dari Pi):
  GPIO 22 = Heater 1   (Active-LOW)
  GPIO  6 = Heater 2   (Active-HIGH)
  GPIO 26 = Fan        (Active-HIGH)
  GPIO  4 = Humidifier (Active-HIGH)
  GPIO 13 = Motor      (Active-HIGH)
  GPIO 19 = UV Light   (Active-HIGH)
"""

import json
import logging
import os
import random
import socket
import threading
import time
import atexit

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from gpiozero import DigitalOutputDevice
    GPIO_AVAILABLE = True
except (ImportError, Exception):
    GPIO_AVAILABLE = False
    print("[WARN] gpiozero tidak tersedia, berjalan dalam mode simulasi.")

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Konfigurasi ─────────────────────────────────────────────────────────────
DEVICE_ID          = os.getenv("DEVICE_ID", "lemari-1")     # WAJIB diubah tiap Raspi!
FLASK_PORT         = int(os.getenv("FLASK_PORT", "5001"))

MQTT_BROKER        = os.getenv("MQTT_BROKER", "tetasco.my.id")   # domain utama
MQTT_PORT          = int(os.getenv("MQTT_PORT", "443"))           # WSS via Cloudflare
MQTT_TRANSPORT     = os.getenv("MQTT_TRANSPORT", "websockets")
MQTT_USE_TLS       = os.getenv("MQTT_USE_TLS", "true").lower() == "true"
MQTT_USER          = os.getenv("MQTT_USER", DEVICE_ID)            # username = device id
MQTT_PASS          = os.getenv("MQTT_PASS", "change-me")
MQTT_WEBSOCKET_PATH = os.getenv("MQTT_WEBSOCKET_PATH", "/mqtt")  # Nginx proxy path

SENSOR_INTERVAL    = int(os.getenv("SENSOR_INTERVAL", "10"))    # detik kirim sensor
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "30")) # detik heartbeat

# ─── Topik MQTT ───────────────────────────────────────────────────────────────
TOPIC_COMMAND    = f"tetasco/{DEVICE_ID}/command/#"
TOPIC_STATUS     = f"tetasco/{DEVICE_ID}/status"
TOPIC_SENSOR     = f"tetasco/{DEVICE_ID}/sensor"
TOPIC_HEARTBEAT  = f"tetasco/{DEVICE_ID}/heartbeat"
TOPIC_EMSTOP_ALL = "tetasco/ALL/command/emergency_stop"

# ─── GPIO Setup ───────────────────────────────────────────────────────────────
GPIO_CONFIG = {
    "heater":     {"pin": 22, "active_high": False},
    "heater2":    {"pin": 6,  "active_high": True},
    "fan":        {"pin": 26, "active_high": True},
    "humidifier": {"pin": 4,  "active_high": True},
    "motor":      {"pin": 13, "active_high": True},
    "uv_light":   {"pin": 19, "active_high": True},
}

devices = {}
if GPIO_AVAILABLE:
    for name, cfg in GPIO_CONFIG.items():
        try:
            devices[name] = DigitalOutputDevice(
                cfg["pin"], active_high=cfg["active_high"], initial_value=False
            )
            logger.info(f"[GPIO] {name} GPIO {cfg['pin']} siap")
        except Exception as e:
            logger.warning(f"[GPIO] Gagal init {name}: {e}")

# ─── State Aktuator ───────────────────────────────────────────────────────────
actuator_state: dict[str, bool] = {k: False for k in GPIO_CONFIG}
_base_temp  = 37.5
_base_humid = 60.0
_state_lock = threading.Lock()


def _write_gpio(name: str, state: bool):
    dev = devices.get(name)
    if dev:
        dev.on() if state else dev.off()


def _set_actuator(name: str, state: bool):
    with _state_lock:
        actuator_state[name] = state
    _write_gpio(name, state)
    logger.info(f"[Aktuator] {name} → {'ON' if state else 'OFF'}")


def _emergency_stop():
    with _state_lock:
        for k in actuator_state:
            actuator_state[k] = False
    for k in GPIO_CONFIG:
        _write_gpio(k, False)
    logger.warning("[EMERGENCY STOP] Semua aktuator dimatikan!")


# ─── MQTT Client ──────────────────────────────────────────────────────────────
_mqtt_client: mqtt.Client = None
_mqtt_connected = False


def _mqtt_on_connect(client, userdata, flags, rc, props=None):
    global _mqtt_connected
    if rc == 0:
        _mqtt_connected = True
        logger.info(f"[MQTT] Terhubung ke broker sebagai {DEVICE_ID}")
        client.subscribe(TOPIC_COMMAND,    qos=1)
        client.subscribe(TOPIC_EMSTOP_ALL, qos=1)
        # Kirim heartbeat langsung setelah connect
        _publish_heartbeat(client)
    else:
        _mqtt_connected = False
        logger.warning(f"[MQTT] Koneksi gagal rc={rc}")


def _mqtt_on_disconnect(client, userdata, flags, rc, props=None):
    global _mqtt_connected
    _mqtt_connected = False
    logger.warning(f"[MQTT] Terputus rc={rc}, akan reconnect...")


def _mqtt_on_message(client, userdata, msg: mqtt.MQTTMessage):
    """Proses perintah dari server pusat."""
    try:
        topic   = msg.topic
        payload = json.loads(msg.payload.decode()) if msg.payload else {}
        logger.info(f"[MQTT] Terima: {topic} → {payload}")

        # Emergency stop untuk semua
        if topic == TOPIC_EMSTOP_ALL or topic.endswith("/emergency_stop"):
            _emergency_stop()
            _publish_status(client)
            return

        # Parse command topik: tetasco/{id}/command/{actuator}
        parts = topic.split("/")
        if len(parts) == 4 and parts[2] == "command":
            actuator = parts[3]
            if actuator in actuator_state:
                state = bool(payload.get("state", False))
                _set_actuator(actuator, state)
                _publish_status(client)
            else:
                logger.warning(f"[MQTT] Aktuator tidak dikenal: {actuator}")
    except Exception as e:
        logger.error(f"[MQTT] Error proses pesan: {e}")


def _publish_status(client):
    """Kirim status semua aktuator ke server."""
    with _state_lock:
        payload = dict(actuator_state)
    payload["ts"] = int(time.time())
    client.publish(TOPIC_STATUS, json.dumps(payload), qos=1)


def _publish_heartbeat(client):
    """Kirim heartbeat ke server."""
    payload = {
        "ts":        int(time.time()),
        "device_id": DEVICE_ID,
        "ip":        _get_local_ip(),
        "uptime":    time.monotonic(),
    }
    client.publish(TOPIC_HEARTBEAT, json.dumps(payload), qos=0)


def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def _sensor_loop(client):
    """Thread: kirim data sensor tiap SENSOR_INTERVAL detik."""
    while True:
        try:
            # Baca sensor nyata di sini (ganti dengan pembacaan DHT22 / DS18B20)
            temp  = round(_base_temp  + random.uniform(-0.5, 0.5), 1)
            humid = round(_base_humid + random.uniform(-2.0, 2.0), 1)
            payload = {
                "temperature": temp,
                "humidity":    humid,
                "ts":          int(time.time()),
                "device_id":   DEVICE_ID,
            }
            if _mqtt_connected:
                client.publish(TOPIC_SENSOR, json.dumps(payload), qos=0)
                logger.debug(f"[Sensor] Publish: {payload}")
        except Exception as e:
            logger.error(f"[Sensor] Error: {e}")
        time.sleep(SENSOR_INTERVAL)


def _heartbeat_loop(client):
    """Thread: kirim heartbeat tiap HEARTBEAT_INTERVAL detik."""
    while True:
        try:
            if _mqtt_connected:
                _publish_heartbeat(client)
        except Exception as e:
            logger.error(f"[Heartbeat] Error: {e}")
        time.sleep(HEARTBEAT_INTERVAL)


def start_mqtt():
    """Inisialisasi dan jalankan MQTT client di background thread."""
    global _mqtt_client

    client = mqtt.Client(
        client_id=f"{DEVICE_ID}-{int(time.time())}",
        transport=MQTT_TRANSPORT,
        protocol=mqtt.MQTTv5,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )

    if MQTT_TRANSPORT == "websockets":
        client.ws_set_options(path=MQTT_WEBSOCKET_PATH)

    if MQTT_USE_TLS:
        import ssl
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED)

    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect    = _mqtt_on_connect
    client.on_disconnect = _mqtt_on_disconnect
    client.on_message    = _mqtt_on_message
    client.reconnect_delay_set(min_delay=3, max_delay=60)

    _mqtt_client = client

    # Sensor & heartbeat threads
    threading.Thread(target=_sensor_loop,    args=(client,), daemon=True).start()
    threading.Thread(target=_heartbeat_loop, args=(client,), daemon=True).start()

    client.connect_async(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    logger.info(f"[MQTT] Connecting → {MQTT_BROKER}:{MQTT_PORT} (transport={MQTT_TRANSPORT})")


# ─── Flask REST API (lokal, opsional) ────────────────────────────────────────
app = Flask(__name__)
CORS(app)


@app.route("/api/health")
@app.route("/health")
@app.route("/")
def health():
    return jsonify({
        "status":        "ok",
        "device_id":     DEVICE_ID,
        "mqtt_connected": _mqtt_connected,
        "uptime":        time.time(),
    })


@app.route("/api/sensor")
def get_sensor():
    temp  = round(_base_temp  + random.uniform(-0.2, 0.2), 1)
    humid = round(_base_humid + random.uniform(-1.0, 1.0), 1)
    return jsonify({"temperature": temp, "humidity": humid,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "device_id": DEVICE_ID})


@app.route("/api/actuators")
def get_actuators():
    with _state_lock:
        return jsonify({"success": True, "device_id": DEVICE_ID, "actuators": dict(actuator_state)})


@app.route("/api/actuators/<name>", methods=["POST"])
def set_actuator_http(name: str):
    if name not in actuator_state:
        return jsonify({"success": False, "error": f"Aktuator tidak dikenal: {name}"}), 404
    data  = request.get_json(force=True, silent=True) or {}
    state = bool(data.get("state", False))
    _set_actuator(name, state)
    return jsonify({"success": True, "actuator": name, "state": state})


@app.route("/api/emergency-stop", methods=["POST"])
def http_emergency_stop():
    _emergency_stop()
    return jsonify({"success": True, "message": "Semua aktuator dimatikan"})


# ─── Cleanup ─────────────────────────────────────────────────────────────────
@atexit.register
def cleanup():
    _emergency_stop()
    for dev in devices.values():
        try:
            dev.close()
        except Exception:
            pass
    if _mqtt_client:
        _mqtt_client.loop_stop()
        _mqtt_client.disconnect()
    logger.info("[Cleanup] Selesai.")


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print(f"  TernakTelur — Raspi Lemari")
    print(f"  Device ID  : {DEVICE_ID}")
    print(f"  MQTT Broker: {MQTT_BROKER}:{MQTT_PORT} ({MQTT_TRANSPORT})")
    print(f"  Flask Port : {FLASK_PORT}")
    print(f"  GPIO Mode  : {'Hardware' if GPIO_AVAILABLE else 'Simulasi'}")
    print("=" * 60)
    start_mqtt()
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)
