import paramiko, sys, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, t=10):
    i,o,e = rp.exec_command(cmd, timeout=t)
    return o.read().decode('utf-8','replace').strip()

# Stop motor dulu
ras('curl -s -X POST http://localhost:5001/api/hydraulic/command -H "Content-Type: application/json" -d \'{"action":"stop"}\'')
time.sleep(1)

# Test 1 cycle dengan t_full yang lebih pendek
# Coba 7.5s dulu (kurang 0.8s dari 8.3)
T_FULL = 7.5
T_EDGE = 3.0
N = 1  # 1 cycle dulu buat kalibrasi

print(f'[TEST] n_cycles={N}, t_edge={T_EDGE}s, t_full={T_FULL}s')
print(f'       Sequence: atas {T_EDGE}s | bawah {T_FULL}s | atas {T_FULL}s | tengah {T_EDGE}s')
print(f'       Total: {T_EDGE + N*2*T_FULL + T_EDGE:.1f}s')

raw = ras(f'curl -s -X POST http://localhost:5001/api/hydraulic/timed_oscillation -H "Content-Type: application/json" -d \'{{"n_cycles":{N},"t_center_to_edge":{T_EDGE},"t_full":{T_FULL}}}\'')
try:
    d = json.loads(raw)
    print(f'[OK] state={d["state"]} is_oscillating={d["is_oscillating"]}')
except:
    print('[RAW]', raw[:100])

rp.close()
print(f'\nMotor jalan! Amati: apakah masih mentok atas/bawah?')
print(f'Kalau masih mentok → coba t_full=7.0 atau 6.5')
print(f'Kalau terlalu pendek (tidak sampai) → coba t_full=7.8 atau 8.0')
