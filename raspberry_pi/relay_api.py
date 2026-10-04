"""
TernakTelur - Incubator API (Flask + gpiozero)
==============================================
Hardware (VCC Relay = 3.3V dari Pi):
  GPIO 22 = Relay LAMPU PEMANAS 1 / HEATER 1   (IN1, Active-LOW)
  GPIO  6 = Relay LAMPU PEMANAS 2 / HEATER 2   (IN2, Active-HIGH)
  GPIO 26 = Relay KIPAS / FAN                   (IN3, Active-HIGH)
  GPIO  4 = Relay PELEMBAB / HUMIDIFIER         (IN4, Active-HIGH)
  GPIO 13 = Relay PEMBALIK TELUR / MOTOR        (IN5, Active-HIGH)
  GPIO 19 = Relay LAMPU UV / UV LIGHT           (IN6, Active-HIGH)

gpiozero menangani logika ON/OFF secara otomatis sesuai active_high flag.
Saat startup: initial_value=False -> semua relay MATI (OFF).
"""

import time
import random
import atexit
from flask import Flask, jsonify, request
from flask_cors import CORS
from gpiozero import DigitalOutputDevice

PORT = 5001

# =========================================================
# KONFIGURASI HARDWARE RELAY
# VCC Relay = 3.3V dari Pi Pin 1
# =========================================================
HEATER_PIN        = 22
HEATER_ACTIVE_HIGH = False  # Active-LOW: ON=0(LOW), OFF=1(HIGH)

HEATER2_PIN        = 6
HEATER2_ACTIVE_HIGH = True   # Sesuaikan True/False setelah tes hardware

FAN_PIN              = 26
FAN_ACTIVE_HIGH      = True    # Active-HIGH: ON=1(HIGH), OFF=0(LOW)

HUMIDIFIER_PIN        = 4
HUMIDIFIER_ACTIVE_HIGH = True  # Sesuaikan True/False setelah tes hardware IN3

MOTOR_PIN        = 13
MOTOR_ACTIVE_HIGH = True       # Sesuaikan True/False setelah tes hardware IN4

UV_LIGHT_PIN        = 19
UV_LIGHT_ACTIVE_HIGH = True    # Sesuaikan True/False setelah tes hardware IN5

devices = {}

try:
    devices['heater'] = DigitalOutputDevice(HEATER_PIN, active_high=HEATER_ACTIVE_HIGH, initial_value=False)
    print(f"[OK] Heater 1 GPIO {HEATER_PIN} siap (Active-{'HIGH' if HEATER_ACTIVE_HIGH else 'LOW'})")
except Exception as err:
    print(f"[WARN] Gagal inisialisasi GPIO Heater 1 ({HEATER_PIN}): {err}")

try:
    devices['heater2'] = DigitalOutputDevice(HEATER2_PIN, active_high=HEATER2_ACTIVE_HIGH, initial_value=False)
    print(f"[OK] Heater 2 GPIO {HEATER2_PIN} siap (Active-{'HIGH' if HEATER2_ACTIVE_HIGH else 'LOW'})")
except Exception as err:
    print(f"[WARN] Gagal inisialisasi GPIO Heater 2 ({HEATER2_PIN}): {err}")

try:
    devices['fan'] = DigitalOutputDevice(FAN_PIN, active_high=FAN_ACTIVE_HIGH, initial_value=False)
    print(f"[OK] Fan GPIO {FAN_PIN} siap (Active-{'HIGH' if FAN_ACTIVE_HIGH else 'LOW'})")
except Exception as err:
    print(f"[WARN] Gagal inisialisasi GPIO Fan ({FAN_PIN}): {err}")

try:
    devices['humidifier'] = DigitalOutputDevice(HUMIDIFIER_PIN, active_high=HUMIDIFIER_ACTIVE_HIGH, initial_value=False)
    print(f"[OK] Humidifier GPIO {HUMIDIFIER_PIN} siap (Active-{'HIGH' if HUMIDIFIER_ACTIVE_HIGH else 'LOW'})")
except Exception as err:
    print(f"[WARN] Gagal inisialisasi GPIO Humidifier ({HUMIDIFIER_PIN}): {err}")

try:
    devices['aux'] = DigitalOutputDevice(MOTOR_PIN, active_high=MOTOR_ACTIVE_HIGH, initial_value=False)
    print(f"[OK] Motor GPIO {MOTOR_PIN} siap (Active-{'HIGH' if MOTOR_ACTIVE_HIGH else 'LOW'})")
except Exception as err:
    print(f"[WARN] Gagal inisialisasi GPIO Motor ({MOTOR_PIN}): {err}")

try:
    devices['uv_light'] = DigitalOutputDevice(UV_LIGHT_PIN, active_high=UV_LIGHT_ACTIVE_HIGH, initial_value=False)
    print(f"[OK] UV Light GPIO {UV_LIGHT_PIN} siap (Active-{'HIGH' if UV_LIGHT_ACTIVE_HIGH else 'LOW'})")
except Exception as err:
    print(f"[WARN] Gagal inisialisasi GPIO UV Light ({UV_LIGHT_PIN}): {err}")
# =========================================================

app = Flask(__name__)
CORS(app)

# -- State in-memory ---------------------------------------
actuator_state: dict[str, bool] = {
    'heater':     False,
    'heater2':    False,
    'fan':        False,
    'humidifier': False,
    'aux':        False,
    'uv_light':   False,
}

_base_temp  = 37.5
_base_humid = 60.0


def _write_gpio(name: str, state: bool):
    dev = devices.get(name)
    if dev is not None:
        dev.on() if state else dev.off()


def _apply_all():
    for name, state in actuator_state.items():
        _write_gpio(name, state)


# Semua relay MATI saat startup
_apply_all()
print("[OK] Semua aktuator diset OFF saat startup.")


# -- Endpoints General -------------------------------------

@app.route('/api/health')
@app.route('/health')
@app.route('/')
def health():
    return jsonify({'status': 'ok', 'uptime': time.time()})


@app.route('/api/sensor')
def get_sensor():
    temp  = round(_base_temp  + random.uniform(-0.2, 0.2), 1)
    humid = round(_base_humid + random.uniform(-1.0, 1.0), 1)
    return jsonify({
        'temperature': temp,
        'humidity':    humid,
        'timestamp':   time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    })


@app.route('/api/actuators')
def get_actuators():
    return jsonify({'success': True, 'actuators': actuator_state})


@app.route('/api/actuators/<name>', methods=['POST'])
def set_actuator(name: str):
    if name not in actuator_state:
        return jsonify({'success': False, 'error': f'Aktuator tidak dikenal: {name}'}), 404

    data  = request.get_json(force=True, silent=True) or {}
    state = bool(data.get('state', False))

    actuator_state[name] = state
    _write_gpio(name, state)

    print(f'[Aktuator] {name} -> {"ON" if state else "OFF"}')
    return jsonify({'success': True, 'actuator': name, 'state': state})


@app.route('/api/emergency-stop', methods=['POST'])
def emergency_stop():
    for key in actuator_state:
        actuator_state[key] = False
    _apply_all()
    print('[EMERGENCY STOP] Semua aktuator dimatikan!')
    return jsonify({'success': True, 'message': 'Semua aktuator dimatikan'})


# -- Endpoints HEATER --------------------------------------
@app.route('/api/relay/status', methods=['GET'])
def relay_status():
    return jsonify({'success': True, 'relay': actuator_state['heater'], 'gpio': HEATER_PIN})


@app.route('/api/relay/on', methods=['POST'])
def relay_on():
    actuator_state['heater'] = True
    _write_gpio('heater', True)
    return jsonify({'success': True, 'message': 'Heater ON', 'state': 'on', 'gpio': HEATER_PIN})


@app.route('/api/relay/off', methods=['POST'])
def relay_off():
    actuator_state['heater'] = False
    _write_gpio('heater', False)
    return jsonify({'success': True, 'message': 'Heater OFF', 'state': 'off', 'gpio': HEATER_PIN})


@app.route('/api/relay/toggle', methods=['POST'])
def relay_toggle():
    new_state = not actuator_state['heater']
    actuator_state['heater'] = new_state
    _write_gpio('heater', new_state)
    return jsonify({'success': True, 'message': 'Heater toggled', 'relay': new_state, 'gpio': HEATER_PIN})


# -- Endpoints HEATER 2 ------------------------------------
@app.route('/api/heater2/status', methods=['GET'])
def heater2_status():
    return jsonify({'success': True, 'heater2': actuator_state['heater2'], 'gpio': HEATER2_PIN})


@app.route('/api/heater2/on', methods=['POST'])
def heater2_on():
    actuator_state['heater2'] = True
    _write_gpio('heater2', True)
    print('[Aktuator] heater2 -> ON')
    return jsonify({'success': True, 'message': 'Heater 2 ON', 'heater2': True, 'gpio': HEATER2_PIN})


@app.route('/api/heater2/off', methods=['POST'])
def heater2_off():
    actuator_state['heater2'] = False
    _write_gpio('heater2', False)
    print('[Aktuator] heater2 -> OFF')
    return jsonify({'success': True, 'message': 'Heater 2 OFF', 'heater2': False, 'gpio': HEATER2_PIN})


@app.route('/api/heater2/toggle', methods=['POST'])
def heater2_toggle():
    new_state = not actuator_state['heater2']
    actuator_state['heater2'] = new_state
    _write_gpio('heater2', new_state)
    print(f'[Aktuator] heater2 -> {"ON" if new_state else "OFF"}')
    return jsonify({'success': True, 'message': 'Heater 2 toggled', 'heater2': new_state, 'gpio': HEATER2_PIN})


# -- Endpoints FAN -----------------------------------------
@app.route('/api/fan/status', methods=['GET'])
def fan_status():
    return jsonify({'success': True, 'fan': actuator_state['fan'], 'gpio': FAN_PIN})


@app.route('/api/fan/on', methods=['POST'])
def fan_on():
    actuator_state['fan'] = True
    _write_gpio('fan', True)
    return jsonify({'success': True, 'message': 'Fan ON', 'fan': True, 'gpio': FAN_PIN})


@app.route('/api/fan/off', methods=['POST'])
def fan_off():
    actuator_state['fan'] = False
    _write_gpio('fan', False)
    return jsonify({'success': True, 'message': 'Fan OFF', 'fan': False, 'gpio': FAN_PIN})


@app.route('/api/fan/toggle', methods=['POST'])
def fan_toggle():
    new_state = not actuator_state['fan']
    actuator_state['fan'] = new_state
    _write_gpio('fan', new_state)
    return jsonify({'success': True, 'message': 'Fan toggled', 'fan': new_state, 'gpio': FAN_PIN})


# -- Endpoints HUMIDIFIER (Pelembab) -----------------------
@app.route('/api/humidifier/status', methods=['GET'])
def humidifier_status():
    return jsonify({'success': True, 'humidifier': actuator_state['humidifier'], 'gpio': HUMIDIFIER_PIN})


@app.route('/api/humidifier/on', methods=['POST'])
def humidifier_on():
    actuator_state['humidifier'] = True
    _write_gpio('humidifier', True)
    print(f'[Aktuator] humidifier -> ON')
    return jsonify({'success': True, 'message': 'Humidifier ON', 'humidifier': True, 'gpio': HUMIDIFIER_PIN})


@app.route('/api/humidifier/off', methods=['POST'])
def humidifier_off():
    actuator_state['humidifier'] = False
    _write_gpio('humidifier', False)
    print(f'[Aktuator] humidifier -> OFF')
    return jsonify({'success': True, 'message': 'Humidifier OFF', 'humidifier': False, 'gpio': HUMIDIFIER_PIN})


@app.route('/api/humidifier/toggle', methods=['POST'])
def humidifier_toggle():
    new_state = not actuator_state['humidifier']
    actuator_state['humidifier'] = new_state
    _write_gpio('humidifier', new_state)
    print(f'[Aktuator] humidifier -> {"ON" if new_state else "OFF"}')
    return jsonify({'success': True, 'message': 'Humidifier toggled', 'humidifier': new_state, 'gpio': HUMIDIFIER_PIN})


# -- Endpoints MOTOR PEMBALIK TELUR -----------------------
@app.route('/api/motor/status', methods=['GET'])
def motor_status():
    return jsonify({'success': True, 'motor': actuator_state['aux'], 'gpio': MOTOR_PIN})


@app.route('/api/motor/on', methods=['POST'])
def motor_on():
    actuator_state['aux'] = True
    _write_gpio('aux', True)
    print('[Aktuator] motor -> ON')
    return jsonify({'success': True, 'message': 'Motor ON', 'motor': True, 'gpio': MOTOR_PIN})


@app.route('/api/motor/off', methods=['POST'])
def motor_off():
    actuator_state['aux'] = False
    _write_gpio('aux', False)
    print('[Aktuator] motor -> OFF')
    return jsonify({'success': True, 'message': 'Motor OFF', 'motor': False, 'gpio': MOTOR_PIN})


@app.route('/api/motor/toggle', methods=['POST'])
def motor_toggle():
    new_state = not actuator_state['aux']
    actuator_state['aux'] = new_state
    _write_gpio('aux', new_state)
    print(f'[Aktuator] motor -> {"ON" if new_state else "OFF"}')
    return jsonify({'success': True, 'message': 'Motor toggled', 'motor': new_state, 'gpio': MOTOR_PIN})


# -- Endpoints UV LIGHT (Lampu UV) -------------------------
@app.route('/api/uv_light/status', methods=['GET'])
def uv_light_status():
    return jsonify({'success': True, 'uv_light': actuator_state['uv_light'], 'gpio': UV_LIGHT_PIN})


@app.route('/api/uv_light/on', methods=['POST'])
def uv_light_on():
    actuator_state['uv_light'] = True
    _write_gpio('uv_light', True)
    print('[Aktuator] uv_light -> ON')
    return jsonify({'success': True, 'message': 'UV Light ON', 'uv_light': True, 'gpio': UV_LIGHT_PIN})


@app.route('/api/uv_light/off', methods=['POST'])
def uv_light_off():
    actuator_state['uv_light'] = False
    _write_gpio('uv_light', False)
    print('[Aktuator] uv_light -> OFF')
    return jsonify({'success': True, 'message': 'UV Light OFF', 'uv_light': False, 'gpio': UV_LIGHT_PIN})


@app.route('/api/uv_light/toggle', methods=['POST'])
def uv_light_toggle():
    new_state = not actuator_state['uv_light']
    actuator_state['uv_light'] = new_state
    _write_gpio('uv_light', new_state)
    print(f'[Aktuator] uv_light -> {"ON" if new_state else "OFF"}')
    return jsonify({'success': True, 'message': 'UV Light toggled', 'uv_light': new_state, 'gpio': UV_LIGHT_PIN})


@atexit.register
def cleanup():
    for dev in devices.values():
        try:
            dev.off()
            dev.close()
        except Exception:
            pass
    print('\n[Cleanup] Semua GPIO dilepas.')


# -- Main --------------------------------------------------
if __name__ == '__main__':
    print('=' * 54)
    print('  TernakTelur - Incubator API (gpiozero)')
    print(f'  GPIO Heater 1   (IN1) : {HEATER_PIN}  (Active-LOW)')
    print(f'  GPIO Heater 2   (IN2) : {HEATER2_PIN}   (Active-HIGH)')
    print(f'  GPIO Fan        (IN3) : {FAN_PIN}  (Active-HIGH)')
    print(f'  GPIO Humidifier (IN4) : {HUMIDIFIER_PIN}   (Active-HIGH)')
    print(f'  GPIO Motor      (IN5) : {MOTOR_PIN}  (Active-HIGH)')
    print(f'  GPIO UV Light   (IN6) : {UV_LIGHT_PIN}  (Active-HIGH)')
    print(f'  Port                  : {PORT}')
    print('=' * 54)
    app.run(host='0.0.0.0', port=PORT, debug=False)

