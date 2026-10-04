"""verify_android_flow.py — Verifikasi full flow untuk Android control"""
import paramiko, sys, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)
cl = paramiko.SSHClient()
cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cl.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)
PROJ = '/home/tetasco1/Penetas-Telur/backend'

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(15)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

print("=" * 60)
print("  VERIFIKASI END-TO-END FLOW ANDROID")
print("=" * 60)

# === 1. SENSOR READ (Android GET data) ===
print("\n\n【FASE 1: READ Sensor (Android baca suhu)】", flush=True)
r(cs, 'curl -s -w "\\nHTTP: %{http_code}" http://localhost:8000/api/tetasco/1/sensor | python3 -m json.tool',
  '1a. Local API sensor')
r(cs, 'curl -s -w "\\nHTTP: %{http_code}" http://localhost:8000/api/devices',
  '1b. Devices list')

# === 2. CORS headers (Android HTTP request) ===
print("\n\n【FASE 2: CORS Headers (penting untuk Android WebView/Retrofit)】", flush=True)
r(cs, 'curl -si -X OPTIONS http://localhost:8000/api/tetasco/1/sensor -H "Origin: http://android.local" | head -15',
  '2a. CORS headers local')
r(cs, 'curl -si -X OPTIONS http://localhost/api/tetasco/1/sensor -H "Origin: http://android.local" | head -15',
  '2b. CORS via Nginx')

# === 3. ACTUATOR CONTROL (Android kirim command) ===
print("\n\n【FASE 3: ACTUATOR Control (Android ON/OFF relay)】", flush=True)
r(cs, 'curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on | python3 -m json.tool',
  '3a. Command: fan ON')

print('\n[Tunggu 3 detik untuk MQTT propagate...]\n', flush=True)
time.sleep(3)

# Cek lemari menerima command
r(cl, f'grep "command\|fan\|Command" {PROJ}/app.log | tail -5', '3b. Lemari terima command?')

r(cs, 'curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/off | python3 -m json.tool',
  '3c. Command: fan OFF')

# === 4. Nginx proxy (Android via internet) ===
print("\n\n【FASE 4: Nginx Proxy (Android via domain)】", flush=True)
r(cs, 'curl -si http://localhost/api/health | head -10', '4a. Nginx /api/health')
r(cs, 'curl -s http://localhost/api/tetasco/1/sensor | python3 -m json.tool', '4b. Nginx sensor endpoint')

# === 5. Cloudflare (Android dari internet) ===
print("\n\n【FASE 5: Cloudflare (Android dari luar jaringan)】", flush=True)
r(cs, 'curl -s --max-time 10 https://tetasco.my.id/api/health 2>&1', '5a. Cloudflare API health')
r(cs, 'curl -s --max-time 10 https://tetasco.my.id/api/tetasco/1/sensor 2>&1 | python3 -m json.tool',
  '5b. Cloudflare sensor endpoint')

# === 6. Main.py CORS check ===
print("\n\n【FASE 6: FastAPI CORS config】", flush=True)
r(cs, 'docker exec tetasco-backend grep -n "CORS\|cors\|allow_origins\|allow_methods" /app/main.py | head -10',
  '6. CORS config di FastAPI')

cl.close()
cs.close()
print('\n✅ Verifikasi selesai!', flush=True)
