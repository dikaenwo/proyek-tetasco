import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('ls -la ~/Penetas-Telur')
print("[ls ~/Penetas-Telur]")
print(o.read().decode())

i,o,e = rp.exec_command('ls -la ~/Penetas-Telur/frontend 2>/dev/null || echo "No frontend folder"')
print("\n[ls ~/Penetas-Telur/frontend]")
print(o.read().decode())

i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py | grep -A 20 "serve_frontend"')
print("\n[app.py serve_frontend route]")
print(o.read().decode())

rp.close()
