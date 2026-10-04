"""
debug_and_patch.py
==================
1. Cari exact MQTT control endpoint di server (bukan yang baru kita tambahkan)
2. Patch agar queue command  
3. Cek kenapa cloud_sync di Raspi tidak push sensor
"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# ── 1. Cari endpoint yang return "FAN ON — perintah dikirim ke lemari-1" ──────
srv(
    'docker exec tetasco-backend grep -n "FAN ON\\|perintah dikirim\\|actuator.*state\\|/devices/" /app/main.py | head -30',
    'Find control endpoint'
)
srv(
    'docker exec tetasco-backend grep -n "def.*device\\|def.*control\\|def.*actuator" /app/main.py | head -20',
    'Control function names'
)

# ── 2. Lihat 40 baris sekitar "perintah dikirim" ─────────────────────────────
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')

idx = main_py.find('perintah dikirim')
if idx >= 0:
    start = max(0, idx-600)
    end = min(len(main_py), idx+300)
    print('\n[Context "perintah dikirim"]:')
    print(main_py[start:end])
else:
    # Cari "FAN ON"
    idx = main_py.find('FAN ON')
    if idx >= 0:
        print('\n[Context "FAN ON"]:')
        print(main_py[max(0,idx-600):idx+300])
    else:
        print('[WARN] Teks tidak ditemukan!')

# ── 3. Cek cloud_sync di Raspi — apakah push_sensor_data pernah dipanggil? ──
print('\n\n=== RASPI cloud_sync diagnostic ===')
ras("grep -n 'push_sensor_data\\|check_cloud_health\\|is_online\\|mode.*online' /home/tetasco1/Penetas-Telur/backend/hardware/cloud_sync.py | head -20", 'cloud_sync push_sensor')
ras("python3 -c \"import urllib.request; r=urllib.request.urlopen('https://tetasco.my.id/api/health',timeout=5); print(r.read().decode())\" 2>&1", 'Test HTTPS ke server')
ras("python3 -c \"import urllib.request; data=b'{\\\"temperature\\\":37.5,\\\"humidity\\\":60}'; req=urllib.request.Request('https://tetasco.my.id/api/tetasco/1/sensors/history',data=data,headers={'Content-Type':'application/json'},method='POST'); r=urllib.request.urlopen(req,timeout=5); print(r.read().decode())\" 2>&1", 'Test manual sensor push')

sv.close()
rp.close()
