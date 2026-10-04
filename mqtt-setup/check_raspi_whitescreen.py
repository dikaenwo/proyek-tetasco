import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

print("[Check what is in src folder]")
i,o,e = rp.exec_command('ls -la ~/Penetas-Telur/src')
print(o.read().decode())

print("\n[Check if there is an error boundary or what is the entry point]")
i,o,e = rp.exec_command('cat ~/Penetas-Telur/src/App.jsx 2>/dev/null || cat ~/Penetas-Telur/src/App.js 2>/dev/null')
print(o.read().decode()[:1000])

print("\n[Check vite config]")
i,o,e = rp.exec_command('cat ~/Penetas-Telur/vite.config.js 2>/dev/null')
print(o.read().decode())

rp.close()
