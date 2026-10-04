import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# Trigger error dan tangkap traceback
srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", 'Fan ON (trigger error)')
time.sleep(1)
srv('docker logs tetasco-backend --tail 30 2>&1', 'Error traceback')

# Lihat kode sekitar return DeviceCommandResponse
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')

idx = main_py.find('DeviceCommandResponse(')
if idx >= 0:
    print('\n[DeviceCommandResponse context]:')
    print(main_py[max(0,idx-400):idx+300])

# Cek apakah ada dua def control_device (konflik nama fungsi)
count = main_py.count('def control_device')
print(f'\nJumlah def control_device: {count}')
if count > 1:
    print('[WARN] Dua definisi! Python akan pakai yang terakhir')
    # Hapus definisi ke-2 (yang baru ditambahkan) agar tidak konflik
    # Cari posisi kedua
    pos1 = main_py.find('def control_device')
    pos2 = main_py.find('def control_device', pos1+1)
    print(f'pos1={pos1}, pos2={pos2}')
    # Tampilkan sekitar definisi pertama untuk konfirmasi
    print('\n[Def 1]:')
    print(main_py[max(0,pos1-50):pos1+100])
    print('\n[Def 2]:')
    print(main_py[max(0,pos2-50):pos2+100])

sv.close()
