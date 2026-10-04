import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(cmd, lbl='', t=15):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(kosong)')
    return out

# Log app.py
r('tail -50 /tmp/tetasco_backend.log 2>/dev/null || echo "no log at /tmp"', 'app.py log (50 baris terakhir)')

# Cek koneksi MQTT dari raspi
r('cat ~/Penetas-Telur/backend/app.py | grep -E "MQTT|mqtt|broker|connect|host" | head -20', 'MQTT config di app.py')

# Test koneksi ke server MQTT
r('python3 -c "import socket; s=socket.create_connection((\"192.168.1.14\",1883),3); print(\"MQTT TCP 1883: OK\"); s.close()" 2>&1', 'Test MQTT TCP 1883')
r('python3 -c "import socket; s=socket.create_connection((\"tetasco.my.id\",9001),5); print(\"MQTT WS 9001: OK\"); s.close()" 2>&1', 'Test MQTT WS 9001')

rp.close()
