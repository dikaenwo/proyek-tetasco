import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

print("Running npm run build in ~/Penetas-Telur on Raspi...")
i,o,e = rp.exec_command('cd ~/Penetas-Telur && npm install && npm run build')
print(o.read().decode())
print(e.read().decode())

# Refresh page via xdotool
rp.exec_command('export DISPLAY=:0 && xdotool key F5')

rp.close()
