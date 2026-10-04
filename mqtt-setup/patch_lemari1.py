"""patch_lemari1.py — Patch app.py dan test MQTT bridge"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('tetasco1', 22, 'tetasco1', 'saumata1192', timeout=10)
PROJ = '/home/tetasco1/Penetas-Telur/backend'

def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(120)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8', 'replace')); sys.stdout.flush()
        except: break
    return o.channel.recv_exit_status()

# 1. Install paho-mqtt (dengan output)
r('pip3 install "paho-mqtt>=2.0.0" 2>&1 | tail -5', '1. Install paho-mqtt')
r('python3 -c "import paho.mqtt.client; print(\'paho-mqtt version:\', paho.mqtt.client.__version__)"',
  '2. Verify paho-mqtt')

# 2. Cek apakah sudah ada patch
r(f'grep -c "mqtt_bridge" {PROJ}/app.py', '3. mqtt_bridge sudah ada di app.py?')

# 3. Buat backup app.py
r(f'cp {PROJ}/app.py {PROJ}/app.py.bak && echo "Backup OK"', '4. Backup app.py')

# 4. Inject mqtt_bridge ke app.py
# Cari baris "cloud_sync.start(sensor_manager, gpio_controller)" dan tambahkan setelahnya
PATCH_CMD = f"""
python3 << 'PYEOF'
import re

with open('{PROJ}/app.py', 'r') as f:
    content = f.read()

# Cek sudah ada patch
if 'mqtt_bridge' in content:
    print('ALREADY PATCHED, skip.')
else:
    # Tambahkan import di bagian atas (setelah from hardware.cloud_sync import)
    old_import = 'from hardware.cloud_sync import cloud_sync'
    new_import = '''from hardware.cloud_sync import cloud_sync
# === MQTT Bridge (tambahan otomatis) ===
try:
    from hardware.mqtt_bridge import mqtt_bridge as _mqtt_bridge
    _MQTT_BRIDGE_AVAILABLE = True
except ImportError as _e:
    _mqtt_bridge = None
    _MQTT_BRIDGE_AVAILABLE = False
    print(f"[WARN] mqtt_bridge tidak tersedia: {{_e}}")
# ======================================='''

    if old_import in content:
        content = content.replace(old_import, new_import, 1)
        print('Import patch: OK')
    else:
        # Tambahkan di awal file setelah docstring/imports
        print('WARNING: cloud_sync import tidak ditemukan, coba cara lain...')
        # Inject setelah baris pertama yang import
        lines = content.split('\\n')
        last_import = 0
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                last_import = i
        inject = [
            '',
            '# === MQTT Bridge (tambahan otomatis) ===',
            'try:',
            '    from hardware.mqtt_bridge import mqtt_bridge as _mqtt_bridge',
            '    _MQTT_BRIDGE_AVAILABLE = True',
            'except ImportError as _e:',
            '    _mqtt_bridge = None',
            '    _MQTT_BRIDGE_AVAILABLE = False',
            '# =======================================',
            '',
        ]
        lines = lines[:last_import+1] + inject + lines[last_import+1:]
        content = '\\n'.join(lines)

    # Tambahkan start mqtt_bridge setelah cloud_sync.start(...)
    old_start = 'cloud_sync.start(sensor_manager, gpio_controller)'
    new_start = '''cloud_sync.start(sensor_manager, gpio_controller)

    # === Start MQTT Bridge (tambahan otomatis) ===
    if _MQTT_BRIDGE_AVAILABLE and _mqtt_bridge:
        import os as _os
        _env_file = _os.path.join(_os.path.dirname(__file__), '.env')
        if _os.path.exists(_env_file):
            for _line in open(_env_file).readlines():
                _line = _line.strip()
                if _line and not _line.startswith('#') and '=' in _line:
                    _k, _v = _line.split('=', 1)
                    _os.environ.setdefault(_k.strip(), _v.strip())
        _mqtt_bridge.start(gpio_controller=gpio_controller, sensor_manager=sensor_manager)
        logger.info("MQTT Bridge dimulai: %s@%s", _os.getenv('DEVICE_ID','lemari-?'), _os.getenv('MQTT_BROKER','tetasco.my.id'))
    # ============================================='''

    if old_start in content:
        content = content.replace(old_start, new_start, 1)
        print('Start patch: OK')
    else:
        print(f'WARNING: target start tidak ditemukan!')

    with open('{PROJ}/app.py', 'w') as f:
        f.write(content)
    print('app.py patched successfully!')

PYEOF
"""
r(PATCH_CMD, '5. Patch app.py')

# 5. Verifikasi patch
r(f'grep -n "mqtt_bridge\|MQTT Bridge" {PROJ}/app.py', '6. Verifikasi patch di app.py')

# 6. Restart backend
print('\n[7. Restart backend]', flush=True)
r('pkill -f "python.*app.py" 2>/dev/null; echo killed', 'Kill old backend')
time.sleep(2)
r(f'cd {PROJ} && nohup python3 app.py > app.log 2>&1 & sleep 3 && echo "PID: $!" && tail -20 app.log',
  'Start backend & wait 3s for log')

c.close()
print('\nDone!', flush=True)
