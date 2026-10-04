import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

# Check how sht20 is implemented in the backend
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/sensor_manager.py 2>/dev/null || cat ~/Penetas-Telur/backend/app.py | grep -iA 20 "sht20"')
print("[Sensor Manager or App.py]")
print(o.read().decode())

rp.close()
