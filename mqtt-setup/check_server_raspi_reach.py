import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=10):
    if lbl: print(f'\n=== {lbl} ===')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek bagaimana server forward ke Raspi (URL, IP)
srv("docker exec tetasco-backend grep -n 'raspi\\|192.168\\|forward\\|RASPI\\|device_url\\|local_url' /app/main.py | head -20", 'Server Raspi URL config')
srv("docker exec tetasco-backend grep -n 'hydraulic\\|timed' /app/main.py | head -10", 'Server hydraulic endpoints')
# Cek apakah server bisa reach Raspi port 5001
srv("docker exec tetasco-backend curl -s --max-time 3 http://192.168.1.27:5001/api/hydraulic/status | head -c 100", 'Server → Raspi reach test')

sv.close()
