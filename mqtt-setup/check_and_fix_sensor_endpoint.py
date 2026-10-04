"""check_and_fix_sensor_endpoint.py — Lihat kode sensor endpoint & patch final"""
import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

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

MAIN = '/home/telur/tetasco-connect/backend/main.py'

# 1. Lihat sensor endpoint saat ini
r(cs, f'sed -n "219,250p" {MAIN}', '1. Sensor endpoint code sekarang (baris 219-250)')

# 2. Baca file dan lihat baris 240-245
r(cs, f'grep -n "actuators\|device_status" {MAIN} | head -20', '2. Grep actuators di main.py')

# 3. Baca file, fix langsung via Python
i, o, e = cs.exec_command(f'cat {MAIN}')
content = o.read().decode('utf-8', 'replace')

lines = content.split('\n')
changed = 0
new_lines = []
for i, line in enumerate(lines):
    # Fix: baris yang mengandung "actuators" + "data.get" → ubah ke status_cache
    if '"actuators"' in line and 'data.get("actuators"' in line:
        old = line
        # Ekstrak indentation
        indent = len(line) - len(line.lstrip())
        new_line = ' ' * indent + '"actuators":    {k: v for k, v in device_status_cache.get(device_id, {}).items() if k not in ("ts", "device_id")},'
        new_lines.append(new_line)
        print(f'[Fix baris {i+1}]: {old.strip()[:60]}', flush=True)
        print(f'           → {new_line.strip()[:60]}', flush=True)
        changed += 1
    # Fix: status endpoint double-nesting "actuators": status → exclude ts/device_id  
    elif '"actuators"' in line and '"actuators":   status' in line:
        old = line
        indent = len(line) - len(line.lstrip())
        new_line = ' ' * indent + '"actuators":   {k: v for k, v in status.items() if k not in ("ts", "device_id")},'
        new_lines.append(new_line)
        print(f'[Fix status baris {i+1}]: {old.strip()[:60]}', flush=True)
        changed += 1
    else:
        new_lines.append(line)

print(f'\n[Total fixes: {changed}]', flush=True)

if changed > 0:
    new_content = '\n'.join(new_lines)
    sftp = cs.open_sftp()
    sftp.putfo(io.BytesIO(new_content.encode()), MAIN)
    sftp.close()
    print('[OK] main.py ditulis ulang', flush=True)

    r(cs, 'docker restart tetasco-backend && sleep 6', 'Restart server')
    r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor | python3 -m json.tool', 'Sensor endpoint FINAL')
    r(cs, 'curl -s http://localhost:8000/api/tetasco/1/status | python3 -m json.tool', 'Status endpoint FINAL')
else:
    print('[INFO] Tidak ada fix yang perlu diterapkan', flush=True)
    r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor | python3 -m json.tool', 'Sensor endpoint (current)')

cs.close()
print('\nDone!', flush=True)
