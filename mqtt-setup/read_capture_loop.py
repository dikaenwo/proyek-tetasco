import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app = o.read().decode('utf-8','replace')

# Lihat context sekitar loop capture
start = app.find('_camera_capture_worker')
end   = app.find('\n\n# Start background', start)
print('[CAPTURE SECTION]:')
print(app[start:start+2000])
rp.close()
