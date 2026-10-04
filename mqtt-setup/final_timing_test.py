import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def srv(cmd, t=10):
    i,o,e = sv.exec_command(cmd, timeout=t)
    return o.read().decode('utf-8','replace').strip()

def ras(cmd, t=8):
    i,o,e = rp.exec_command(cmd, timeout=t)
    return o.read().decode('utf-8','replace').strip()

print('=== END-TO-END TIMING TEST ===')
print('(HP → Server → MQTT → Raspi GPIO)\n')

for action in ['on','off','on','off']:
    # Bersihkan log Raspi dulu
    rp.exec_command('tail -0 -F /tmp/tetasco_backend.log > /dev/null 2>&1 &')
    
    t0 = time.time()
    result = srv(f'curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/{action}')
    t1 = time.time()
    
    time.sleep(0.2)  # tunggu log Raspi
    log = ras('tail -3 /tmp/tetasco_backend.log')
    instant = 'INSTANT' in log
    
    print(f'  Fan {action:3}: {(t1-t0)*1000:5.0f}ms dari server | GPIO: {"⚡ INSTANT (MQTT)" if instant else "⏳ polling"}')
    time.sleep(0.4)

print()
# Cek log Raspi akhir
print('[Raspi recent log]')
print(ras('tail -6 /tmp/tetasco_backend.log'))

sv.close()
rp.close()
print('\n✅ Test selesai!')
