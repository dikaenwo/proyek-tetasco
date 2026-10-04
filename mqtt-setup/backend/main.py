"""
main.py — Tetasco Connect FastAPI (dengan integrasi MQTT)
=========================================================
Tambahan dari versi sebelumnya:
  - Lifespan event: start/stop MQTTManager
  - Setiap endpoint kontrol perangkat → publish MQTT command
  - Endpoint baru: /api/tetasco/{id}/devices/emergency-stop
  - Endpoint baru: /api/mqtt/status (health check MQTT)
  - Sensor otomatis tersimpan saat Raspi publish ke MQTT
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import MQTT manager
from mqtt_manager import mqtt_manager

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── State in-memory cache status lemari (update dari MQTT) ──────────────────
device_status_cache: dict[str, dict] = {}
device_sensor_cache: dict[str, dict] = {}
device_heartbeat_cache: dict[str, dict] = {}


# ─── MQTT Callbacks ──────────────────────────────────────────────────────────
def handle_status(device_id: str, payload: dict):
    """Simpan status device ke cache (dan bisa simpan ke DB)."""
    device_status_cache[device_id] = payload
    logger.info(f"[Status] {device_id}: {payload}")
    # TODO: simpan ke PostgreSQL jika perlu histori


def handle_sensor(device_id: str, payload: dict):
    """Simpan data sensor ke cache dan PostgreSQL."""
    device_sensor_cache[device_id] = payload
    logger.info(f"[Sensor] {device_id}: temp={payload.get('temperature')} hum={payload.get('humidity')}")
    # TODO: db.execute("INSERT INTO sensor_history ...") pakai asyncpg/sqlalchemy


def handle_heartbeat(device_id: str, payload: dict):
    """Catat heartbeat terakhir."""
    device_heartbeat_cache[device_id] = payload
    logger.debug(f"[Heartbeat] {device_id}: {payload}")


# ─── Lifespan (startup / shutdown) ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    mqtt_manager.on_status(handle_status)
    mqtt_manager.on_sensor(handle_sensor)
    mqtt_manager.on_heartbeat(handle_heartbeat)
    mqtt_manager.start()
    logger.info("[App] FastAPI started, MQTT running.")
    yield
    # Shutdown
    mqtt_manager.stop()
    logger.info("[App] FastAPI shutdown, MQTT stopped.")


# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Tetasco Connect API",
    version="2.0.0",
    description="API penetas telur IoT dengan MQTT multi-lemari",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Models ───────────────────────────────────────────────────────────────────
class DeviceCommandResponse(BaseModel):
    success: bool
    device_id: str
    actuator: str
    state: bool
    mqtt_sent: bool
    message: str


# ─── Helper ───────────────────────────────────────────────────────────────────
VALID_ACTUATORS = {"fan", "heater", "heater2", "humidifier", "motor", "uv_light"}

def device_id_from_tetasco_id(tetasco_id: int) -> str:
    """Konversi tetasco_id (int) ke MQTT device_id string."""
    return f"lemari-{tetasco_id}"


# ─── Endpoints Dasar ─────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"service": "Tetasco Connect API", "version": "2.0.0", "mqtt": mqtt_manager.is_connected}


@app.get("/api/health")
def health():
    return {"status": "ok", "mqtt_connected": mqtt_manager.is_connected}


@app.get("/api/mqtt/status")
def mqtt_status():
    """Cek status koneksi MQTT broker."""
    return {
        "connected": mqtt_manager.is_connected,
        "broker":    os.getenv("MQTT_BROKER", "mosquitto"),
        "port":      int(os.getenv("MQTT_PORT", "1883")),
    }


# ─── Endpoint Kontrol Perangkat (dengan MQTT) ─────────────────────────────────
@app.post("/api/tetasco/{tetasco_id}/devices/{actuator}/{action}")
def control_device(tetasco_id: int, actuator: str, action: str) -> DeviceCommandResponse:
    """
    Kontrol perangkat lemari via MQTT.
    actuator: fan | heater | heater2 | humidifier | motor | uv_light
    action:   on | off
    """
    if actuator not in VALID_ACTUATORS:
        raise HTTPException(status_code=400, detail=f"Aktuator tidak valid: {actuator}. Pilihan: {VALID_ACTUATORS}")

    if action not in ("on", "off"):
        raise HTTPException(status_code=400, detail="Action harus 'on' atau 'off'")

    state     = (action == "on")
    device_id = device_id_from_tetasco_id(tetasco_id)

    # Publish ke MQTT (Raspi Lemari akan eksekusi GPIO-nya)
    mqtt_sent = mqtt_manager.publish_command(device_id, actuator, state)

    # Update cache lokal
    if device_id not in device_status_cache:
        device_status_cache[device_id] = {}
    device_status_cache[device_id][actuator] = state

    # TODO: Update DB (logical state)
    # db.execute("UPDATE device_states SET {actuator}={state} WHERE tetasco_id={tetasco_id}")

    return DeviceCommandResponse(
        success=True,
        device_id=device_id,
        actuator=actuator,
        state=state,
        mqtt_sent=mqtt_sent,
        message=f"{actuator.upper()} {'ON' if state else 'OFF'} — perintah dikirim ke {device_id}",
    )


@app.post("/api/tetasco/{tetasco_id}/devices/emergency-stop")
def emergency_stop_device(tetasco_id: int):
    """Emergency stop satu lemari."""
    device_id = device_id_from_tetasco_id(tetasco_id)
    sent      = mqtt_manager.publish_emergency_stop(device_id)
    if device_id in device_status_cache:
        device_status_cache[device_id] = {k: False for k in VALID_ACTUATORS}
    return {"success": True, "device_id": device_id, "mqtt_sent": sent, "message": "Emergency stop dikirim"}


@app.post("/api/emergency-stop-all")
def emergency_stop_all():
    """Emergency stop SEMUA lemari sekaligus."""
    sent = mqtt_manager.publish_emergency_stop_all()
    return {"success": True, "mqtt_sent": sent, "message": "Emergency stop dikirim ke semua lemari"}


# ─── Endpoint Status ──────────────────────────────────────────────────────────
@app.get("/api/tetasco/{tetasco_id}/devices")
def get_device_status(tetasco_id: int):
    """Ambil status perangkat terakhir yang diterima via MQTT."""
    device_id = device_id_from_tetasco_id(tetasco_id)
    status    = device_status_cache.get(device_id, {})
    return {"device_id": device_id, "status": status}


@app.get("/api/tetasco/{tetasco_id}/sensors")
def get_sensor(tetasco_id: int):
    """Ambil data sensor terakhir dari lemari."""
    device_id = device_id_from_tetasco_id(tetasco_id)
    sensor    = device_sensor_cache.get(device_id, {})
    if not sensor:
        raise HTTPException(status_code=404, detail=f"Belum ada data sensor untuk {device_id}")
    return {"device_id": device_id, "sensor": sensor}


@app.get("/api/tetasco/{tetasco_id}/heartbeat")
def get_heartbeat(tetasco_id: int):
    """Cek apakah lemari masih online (heartbeat terakhir)."""
    device_id = device_id_from_tetasco_id(tetasco_id)
    hb        = device_heartbeat_cache.get(device_id)
    return {"device_id": device_id, "online": hb is not None, "last_heartbeat": hb}


@app.get("/api/tetasco/all/status")
def get_all_status():
    """Status semua lemari yang pernah connect."""
    return {
        "devices":    device_status_cache,
        "sensors":    device_sensor_cache,
        "heartbeats": device_heartbeat_cache,
    }
