import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

def srv(cmd, lbl='', t=15):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek kode pending-commands polling di cloud_sync
ras("grep -n -A5 'pending.command\\|_fetch_pending\\|poll.*command\\|line 315' ~/Penetas-Telur/backend/hardware/cloud_sync.py | head -30", 'Pending commands code')
ras("sed -n '305,330p' ~/Penetas-Telur/backend/hardware/cloud_sync.py", 'Lines 305-330')

# Baca dan patch cloud_sync
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/hardware/cloud_sync.py')
cloud_sync = o.read().decode('utf-8','replace')
print(f'cloud_sync: {len(cloud_sync)} chars')

# Cari method _fetch_pending_commands dan jadikan no-op
if '_fetch_pending_commands' in cloud_sync:
    # Replace seluruh method dengan no-op
    import re
    # Cari definisi method
    m = re.search(r'    def _fetch_pending_commands\(self\)[^}]+?(?=\n    def |\nclass |\Z)', cloud_sync, re.DOTALL)
    if m:
        old_method = m.group(0)
        new_method = '''    def _fetch_pending_commands(self):
        """DISABLED: MQTT subscriber handles command delivery now (no polling needed)."""
        return  # MQTT handles this'''
        cloud_sync = cloud_sync.replace(old_method, new_method, 1)
        print('[OK] _fetch_pending_commands disabled (MQTT handles this)')
    else:
        print('[WARN] Method tidak ditemukan dengan regex, coba manual')
        idx = cloud_sync.find('def _fetch_pending_commands')
        print(cloud_sync[idx:idx+400])
elif 'pending' in cloud_sync.lower():
    # Cari baris yang memanggil fetch_pending
    idx = cloud_sync.lower().find('pending')
    print(f'Found "pending" at idx {idx}:')
    print(cloud_sync[max(0,idx-50):idx+200])

# Juga clear _cmd_queue di server setelah MQTT publish berhasil
# (supaya kalau Raspi restart, queue tidak re-eksekusi command lama)
i2,o2,e2 = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o2.read().decode('utf-8','replace')

# Clear _cmd_queue setelah MQTT berhasil publish
old_mqtt_sent = '    mqtt_sent = mqtt_manager.publish_command(device_id, actuator, state)'
new_mqtt_sent = '''    mqtt_sent = mqtt_manager.publish_command(device_id, actuator, state)
    if mqtt_sent:
        # Clear pending-commands queue (MQTT sudah deliver, tidak perlu polling)
        _cmd_queue[device_id] = {}'''

if old_mqtt_sent in main_py:
    main_py = main_py.replace(old_mqtt_sent, new_mqtt_sent, 1)
    print('[OK] Server: clear _cmd_queue setelah MQTT publish')

# Deploy server
sftp_s = sv.open_sftp()
sftp_s.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp_s.putfo(io.BytesIO(main_py.encode()), '/tmp/main_clear_queue.py')
sftp_s.close()

# Deploy Raspi
sftp_r = rp.open_sftp()
sftp_r.putfo(io.BytesIO(cloud_sync.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/cloud_sync.py')
sftp_r.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/hardware/cloud_sync.py && echo OK', 'Syntax cloud_sync')

srv('docker cp /tmp/main_clear_queue.py tetasco-backend:/app/main.py && echo ok', 'Deploy server')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart server', t=25)
time.sleep(12)
srv('curl -s http://localhost:8000/api/health', 'Health')

# Restart Raspi
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
transport = rp.get_transport()
chan = transport.open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1)
chan.close()
time.sleep(10)
ras('ss -tnp | grep 1883 | head -1', 'MQTT connected')

# Test race condition
print('\n=== Test race: ON → OFF (300ms) — harus akhir OFF ===')
time.sleep(3)
i3,o3,_ = sv.exec_command('curl -s -X POST http://localhost:8000/api/tetasco/1/devices/humidifier/on')
time.sleep(0.3)
i4,o4,_ = sv.exec_command('curl -s -X POST http://localhost:8000/api/tetasco/1/devices/humidifier/off')
o3.read(); o4.read()

time.sleep(2)
ras('tail -8 /tmp/tetasco_backend.log | grep -i "INSTANT\\|GPIO"', 'Final state (harus OFF)')

rp.close()
sv.close()
print('\n✅ Race fix selesai!')
