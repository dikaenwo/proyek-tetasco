import paramiko, sys, time
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

# Test fan toggle dan ukur waktu
srv('docker logs tetasco-backend --tail 5 2>&1', 'Server log sebelum')
print('\nSend fan ON...')
t0 = time.time()
srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", 'Fan ON')
srv('docker logs tetasco-backend --tail 8 2>&1', 'Server log setelah fan ON (cek WS-Push)')

# Cek apakah _push_command_to_raspi berjalan (cari log WS-Push)
time.sleep(1)
srv('docker logs tetasco-backend --tail 5 2>&1 | grep -i "WS-Push\\|push\\|instant\\|error\\|warn" || echo "no match"', 'WS-Push log')

# Cek juga apakah ada error async
srv('docker logs tetasco-backend --tail 15 2>&1 | grep -i "error\\|exception\\|coroutine" || echo "no error"', 'Error check')

sv.close()
