import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=15):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')
    return o.read().decode('utf-8','replace').strip()

# Kill PID lama secara paksa
ras('kill -9 1651 2>/dev/null; pkill -9 -f "app.py" 2>/dev/null; sleep 2; echo done', 'Force kill PID 1651')
ras('pgrep -fa "app.py" | grep -v pgrep', 'Proses setelah kill')
ras('ss -tlnp | grep 5001 || echo "port 5001 bebas"', 'Port 5001')

# Verify file sudah diupdate
ras('grep -c "mqtt_subscriber" ~/Penetas-Telur/backend/app.py', 'Baris mqtt_subscriber di app.py')
ras('ls -la ~/Penetas-Telur/backend/hardware/mqtt_subscriber.py', 'File mqtt_subscriber.py')

# Hapus log lama agar bersih
ras('> /tmp/tetasco_backend.log', 'Clear log')

# Start ulang
transport = rp.get_transport()
chan = transport.open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(2)
chan.close()

time.sleep(12)
ras('pgrep -fa "python3 backend/app.py" | grep -v pgrep', 'Proses baru')
ras('ss -tlnp | grep 5001', 'Port 5001 bound')
ras('tail -25 /tmp/tetasco_backend.log', 'Log (cari MQTT-Sub connected)')

rp.close()
print('\nDone! Cek log di atas untuk status MQTT-Sub.')
