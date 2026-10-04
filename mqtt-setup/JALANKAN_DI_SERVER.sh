#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║   TETASCO CONNECT — MQTT FULL SETUP (Server Pusat)          ║
# ║   Copy-paste SELURUH script ini ke terminal SSH Anda        ║
# ║   ssh telur@telur → lalu paste & Enter                      ║
# ╚══════════════════════════════════════════════════════════════╝
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }
step() { echo -e "\n${CYAN}━━━ $1 ━━━${NC}"; }

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     Tetasco Connect — MQTT Setup Script v1.0            ║"
echo "║     Server: $(hostname) | $(date '+%Y-%m-%d %H:%M:%S')             ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

PROJ="/home/telur/tetasco-connect"

# ═══════════════════════════════════════════════════════════════
# STEP 1 — Buat Struktur Folder
# ═══════════════════════════════════════════════════════════════
step "STEP 1: Membuat Struktur Folder"
mkdir -p $PROJ/{mosquitto/{config,data,log},backend,frontend,nginx,cloudflare}
chmod 777 $PROJ/mosquitto/data $PROJ/mosquitto/log
log "Folder dibuat: $PROJ"
ls -la $PROJ/

# ═══════════════════════════════════════════════════════════════
# STEP 2 — Mosquitto Config
# ═══════════════════════════════════════════════════════════════
step "STEP 2: Membuat Konfigurasi Mosquitto"

cat > $PROJ/mosquitto/config/mosquitto.conf << 'MOSQ_CONF'
pid_file /run/mosquitto/mosquitto.pid
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout

# Listener TCP (internal Docker)
listener 1883
bind_address 0.0.0.0
protocol mqtt

# Listener WebSocket (untuk Cloudflare Tunnel)
listener 9001
protocol websockets
bind_address 0.0.0.0

# Autentikasi
allow_anonymous false
password_file /mosquitto/config/passwd
acl_file /mosquitto/config/acl.conf

# Tuning
max_keepalive 120
max_inflight_messages 20
max_queued_messages 100
log_type error
log_type warning
log_type notice
log_type information
log_timestamp true
MOSQ_CONF

log "mosquitto.conf dibuat"

# ═══════════════════════════════════════════════════════════════
# STEP 3 — ACL Config
# ═══════════════════════════════════════════════════════════════
step "STEP 3: Membuat ACL Rules"

cat > $PROJ/mosquitto/config/acl.conf << 'ACL_CONF'
# Server pusat: akses penuh
user server
topic readwrite tetasco/#

# Template lemari (1-15)
ACL_CONF

for i in $(seq 1 15); do
cat >> $PROJ/mosquitto/config/acl.conf << ACL_ITEM
user lemari-$i
topic write tetasco/lemari-$i/status
topic write tetasco/lemari-$i/sensor
topic write tetasco/lemari-$i/heartbeat
topic read  tetasco/lemari-$i/command/#

ACL_ITEM
done

log "acl.conf dibuat (15 lemari)"

# ═══════════════════════════════════════════════════════════════
# STEP 4 — Generate Passwords Mosquitto
# ═══════════════════════════════════════════════════════════════
step "STEP 4: Generate Password Mosquitto"

# Install mosquitto-clients jika belum ada
if ! command -v mosquitto_passwd &>/dev/null; then
    info "Menginstall mosquitto-clients..."
    sudo apt-get update -qq && sudo apt-get install -y mosquitto-clients
fi

PASSWD_FILE="$PROJ/mosquitto/config/passwd"
PASS_LOG="$PROJ/mqtt_passwords.txt"

# Hapus file lama jika ada
> "$PASSWD_FILE"
> "$PASS_LOG"

# Generate password server
SERVER_PASS="srv-$(openssl rand -hex 10)"
mosquitto_passwd -b "$PASSWD_FILE" server "$SERVER_PASS"
echo "server = $SERVER_PASS" >> "$PASS_LOG"

# Generate password tiap lemari
for i in $(seq 1 15); do
    LP="lem${i}-$(openssl rand -hex 8)"
    mosquitto_passwd -b "$PASSWD_FILE" "lemari-$i" "$LP"
    echo "lemari-$i = $LP" >> "$PASS_LOG"
done

chmod 600 "$PASS_LOG" "$PASSWD_FILE"
log "Password dibuat → $PASS_LOG"
warn "SIMPAN FILE INI: $PASS_LOG"
echo ""
cat "$PASS_LOG"
echo ""

# ═══════════════════════════════════════════════════════════════
# STEP 5 — FastAPI Backend
# ═══════════════════════════════════════════════════════════════
step "STEP 5: Membuat FastAPI Backend"

cat > $PROJ/backend/requirements.txt << 'REQ'
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
paho-mqtt>=2.0.0
asyncpg>=0.29.0
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0
REQ

cat > $PROJ/backend/Dockerfile << 'DFILE'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
DFILE

# ── mqtt_manager.py ──────────────────────────────────────────
cat > $PROJ/backend/mqtt_manager.py << 'MQTT_MGR'
"""mqtt_manager.py — Tetasco Connect MQTT Publisher/Subscriber"""
import json, logging, os, time, threading
from typing import Callable, Optional
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

MQTT_BROKER    = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT      = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER      = os.getenv("MQTT_USER", "server")
MQTT_PASS      = os.getenv("MQTT_PASS", "server-secret")
MQTT_CLIENT_ID = "tetasco-server"
MQTT_QOS       = 1

_status_callbacks:    list[Callable] = []
_sensor_callbacks:    list[Callable] = []
_heartbeat_callbacks: list[Callable] = []


class MQTTManager:
    def __init__(self):
        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._lock = threading.Lock()

    def start(self):
        self._client = mqtt.Client(
            client_id=MQTT_CLIENT_ID,
            protocol=mqtt.MQTTv5,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        self._client.username_pw_set(MQTT_USER, MQTT_PASS)
        self._client.on_connect    = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message    = self._on_message
        self._client.reconnect_delay_set(min_delay=2, max_delay=30)
        self._client.connect_async(MQTT_BROKER, MQTT_PORT, 60)
        self._client.loop_start()
        logger.info(f"[MQTT] Connecting → {MQTT_BROKER}:{MQTT_PORT}")

    def stop(self):
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self._connected = True
            logger.info("[MQTT] Connected!")
            client.subscribe("tetasco/+/status",    qos=MQTT_QOS)
            client.subscribe("tetasco/+/sensor",    qos=MQTT_QOS)
            client.subscribe("tetasco/+/heartbeat", qos=MQTT_QOS)
        else:
            self._connected = False
            logger.warning(f"[MQTT] Gagal connect rc={rc}")

    def _on_disconnect(self, client, userdata, flags, rc, properties=None):
        self._connected = False
        if rc != 0:
            logger.warning(f"[MQTT] Disconnected rc={rc}, reconnecting...")

    def _on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        try:
            parts = msg.topic.split("/")
            if len(parts) < 3: return
            device_id = parts[1]
            msg_type  = parts[2]
            payload   = json.loads(msg.payload.decode())
            if msg_type == "status":
                [cb(device_id, payload) for cb in _status_callbacks]
            elif msg_type == "sensor":
                [cb(device_id, payload) for cb in _sensor_callbacks]
            elif msg_type == "heartbeat":
                [cb(device_id, payload) for cb in _heartbeat_callbacks]
        except Exception as e:
            logger.error(f"[MQTT] Error: {e}")

    def publish_command(self, device_id: str, actuator: str, state: bool) -> bool:
        if not self._connected or not self._client: return False
        topic   = f"tetasco/{device_id}/command/{actuator}"
        payload = json.dumps({"state": state, "ts": int(time.time())})
        with self._lock:
            result = self._client.publish(topic, payload, qos=MQTT_QOS)
        logger.info(f"[MQTT] → {topic}: {payload}")
        return result.rc == mqtt.MQTT_ERR_SUCCESS

    def publish_emergency_stop(self, device_id: str) -> bool:
        if not self._connected or not self._client: return False
        topic = f"tetasco/{device_id}/command/emergency_stop"
        result = self._client.publish(topic, json.dumps({"ts": int(time.time())}), qos=MQTT_QOS)
        return result.rc == mqtt.MQTT_ERR_SUCCESS

    def publish_emergency_stop_all(self) -> bool:
        if not self._connected or not self._client: return False
        result = self._client.publish("tetasco/ALL/command/emergency_stop",
                                      json.dumps({"ts": int(time.time())}), qos=MQTT_QOS)
        return result.rc == mqtt.MQTT_ERR_SUCCESS

    def on_status(self, fn): _status_callbacks.append(fn)
    def on_sensor(self, fn): _sensor_callbacks.append(fn)
    def on_heartbeat(self, fn): _heartbeat_callbacks.append(fn)

    @property
    def is_connected(self): return self._connected


mqtt_manager = MQTTManager()
MQTT_MGR

# ── main.py ──────────────────────────────────────────────────
cat > $PROJ/backend/main.py << 'MAIN_PY'
"""main.py — Tetasco Connect FastAPI dengan MQTT"""
import logging, os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mqtt_manager import mqtt_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

device_status_cache:    dict = {}
device_sensor_cache:    dict = {}
device_heartbeat_cache: dict = {}

def handle_status(device_id, payload):
    device_status_cache[device_id] = payload
    logger.info(f"[Status] {device_id}: {payload}")

def handle_sensor(device_id, payload):
    device_sensor_cache[device_id] = payload
    logger.info(f"[Sensor] {device_id}: T={payload.get('temperature')} H={payload.get('humidity')}")

def handle_heartbeat(device_id, payload):
    device_heartbeat_cache[device_id] = payload

@asynccontextmanager
async def lifespan(app: FastAPI):
    mqtt_manager.on_status(handle_status)
    mqtt_manager.on_sensor(handle_sensor)
    mqtt_manager.on_heartbeat(handle_heartbeat)
    mqtt_manager.start()
    logger.info("[App] Started, MQTT running.")
    yield
    mqtt_manager.stop()

app = FastAPI(title="Tetasco Connect API", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

VALID_ACTUATORS = {"fan","heater","heater2","humidifier","motor","uv_light"}

@app.get("/")
def root():
    return {"service": "Tetasco Connect", "version": "2.0.0", "mqtt": mqtt_manager.is_connected}

@app.get("/api/health")
def health():
    return {"status": "ok", "mqtt": mqtt_manager.is_connected}

@app.get("/api/mqtt/status")
def mqtt_status():
    return {"connected": mqtt_manager.is_connected,
            "broker": os.getenv("MQTT_BROKER"), "port": int(os.getenv("MQTT_PORT", 1883))}

@app.post("/api/tetasco/{tid}/devices/{actuator}/{action}")
def control_device(tid: int, actuator: str, action: str):
    if actuator not in VALID_ACTUATORS:
        raise HTTPException(400, f"Actuator tidak valid: {actuator}")
    if action not in ("on","off"):
        raise HTTPException(400, "Action harus on/off")
    state     = action == "on"
    device_id = f"lemari-{tid}"
    sent      = mqtt_manager.publish_command(device_id, actuator, state)
    if device_id not in device_status_cache:
        device_status_cache[device_id] = {}
    device_status_cache[device_id][actuator] = state
    return {"success": True, "device_id": device_id, "actuator": actuator,
            "state": state, "mqtt_sent": sent}

@app.post("/api/tetasco/{tid}/devices/emergency-stop")
def emergency_stop(tid: int):
    device_id = f"lemari-{tid}"
    sent = mqtt_manager.publish_emergency_stop(device_id)
    device_status_cache[device_id] = {k: False for k in VALID_ACTUATORS}
    return {"success": True, "device_id": device_id, "mqtt_sent": sent}

@app.post("/api/emergency-stop-all")
def emergency_stop_all():
    return {"success": True, "mqtt_sent": mqtt_manager.publish_emergency_stop_all()}

@app.get("/api/tetasco/{tid}/devices")
def get_status(tid: int):
    did = f"lemari-{tid}"
    return {"device_id": did, "status": device_status_cache.get(did, {})}

@app.get("/api/tetasco/{tid}/sensors")
def get_sensor(tid: int):
    did = f"lemari-{tid}"
    s = device_sensor_cache.get(did)
    if not s: raise HTTPException(404, f"Belum ada data sensor {did}")
    return {"device_id": did, "sensor": s}

@app.get("/api/tetasco/{tid}/heartbeat")
def get_heartbeat(tid: int):
    did = f"lemari-{tid}"
    hb  = device_heartbeat_cache.get(did)
    return {"device_id": did, "online": hb is not None, "last_heartbeat": hb}

@app.get("/api/tetasco/all/status")
def all_status():
    return {"devices": device_status_cache,
            "sensors": device_sensor_cache,
            "heartbeats": device_heartbeat_cache}
MAIN_PY

log "Backend files dibuat"

# ═══════════════════════════════════════════════════════════════
# STEP 6 — Nginx Config
# ═══════════════════════════════════════════════════════════════
step "STEP 6: Konfigurasi Nginx"

cat > $PROJ/nginx/nginx.conf << 'NGINX_CONF'
events { worker_connections 1024; }
http {
    include      mime.types;
    default_type application/octet-stream;
    upstream fastapi { server backend:8000; }
    server {
        listen 80;
        server_name _;
        location /api/ {
            proxy_pass         http://fastapi;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_read_timeout 60s;
        }
        location /docs         { proxy_pass http://fastapi/docs; }
        location /openapi.json { proxy_pass http://fastapi/openapi.json; }
        location / {
            root      /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }
    }
}
NGINX_CONF

echo "<h1>Tetasco Connect</h1>" > $PROJ/frontend/index.html
log "Nginx config dibuat"

# ═══════════════════════════════════════════════════════════════
# STEP 7 — .env & Docker Compose
# ═══════════════════════════════════════════════════════════════
step "STEP 7: Docker Compose & .env"

SERVER_PASS=$(grep "^server" $PROJ/mqtt_passwords.txt | cut -d' ' -f3)
DB_PASS="db-$(openssl rand -hex 12)"

cat > $PROJ/.env << ENV
DB_PASS=$DB_PASS
MQTT_SERVER_PASS=$SERVER_PASS
ENV
chmod 600 $PROJ/.env

cat > $PROJ/docker-compose.yml << 'DC'
services:
  mosquitto:
    image: eclipse-mosquitto:2
    container_name: tetasco-mosquitto
    restart: unless-stopped
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - ./mosquitto/config:/mosquitto/config:ro
      - ./mosquitto/data:/mosquitto/data
      - ./mosquitto/log:/mosquitto/log
    networks:
      - tetasco-net

  backend:
    build: ./backend
    container_name: tetasco-backend
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://telur:${DB_PASS}@database:5432/tetasco
      MQTT_BROKER: mosquitto
      MQTT_PORT: 1883
      MQTT_USER: server
      MQTT_PASS: ${MQTT_SERVER_PASS}
    ports:
      - "8000:8000"
    depends_on:
      - mosquitto
      - database
    networks:
      - tetasco-net

  database:
    image: postgres:15-alpine
    container_name: tetasco-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: telur
      POSTGRES_PASSWORD: ${DB_PASS}
      POSTGRES_DB: tetasco
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - tetasco-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U telur -d tetasco"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    container_name: tetasco-nginx
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend:/usr/share/nginx/html:ro
    depends_on:
      - backend
    networks:
      - tetasco-net

volumes:
  postgres_data:

networks:
  tetasco-net:
    driver: bridge
DC

log "docker-compose.yml & .env dibuat"

# ═══════════════════════════════════════════════════════════════
# STEP 8 — Relay API untuk Raspi Lemari
# ═══════════════════════════════════════════════════════════════
step "STEP 8: File Raspi Lemari (relay_api_mqtt.py)"

cat > $PROJ/relay_api_mqtt.py << 'RELAY'
"""
relay_api_mqtt.py — TernakTelur Raspi Lemari (Flask + gpiozero + MQTT)
Salin file ini ke tiap Raspi Lemari, set DEVICE_ID & MQTT_PASS.
Jalankan: DEVICE_ID=lemari-1 MQTT_PASS=xxx python relay_api_mqtt.py
"""
import json, logging, os, random, socket, threading, time, atexit
import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request
from flask_cors import CORS
try:
    from gpiozero import DigitalOutputDevice
    GPIO_AVAILABLE = True
except Exception:
    GPIO_AVAILABLE = False
    print("[WARN] gpiozero tidak tersedia, mode simulasi aktif")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEVICE_ID           = os.getenv("DEVICE_ID", "lemari-1")
FLASK_PORT          = int(os.getenv("FLASK_PORT", "5001"))
MQTT_BROKER         = os.getenv("MQTT_BROKER", "mqtt.tetasco.my.id")
MQTT_PORT           = int(os.getenv("MQTT_PORT", "443"))
MQTT_TRANSPORT      = os.getenv("MQTT_TRANSPORT", "websockets")
MQTT_USE_TLS        = os.getenv("MQTT_USE_TLS", "true").lower() == "true"
MQTT_USER           = os.getenv("MQTT_USER", DEVICE_ID)
MQTT_PASS           = os.getenv("MQTT_PASS", "change-me")
MQTT_WS_PATH        = os.getenv("MQTT_WEBSOCKET_PATH", "/mqtt")
SENSOR_INTERVAL     = int(os.getenv("SENSOR_INTERVAL", "10"))
HEARTBEAT_INTERVAL  = int(os.getenv("HEARTBEAT_INTERVAL", "30"))

TOPIC_COMMAND   = f"tetasco/{DEVICE_ID}/command/#"
TOPIC_STATUS    = f"tetasco/{DEVICE_ID}/status"
TOPIC_SENSOR    = f"tetasco/{DEVICE_ID}/sensor"
TOPIC_HEARTBEAT = f"tetasco/{DEVICE_ID}/heartbeat"
TOPIC_EMSTOP    = "tetasco/ALL/command/emergency_stop"

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
            devices[name] = DigitalOutputDevice(cfg["pin"], active_high=cfg["active_high"], initial_value=False)
            logger.info(f"[GPIO] {name} GPIO {cfg['pin']} siap")
        except Exception as e:
            logger.warning(f"[GPIO] Gagal init {name}: {e}")

actuator_state = {k: False for k in GPIO_CONFIG}
_base_temp = 37.5; _base_humid = 60.0; _lock = threading.Lock()
_mqtt_client = None; _mqtt_connected = False

def _write_gpio(name, state):
    dev = devices.get(name)
    if dev: dev.on() if state else dev.off()

def _set_actuator(name, state):
    with _lock: actuator_state[name] = state
    _write_gpio(name, state)
    logger.info(f"[Aktuator] {name} → {'ON' if state else 'OFF'}")

def _emergency_stop():
    with _lock:
        for k in actuator_state: actuator_state[k] = False
    for k in GPIO_CONFIG: _write_gpio(k, False)
    logger.warning("[EMERGENCY STOP] Semua aktuator OFF!")

def _get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except: return "unknown"

def _on_connect(client, ud, flags, rc, props=None):
    global _mqtt_connected
    if rc == 0:
        _mqtt_connected = True
        logger.info(f"[MQTT] Terhubung ke broker sbg {DEVICE_ID}")
        client.subscribe(TOPIC_COMMAND, qos=1)
        client.subscribe(TOPIC_EMSTOP,  qos=1)
        client.publish(TOPIC_HEARTBEAT, json.dumps({"ts": int(time.time()), "device_id": DEVICE_ID, "ip": _get_ip()}), qos=0)
    else:
        _mqtt_connected = False
        logger.warning(f"[MQTT] Gagal connect rc={rc}")

def _on_disconnect(client, ud, flags, rc, props=None):
    global _mqtt_connected
    _mqtt_connected = False
    logger.warning(f"[MQTT] Terputus rc={rc}, reconnecting...")

def _on_message(client, ud, msg):
    try:
        topic   = msg.topic
        payload = json.loads(msg.payload.decode()) if msg.payload else {}
        logger.info(f"[MQTT] Terima: {topic} → {payload}")
        if topic == TOPIC_EMSTOP or topic.endswith("/emergency_stop"):
            _emergency_stop()
            client.publish(TOPIC_STATUS, json.dumps({**actuator_state, "ts": int(time.time())}), qos=1)
            return
        parts = topic.split("/")
        if len(parts) == 4 and parts[2] == "command":
            act = parts[3]
            if act in actuator_state:
                _set_actuator(act, bool(payload.get("state", False)))
                client.publish(TOPIC_STATUS, json.dumps({**actuator_state, "ts": int(time.time())}), qos=1)
    except Exception as e:
        logger.error(f"[MQTT] Error: {e}")

def _sensor_loop(client):
    while True:
        try:
            if _mqtt_connected:
                payload = {"temperature": round(_base_temp + random.uniform(-0.5,0.5),1),
                           "humidity": round(_base_humid + random.uniform(-2,2),1),
                           "ts": int(time.time()), "device_id": DEVICE_ID}
                client.publish(TOPIC_SENSOR, json.dumps(payload), qos=0)
        except Exception as e: logger.error(f"[Sensor] {e}")
        time.sleep(SENSOR_INTERVAL)

def _heartbeat_loop(client):
    while True:
        try:
            if _mqtt_connected:
                client.publish(TOPIC_HEARTBEAT, json.dumps({"ts": int(time.time()), "device_id": DEVICE_ID, "ip": _get_ip()}), qos=0)
        except Exception as e: logger.error(f"[HB] {e}")
        time.sleep(HEARTBEAT_INTERVAL)

def start_mqtt():
    global _mqtt_client
    client = mqtt.Client(client_id=f"{DEVICE_ID}-{int(time.time())}", transport=MQTT_TRANSPORT,
                         protocol=mqtt.MQTTv5, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    if MQTT_TRANSPORT == "websockets": client.ws_set_options(path=MQTT_WS_PATH)
    if MQTT_USE_TLS:
        import ssl; client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = _on_connect; client.on_disconnect = _on_disconnect; client.on_message = _on_message
    client.reconnect_delay_set(min_delay=3, max_delay=60)
    _mqtt_client = client
    threading.Thread(target=_sensor_loop,    args=(client,), daemon=True).start()
    threading.Thread(target=_heartbeat_loop, args=(client,), daemon=True).start()
    client.connect_async(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    logger.info(f"[MQTT] Connecting → {MQTT_BROKER}:{MQTT_PORT} ({MQTT_TRANSPORT})")

app = Flask(__name__); CORS(app)

@app.get("/api/health"); @app.route("/")
def health(): return jsonify({"status":"ok","device_id":DEVICE_ID,"mqtt":_mqtt_connected})

@app.route("/api/sensor")
def get_sensor(): return jsonify({"temperature":round(_base_temp+random.uniform(-0.2,0.2),1),
    "humidity":round(_base_humid+random.uniform(-1,1),1),"device_id":DEVICE_ID})

@app.route("/api/actuators")
def get_actuators():
    with _lock: return jsonify({"success":True,"device_id":DEVICE_ID,"actuators":dict(actuator_state)})

@app.route("/api/actuators/<name>", methods=["POST"])
def set_act(name):
    if name not in actuator_state: return jsonify({"success":False,"error":f"Unknown: {name}"}),404
    data = request.get_json(force=True,silent=True) or {}
    _set_actuator(name, bool(data.get("state",False)))
    return jsonify({"success":True,"actuator":name,"state":actuator_state[name]})

@app.route("/api/emergency-stop", methods=["POST"])
def http_estop(): _emergency_stop(); return jsonify({"success":True})

@atexit.register
def cleanup():
    _emergency_stop()
    for dev in devices.values():
        try: dev.close()
        except: pass
    if _mqtt_client: _mqtt_client.loop_stop(); _mqtt_client.disconnect()

if __name__ == "__main__":
    print(f"{'='*55}\n  Raspi Lemari: {DEVICE_ID}\n  MQTT: {MQTT_BROKER}:{MQTT_PORT}\n  GPIO: {'HW' if GPIO_AVAILABLE else 'Simulasi'}\n{'='*55}")
    start_mqtt()
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)
RELAY

log "relay_api_mqtt.py dibuat di $PROJ/"

# ═══════════════════════════════════════════════════════════════
# STEP 9 — Cloudflare Config
# ═══════════════════════════════════════════════════════════════
step "STEP 9: Cloudflare Tunnel Config"

cat > $PROJ/cloudflare/config.yml << 'CF_CONF'
# Edit tunnel ID setelah menjalankan: cloudflared tunnel create tetasco-mqtt
tunnel: GANTI_TUNNEL_ID_DISINI
credentials-file: /home/telur/.cloudflared/GANTI_TUNNEL_ID_DISINI.json

ingress:
  - hostname: api.tetasco.my.id
    service: http://localhost:80

  - hostname: mqtt.tetasco.my.id
    service: http://localhost:9001
    originRequest:
      connectTimeout: 30s

  - service: http_status:404
CF_CONF

log "cloudflare/config.yml dibuat"

# ═══════════════════════════════════════════════════════════════
# STEP 10 — Jalankan Docker Compose
# ═══════════════════════════════════════════════════════════════
step "STEP 10: Jalankan Docker Compose"

cd $PROJ
sudo docker compose up -d --build

echo ""
sleep 3
sudo docker compose ps
echo ""

# ═══════════════════════════════════════════════════════════════
# SELESAI
# ═══════════════════════════════════════════════════════════════
echo -e "\n${GREEN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                   SETUP SELESAI! ✓                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "  ${CYAN}📁 Project:${NC}     $PROJ"
echo -e "  ${CYAN}🔑 Passwords:${NC}   $PROJ/mqtt_passwords.txt"
echo -e "  ${CYAN}🌐 API:${NC}         http://$(hostname -I | awk '{print $1}')/api/health"
echo -e "  ${CYAN}📡 MQTT TCP:${NC}    $(hostname -I | awk '{print $1}'):1883"
echo -e "  ${CYAN}🔌 MQTT WS:${NC}     $(hostname -I | awk '{print $1}'):9001"
echo ""
echo -e "${YELLOW}━━━ LANGKAH SELANJUTNYA: Cloudflare Tunnel ━━━${NC}"
echo ""
echo "  1. curl -L https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-archive-keyring.gpg >/dev/null"
echo "  2. echo 'deb [signed-by=/usr/share/keyrings/cloudflare-archive-keyring.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main' | sudo tee /etc/apt/sources.list.d/cloudflared.list"
echo "  3. sudo apt-get update && sudo apt-get install -y cloudflared"
echo "  4. cloudflared tunnel login"
echo "  5. cloudflared tunnel create tetasco-mqtt"
echo "  6. cp $PROJ/cloudflare/config.yml ~/.cloudflared/ && nano ~/.cloudflared/config.yml  # edit tunnel ID"
echo "  7. cloudflared tunnel route dns tetasco-mqtt mqtt.tetasco.my.id"
echo "  8. cloudflared tunnel route dns tetasco-mqtt api.tetasco.my.id"
echo "  9. sudo cloudflared service install && sudo systemctl start cloudflared"
echo ""
echo -e "${YELLOW}━━━ SETUP RASPI LEMARI ━━━${NC}"
echo ""
echo "  Di tiap Raspi lemari, jalankan:"
echo "  pip install flask flask-cors paho-mqtt gpiozero"
echo "  # Copy relay_api_mqtt.py dari: $PROJ/relay_api_mqtt.py"
echo "  DEVICE_ID=lemari-1 MQTT_PASS=\"\$(grep 'lemari-1' $PROJ/mqtt_passwords.txt | cut -d' ' -f3)\" python relay_api_mqtt.py"
echo ""
