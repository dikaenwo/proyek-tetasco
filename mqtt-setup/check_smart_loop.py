import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek mode device saat ini
ras('curl -s http://localhost:5001/api/control/mode', 'Device mode (auto/manual/RUNNING?)')
ras('curl -s http://localhost:5001/api/actuators', 'State aktuator sekarang')
ras('curl -s http://localhost:5001/api/sensor', 'Sensor (suhu & kelembaban)')

# Cek smart_control_loop — kondisi apa yang trigger fan & mist_maker
ras("sed -n '50,110p' ~/Penetas-Telur/backend/app.py", 'Smart loop fan & mist logic')

# Cek apakah AUTO mode aktif
ras("grep -n 'auto.*True\\|device_status.*RUNNING\\|control_state' ~/Penetas-Telur/backend/app.py | head -10", 'Auto mode condition')

rp.close()
