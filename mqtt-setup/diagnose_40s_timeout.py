import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def srv(cmd, lbl='', t=8):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

def ras(cmd, lbl='', t=8):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek FPS dan frame count di server
srv('curl -s http://localhost:8000/api/tetasco/1/camera/stats', 'Camera stats (frame count)')

# Cek apakah Raspi benar-benar kirim frames (fps > 0)
ras('curl -s http://localhost:5001/api/cloud/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(d)"', 'Cloud status')

# Cek uvicorn startup command
srv('cat /proc/$(docker inspect --format \'{{.State.Pid}}\' tetasco-backend)/cmdline 2>/dev/null | tr "\\0" " " | head -c 300', 'Uvicorn command')
srv('docker inspect tetasco-backend --format "{{.HostConfig.RestartPolicy}}" 2>/dev/null', 'Restart policy')

# Cek apakah ada timeout di uvicorn
srv('docker exec tetasco-backend ps aux | grep uvicorn', 'Uvicorn process')

# Cek nginx untuk timeout 40 detik
srv('grep -n "40\|timeout\|keep" /home/telur/tetasco-connect/nginx/nginx.conf | head -15', 'Nginx timeout config')

rp.close()
sv.close()
