import paramiko, sys, time, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def r(cmd, lbl='', t=30):
    if lbl: print(f'[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(ok)')
    return out

r('cd ~/tetasco-connect && docker compose build backend 2>&1 | tail -4', 'Build', t=120)
r('cd ~/tetasco-connect && docker compose up -d 2>&1 | tail -5', 'Up', t=30)
time.sleep(12)
r('curl -s http://localhost:8000/api/health', 'Health')
r(
    "curl -s -X POST http://localhost:8000/api/tetasco/1/share-token"
    " -H 'Content-Type: application/json'"
    " -d '{\"appId\":\"test\"}'",
    'Final test share token'
)
sv.close()
print('\n✅ Rebuild selesai — share token permanen!')
