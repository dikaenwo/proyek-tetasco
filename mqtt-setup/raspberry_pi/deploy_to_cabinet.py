#!/usr/bin/env python3
"""
deploy_to_cabinet.py
====================
Script otomatis untuk deploy MQTT bridge ke Raspi Lemari manapun.
Jalankan dari PC Windows:

  python deploy_to_cabinet.py --id 2 --host 192.168.1.28 --user tetasco2 --pass saumata1192

Script akan:
  1. Upload mqtt_bridge.py ke hardware/mqtt_bridge.py
  2. Buat/update .env dengan konfigurasi MQTT yang benar
  3. Patch app.py untuk load mqtt_bridge (jika belum)
  4. Restart backend dengan kill PID + start fresh
  5. Verifikasi MQTT connected dan sensor data mengalir
"""
import argparse, paramiko, sys, time, io, os

# ── Credentials per lemari ──────────────────────────────────────────────────
MQTT_PASSWORDS = {
    1:  "lem1-IJjLZ7QCc2RI8UyC",
    2:  "lem2-lUIxylGuBhYhHoBO",
    3:  "lem3-9uBPvnFXWLrfJOmR",
    4:  "lem4-Wqgz48o7La3u5vVv",
    5:  "lem5-j3enIcA0VgJzOHjN",
    6:  "lem6-GHl8NFAeKcwK0Gv5",
    7:  "lem7-0mpPsU2nRHxcplTL",
    8:  "lem8-A2YCFUJagmZWvX9v",
    9:  "lem9-0QQQmada4AisnlTR",
    10: "lem10-yRFImHJak7zd0NRg",
    11: "lem11-KAAdaqep8CsBqgZx",
    12: "lem12-QPXHJgoww6qFdKi6",
    13: "lem13-qHBrLEs1G4ITwUt8",
    14: "lem14-VhqjQ2Itrz2xijhz",
    15: "lem15-bTWoC3i4ne7JpElM",
}

# Server MQTT (di LAN yang sama) — bisa ganti ke tetasco.my.id:443 untuk remote
MQTT_BROKER        = "192.168.1.14"
MQTT_PORT          = 9001
MQTT_TRANSPORT     = "websockets"
MQTT_USE_TLS       = "false"
MQTT_WS_PATH       = "/mqtt"
SENSOR_INTERVAL    = 10
HEARTBEAT_INTERVAL = 30

# Patch yang diinjeksi ke app.py
APP_PY_PATCH_MARKER = "# === Start MQTT Bridge (tambahan otomatis) ==="
APP_PY_PATCH = '''
# === Start MQTT Bridge (tambahan otomatis) ===
try:
    import os as _os, re as _re
    from hardware.mqtt_bridge import mqtt_bridge as _mqtt_bridge
    _MQTT_BRIDGE_AVAILABLE = True
except ImportError as _e:
    logger.warning("MQTT bridge tidak tersedia: %s", _e)
    _mqtt_bridge = None
    _MQTT_BRIDGE_AVAILABLE = False
'''

APP_PY_START_PATCH = '''
    # === Start MQTT Bridge (tambahan otomatis) ===
    if _MQTT_BRIDGE_AVAILABLE and _mqtt_bridge:
        try:
            import os as _os
            _env_file = _os.path.join(_os.path.dirname(__file__), '.env')
            if _os.path.exists(_env_file):
                for _line in open(_env_file).readlines():
                    _line = _line.strip()
                    if _line and not _line.startswith('#') and '=' in _line:
                        _k, _v = _line.split('=', 1)
                        _os.environ.setdefault(_k.strip(), _v.strip())
            _mqtt_bridge.start(gpio_controller=gpio_controller, sensor_manager=sensor_manager)
            logger.info("MQTT Bridge dimulai: %s@%s",
                        _os.getenv('DEVICE_ID','lemari-?'), _os.getenv('MQTT_BROKER','tetasco.my.id'))
        except Exception as _e:
            logger.warning("MQTT bridge tidak bisa start: %s", _e)
'''


def r(c, cmd, lbl='', timeout=30):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(timeout)
    out = b''
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            out += chunk
            sys.stdout.write(chunk.decode('utf-8', 'replace'))
            sys.stdout.flush()
        except: break
    return out.decode('utf-8', 'replace')


def deploy(host, user, password, cabinet_id, proj_path=None):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print(f"\n{'='*60}")
    print(f"  Deploy MQTT Bridge → Lemari-{cabinet_id} ({host})")
    print(f"{'='*60}\n", flush=True)

    # Koneksi SSH
    cl = paramiko.SSHClient()
    cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cl.connect(host, 22, user, password, timeout=15)
    print(f"[OK] SSH connected: {user}@{host}", flush=True)

    # Cari PROJ path
    if proj_path is None:
        out = r(cl, 'find ~ -name "app.py" -path "*/backend/*" 2>/dev/null | head -3')
        candidates = [p.strip() for p in out.strip().splitlines() if p.strip()]
        if not candidates:
            print("[ERROR] Tidak menemukan app.py! Tentukan --proj secara manual.", flush=True)
            cl.close()
            return False
        proj_path = os.path.dirname(candidates[0])
        print(f"[OK] Ditemukan project path: {proj_path}", flush=True)

    PROJ = proj_path
    device_id = f"lemari-{cabinet_id}"
    mqtt_pass = MQTT_PASSWORDS.get(cabinet_id)
    if not mqtt_pass:
        print(f"[ERROR] Tidak ada password untuk lemari-{cabinet_id}!", flush=True)
        cl.close()
        return False

    sftp = cl.open_sftp()

    # 1. Upload mqtt_bridge.py
    local_bridge = os.path.join(os.path.dirname(__file__), 'mqtt_bridge.py')
    if not os.path.exists(local_bridge):
        local_bridge = os.path.join(os.path.dirname(__file__), '..', 'raspberry_pi', 'mqtt_bridge.py')
    sftp.put(local_bridge, f'{PROJ}/hardware/mqtt_bridge.py')
    print(f"[OK] mqtt_bridge.py → {PROJ}/hardware/mqtt_bridge.py", flush=True)

    # 2. Buat/update .env
    env_content = (
        f"DEVICE_ID={device_id}\n"
        f"MQTT_BROKER={MQTT_BROKER}\n"
        f"MQTT_PORT={MQTT_PORT}\n"
        f"MQTT_TRANSPORT={MQTT_TRANSPORT}\n"
        f"MQTT_USE_TLS={MQTT_USE_TLS}\n"
        f"MQTT_WEBSOCKET_PATH={MQTT_WS_PATH}\n"
        f"MQTT_USER={device_id}\n"
        f"MQTT_PASS={mqtt_pass}\n"
        f"SENSOR_INTERVAL={SENSOR_INTERVAL}\n"
        f"HEARTBEAT_INTERVAL={HEARTBEAT_INTERVAL}\n"
    )
    sftp.putfo(io.BytesIO(env_content.encode()), f'{PROJ}/.env')
    print(f"[OK] .env dibuat untuk {device_id}", flush=True)

    # 3. Cek & patch app.py jika belum
    app_py = f'{PROJ}/app.py'
    try:
        with sftp.open(app_py, 'r') as f:
            content = f.read().decode('utf-8', 'replace')

        if APP_PY_PATCH_MARKER not in content:
            print("[INFO] app.py belum di-patch, menambahkan MQTT bridge...", flush=True)

            # Tambah import block sebelum "if __name__"
            import_insert = "\nfrom hardware.mqtt_bridge import mqtt_bridge as _mqtt_bridge\n"
            if "from hardware.mqtt_bridge" not in content:
                # Inject setelah block import terakhir (sebelum app = Flask)
                content = content.replace(
                    "app = Flask(__name__)",
                    f"{import_insert}\napp = Flask(__name__)",
                    1
                )

            # Tambah start block di dalam if __name__
            if APP_PY_PATCH_MARKER not in content:
                # Cari posisi app.run() dan inject sebelumnya
                content = content.replace(
                    "    app.run(",
                    f"{APP_PY_START_PATCH}\n    app.run(",
                    1
                )

            with sftp.open(app_py, 'w') as f:
                f.write(content.encode())
            print("[OK] app.py di-patch dengan MQTT bridge", flush=True)
        else:
            print("[OK] app.py sudah di-patch sebelumnya", flush=True)
    except Exception as e:
        print(f"[WARN] Gagal patch app.py: {e} — lanjutkan tanpa patch", flush=True)

    sftp.close()

    # 4. Kill proses lama + start bersih
    r(cl, f'''
PID=$(ss -tlnp | grep ":5001" | grep -oP "pid=\K[0-9]+")
if [ -n "$PID" ]; then
    echo "Killing PID $PID di port 5001"
    kill -9 $PID 2>/dev/null
    sleep 3
fi
ss -tlnp | grep 5001 || echo "Port 5001 BEBAS"
''', '4. Kill proses lama')

    r(cl, f'''
cd {PROJ} && > app.log
set -a && source .env && set +a
nohup python3 app.py >> app.log 2>&1 &
echo "PID: $!"
sleep 3
ss -tlnp | grep 5001 && echo "Flask OK" || echo "Flask belum start"
''', '5. Start backend')

    print(f'\n[Tunggu 15 detik untuk MQTT connect...]\n', flush=True)
    time.sleep(15)

    log = r(cl, f'grep "MQTTBridge\|Address already\|Serving" {PROJ}/app.log | head -10',
             '6. MQTT + Flask log')

    time.sleep(12)
    sensor_log = r(cl, f'grep "Connected\|Sensor publish\|Error" {PROJ}/app.log | tail -5',
                   '7. MQTT status')

    connected = "Connected ke broker" in log or "Connected ke broker" in sensor_log
    print(f"\n{'='*60}")
    print(f"  Lemari-{cabinet_id}: {'✅ MQTT CONNECTED!' if connected else '❌ MQTT belum connect'}")
    print(f"{'='*60}\n", flush=True)

    cl.close()
    return connected


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy MQTT Bridge ke Raspi Lemari")
    parser.add_argument("--id",   type=int, required=True, help="Nomor lemari (1-15)")
    parser.add_argument("--host", required=True, help="IP Raspi lemari, contoh: 192.168.1.28")
    parser.add_argument("--user", default="tetasco1", help="SSH username")
    parser.add_argument("--pass", dest="password", default="saumata1192", help="SSH password")
    parser.add_argument("--proj", default=None, help="Path project di Raspi (auto-detect jika tidak diisi)")
    args = parser.parse_args()

    ok = deploy(args.host, args.user, args.password, args.id, args.proj)
    sys.exit(0 if ok else 1)
