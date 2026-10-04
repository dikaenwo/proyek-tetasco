"""
mqtt_manager.py — Tetasco Connect MQTT Publisher
=================================================
Dijalankan di Server Pusat (FastAPI backend).
Bertanggung jawab untuk:
  - Connect ke Mosquitto broker (internal Docker)
  - Publish perintah ke Raspi Lemari
  - Subscribe status & sensor dari Lemari
  - Auto-reconnect jika koneksi putus
"""

import json
import logging
import os
import time
import threading
from typing import Callable, Optional

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

# ─── Konfigurasi ──────────────────────────────────────────────────────────────
MQTT_BROKER   = os.getenv("MQTT_BROKER", "mosquitto")   # nama service Docker
MQTT_PORT     = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER     = os.getenv("MQTT_USER", "server")
MQTT_PASS     = os.getenv("MQTT_PASS", "server-secret")
MQTT_CLIENT_ID = "tetasco-server"
MQTT_KEEPALIVE = 60
MQTT_QOS       = 1                                      # At least once


# ─── Callback registry ────────────────────────────────────────────────────────
_status_callbacks:  list[Callable] = []   # dipanggil saat terima status lemari
_sensor_callbacks:  list[Callable] = []   # dipanggil saat terima data sensor
_heartbeat_callbacks: list[Callable] = []


class MQTTManager:
    """Singleton MQTT client untuk server pusat Tetasco."""

    def __init__(self):
        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._lock = threading.Lock()

    # ── Setup ─────────────────────────────────────────────────────────────────
    def start(self):
        """Inisialisasi dan connect ke broker. Dipanggil saat FastAPI startup."""
        self._client = mqtt.Client(
            client_id=MQTT_CLIENT_ID,
            protocol=mqtt.MQTTv5,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        self._client.username_pw_set(MQTT_USER, MQTT_PASS)
        self._client.on_connect    = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message    = self._on_message

        # Reconnect otomatis
        self._client.reconnect_delay_set(min_delay=2, max_delay=30)

        self._client.connect_async(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        self._client.loop_start()
        logger.info(f"[MQTT] Connecting to {MQTT_BROKER}:{MQTT_PORT}...")

    def stop(self):
        """Disconnect bersih saat FastAPI shutdown."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            logger.info("[MQTT] Disconnected.")

    # ── Callbacks ─────────────────────────────────────────────────────────────
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self._connected = True
            logger.info("[MQTT] Connected ke broker!")
            # Subscribe ke semua topik status, sensor, heartbeat
            client.subscribe("tetasco/+/status",    qos=MQTT_QOS)
            client.subscribe("tetasco/+/sensor",    qos=MQTT_QOS)
            client.subscribe("tetasco/+/heartbeat", qos=MQTT_QOS)
            logger.info("[MQTT] Subscribed ke tetasco/+/status|sensor|heartbeat")
        else:
            self._connected = False
            logger.warning(f"[MQTT] Koneksi gagal, rc={rc}")

    def _on_disconnect(self, client, userdata, flags, rc, properties=None):
        self._connected = False
        if rc != 0:
            logger.warning(f"[MQTT] Terputus (rc={rc}), mencoba reconnect...")

    def _on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        """Proses pesan masuk dari lemari."""
        try:
            parts   = msg.topic.split("/")   # tetasco / {id} / {type}
            if len(parts) < 3:
                return
            device_id = parts[1]
            msg_type  = parts[2]
            payload   = json.loads(msg.payload.decode())

            if msg_type == "status":
                for cb in _status_callbacks:
                    cb(device_id, payload)
            elif msg_type == "sensor":
                for cb in _sensor_callbacks:
                    cb(device_id, payload)
            elif msg_type == "heartbeat":
                for cb in _heartbeat_callbacks:
                    cb(device_id, payload)
        except Exception as e:
            logger.error(f"[MQTT] Error proses pesan {msg.topic}: {e}")

    # ── Publish ───────────────────────────────────────────────────────────────
    def publish_command(self, device_id: str, actuator: str, state: bool) -> bool:
        """
        Kirim perintah kontrol ke lemari.
        Contoh: publish_command("lemari-1", "fan", True)
        Topic: tetasco/lemari-1/command/fan
        Payload: {"state": true, "ts": 1234567890}
        """
        if not self._connected or not self._client:
            logger.warning(f"[MQTT] Tidak terkoneksi, command {device_id}/{actuator} dibatalkan")
            return False

        topic   = f"tetasco/{device_id}/command/{actuator}"
        payload = json.dumps({"state": state, "ts": int(time.time())})

        with self._lock:
            result = self._client.publish(topic, payload, qos=MQTT_QOS, retain=False)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"[MQTT] Publish → {topic}: {payload}")
            return True
        else:
            logger.error(f"[MQTT] Gagal publish ke {topic}, rc={result.rc}")
            return False

    def publish_emergency_stop(self, device_id: str) -> bool:
        """Kirim emergency stop ke satu lemari."""
        if not self._connected or not self._client:
            return False
        topic   = f"tetasco/{device_id}/command/emergency_stop"
        payload = json.dumps({"ts": int(time.time())})
        result  = self._client.publish(topic, payload, qos=MQTT_QOS)
        return result.rc == mqtt.MQTT_ERR_SUCCESS

    def publish_emergency_stop_all(self) -> bool:
        """Kirim emergency stop ke SEMUA lemari sekaligus."""
        if not self._connected or not self._client:
            return False
        topic   = "tetasco/ALL/command/emergency_stop"
        payload = json.dumps({"ts": int(time.time())})
        result  = self._client.publish(topic, payload, qos=MQTT_QOS)
        return result.rc == mqtt.MQTT_ERR_SUCCESS

    # ── Register Callbacks ────────────────────────────────────────────────────
    def on_status(self, fn: Callable):
        """Register callback: fn(device_id: str, payload: dict)"""
        _status_callbacks.append(fn)

    def on_sensor(self, fn: Callable):
        """Register callback: fn(device_id: str, payload: dict)"""
        _sensor_callbacks.append(fn)

    def on_heartbeat(self, fn: Callable):
        """Register callback: fn(device_id: str, payload: dict)"""
        _heartbeat_callbacks.append(fn)

    @property
    def is_connected(self) -> bool:
        return self._connected


# ─── Singleton instance ───────────────────────────────────────────────────────
mqtt_manager = MQTTManager()
