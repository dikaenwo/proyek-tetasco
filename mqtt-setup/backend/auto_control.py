"""
auto_control.py — Tetasco Connect Auto Control Engine
======================================================
Logic kontrol otomatis berdasarkan pembacaan sensor SHT20.

Cara kerja:
  - Setiap kali sensor data diterima via MQTT, fungsi evaluate() dipanggil
  - Dibandingkan dengan target range berdasarkan jenis telur (species)
  - Jika suhu/kelembaban di luar range → publish MQTT command ON/OFF ke aktuator

Aktuator yang dikontrol:
  - heater  : pemanas → nyala jika suhu < min, mati jika suhu > max
  - humidifier : pelembab → nyala jika kelembaban < min, mati jika kelembaban > max
  - fan     : kipas ventilasi → nyala jika suhu > max (bantu dinginkan)
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Profil Range Per Jenis Telur ────────────────────────────────────────────
@dataclass
class SpeciesProfile:
    name: str
    temp_min: float     # °C — suhu minimum (heater ON jika di bawah ini)
    temp_max: float     # °C — suhu maksimum (heater OFF jika di atas ini)
    hum_min: float      # %  — kelembaban minimum (humidifier ON jika di bawah ini)
    hum_max: float      # %  — kelembaban maksimum (humidifier OFF jika di atas ini)
    incubation_days: int = 21  # lama inkubasi (informasi saja)

SPECIES_PROFILES: dict[str, SpeciesProfile] = {
    "ayam": SpeciesProfile(
        name="Ayam",
        temp_min=37.5,
        temp_max=38.3,
        hum_min=50.0,
        hum_max=60.0,
        incubation_days=21,
    ),
    "puyuh": SpeciesProfile(
        name="Puyuh",
        temp_min=37.2,
        temp_max=37.8,
        hum_min=45.0,
        hum_max=55.0,
        incubation_days=17,
    ),
    "bebek": SpeciesProfile(
        name="Bebek",
        temp_min=37.5,
        temp_max=38.0,
        hum_min=55.0,
        hum_max=70.0,
        incubation_days=28,
    ),
    "angsa": SpeciesProfile(
        name="Angsa",
        temp_min=37.4,
        temp_max=38.0,
        hum_min=55.0,
        hum_max=75.0,
        incubation_days=30,
    ),
    "kalkun": SpeciesProfile(
        name="Kalkun",
        temp_min=37.5,
        temp_max=38.3,
        hum_min=55.0,
        hum_max=65.0,
        incubation_days=28,
    ),
}

# Default ke ayam jika species tidak diketahui
DEFAULT_SPECIES = "ayam"


# ─── State Tracking Per Lemari ────────────────────────────────────────────────
@dataclass
class DeviceAutoState:
    """Track status aktuator terakhir agar tidak kirim MQTT berulang-ulang."""
    heater_on: Optional[bool] = None
    humidifier_on: Optional[bool] = None
    fan_on: Optional[bool] = None
    species: str = DEFAULT_SPECIES
    auto_mode: bool = True   # bisa di-disable via API jika user ingin kontrol manual


# ─── Engine Utama ─────────────────────────────────────────────────────────────
class AutoControlEngine:
    """
    Engine kontrol otomatis untuk semua lemari.
    Dipanggil setiap kali data sensor baru masuk.
    """

    def __init__(self):
        # Simpan state per device_id
        self._states: dict[str, DeviceAutoState] = {}

    def get_or_create_state(self, device_id: str) -> DeviceAutoState:
        if device_id not in self._states:
            self._states[device_id] = DeviceAutoState()
        return self._states[device_id]

    def set_species(self, device_id: str, species: str):
        """Atur jenis telur untuk lemari tertentu."""
        species = species.lower()
        if species not in SPECIES_PROFILES:
            logger.warning(f"[AutoControl] Species '{species}' tidak dikenali, pakai default '{DEFAULT_SPECIES}'")
            species = DEFAULT_SPECIES
        state = self.get_or_create_state(device_id)
        state.species = species
        logger.info(f"[AutoControl] {device_id} species diset ke: {species}")

    def set_auto_mode(self, device_id: str, enabled: bool):
        """Enable/disable auto control untuk lemari tertentu."""
        state = self.get_or_create_state(device_id)
        state.auto_mode = enabled
        logger.info(f"[AutoControl] {device_id} auto mode: {'ON' if enabled else 'OFF (Manual)'}")

    def get_status(self, device_id: str) -> dict:
        """Kembalikan status auto control lemari."""
        state = self.get_or_create_state(device_id)
        profile = SPECIES_PROFILES.get(state.species, SPECIES_PROFILES[DEFAULT_SPECIES])
        return {
            "device_id": device_id,
            "auto_mode": state.auto_mode,
            "species": state.species,
            "profile": {
                "name": profile.name,
                "temp_min": profile.temp_min,
                "temp_max": profile.temp_max,
                "hum_min": profile.hum_min,
                "hum_max": profile.hum_max,
            },
            "actuator_state": {
                "heater": state.heater_on,
                "humidifier": state.humidifier_on,
                "fan": state.fan_on,
            }
        }

    def get_all_status(self) -> list[dict]:
        """Status semua lemari yang punya auto control."""
        return [self.get_status(did) for did in self._states]

    def evaluate(self, device_id: str, temp: float, humidity: float, publish_fn) -> dict:
        """
        Evaluasi kondisi sensor dan kirim perintah aktuator jika diperlukan.

        Args:
            device_id   : ID lemari, contoh 'lemari-1'
            temp        : suhu saat ini (°C)
            humidity    : kelembaban saat ini (%)
            publish_fn  : callable(device_id, actuator, state) → bool
                          biasanya mqtt_manager.publish_command

        Returns:
            dict berisi keputusan yang diambil
        """
        state   = self.get_or_create_state(device_id)
        profile = SPECIES_PROFILES.get(state.species, SPECIES_PROFILES[DEFAULT_SPECIES])
        actions = {}

        if not state.auto_mode:
            logger.debug(f"[AutoControl] {device_id} auto mode OFF, skip.")
            return {"auto_mode": False}

        # ── Kontrol Heater ──────────────────────────────────────────────────────
        if temp < profile.temp_min:
            # Suhu terlalu rendah → nyalakan heater
            if state.heater_on is not True:
                ok = publish_fn(device_id, "heater", True)
                state.heater_on = True
                actions["heater"] = {"action": "ON", "reason": f"temp={temp}°C < min={profile.temp_min}°C", "sent": ok}
                logger.info(f"[AutoControl] {device_id} HEATER ON — suhu {temp}°C < {profile.temp_min}°C")

        elif temp > profile.temp_max:
            # Suhu terlalu tinggi → matikan heater
            if state.heater_on is not False:
                ok = publish_fn(device_id, "heater", False)
                state.heater_on = False
                actions["heater"] = {"action": "OFF", "reason": f"temp={temp}°C > max={profile.temp_max}°C", "sent": ok}
                logger.info(f"[AutoControl] {device_id} HEATER OFF — suhu {temp}°C > {profile.temp_max}°C")

        else:
            # Suhu dalam range → tidak perlu ubah apapun
            actions["heater"] = {"action": "HOLD", "reason": f"temp={temp}°C dalam range [{profile.temp_min}–{profile.temp_max}]°C"}

        # ── Kontrol Fan (bantu buang panas jika suhu berlebih) ──────────────────
        if temp > profile.temp_max:
            if state.fan_on is not True:
                ok = publish_fn(device_id, "fan", True)
                state.fan_on = True
                actions["fan"] = {"action": "ON", "reason": f"temp={temp}°C > max={profile.temp_max}°C (cooling)", "sent": ok}
                logger.info(f"[AutoControl] {device_id} FAN ON — bantu dinginkan suhu {temp}°C")
        else:
            if state.fan_on is not False:
                ok = publish_fn(device_id, "fan", False)
                state.fan_on = False
                actions["fan"] = {"action": "OFF", "reason": "suhu normal", "sent": ok}

        # ── Kontrol Humidifier ──────────────────────────────────────────────────
        if humidity < profile.hum_min:
            # Kelembaban terlalu rendah → nyalakan humidifier
            if state.humidifier_on is not True:
                ok = publish_fn(device_id, "humidifier", True)
                state.humidifier_on = True
                actions["humidifier"] = {"action": "ON", "reason": f"hum={humidity}% < min={profile.hum_min}%", "sent": ok}
                logger.info(f"[AutoControl] {device_id} HUMIDIFIER ON — kelembaban {humidity}% < {profile.hum_min}%")

        elif humidity > profile.hum_max:
            # Kelembaban terlalu tinggi → matikan humidifier
            if state.humidifier_on is not False:
                ok = publish_fn(device_id, "humidifier", False)
                state.humidifier_on = False
                actions["humidifier"] = {"action": "OFF", "reason": f"hum={humidity}% > max={profile.hum_max}%", "sent": ok}
                logger.info(f"[AutoControl] {device_id} HUMIDIFIER OFF — kelembaban {humidity}% > {profile.hum_max}%")

        else:
            actions["humidifier"] = {"action": "HOLD", "reason": f"hum={humidity}% dalam range [{profile.hum_min}–{profile.hum_max}]%"}

        return {
            "auto_mode": True,
            "device_id": device_id,
            "species": state.species,
            "sensor": {"temp": temp, "humidity": humidity},
            "profile": {"temp": [profile.temp_min, profile.temp_max], "hum": [profile.hum_min, profile.hum_max]},
            "actions": actions,
        }


# ─── Singleton Instance ───────────────────────────────────────────────────────
auto_control = AutoControlEngine()
