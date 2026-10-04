import paramiko, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(cmd, lbl='', timeout=15):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i,o,e = sv.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)'); sys.stdout.flush()
    return out

# Cek isi claims file di backend container
r('docker exec tetasco-backend cat /app/claims.json 2>/dev/null || echo "FILE NOT FOUND"', '1. claims.json isi')
r('docker exec tetasco-backend ls /app/ 2>/dev/null', '2. /app/ isi')
r('docker exec tetasco-backend find /app -name "*.json" 2>/dev/null', '3. JSON files di container')

# Cek _load_claims di main.py untuk tahu path file
r('docker exec tetasco-backend grep -n "_load_claims\|CLAIMS_FILE\|claims" /app/main.py 2>/dev/null | head -15', '4. claims path di main.py')

sv.close()
