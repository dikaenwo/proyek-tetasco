import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=15):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek error di server log
srv('docker logs tetasco-backend --tail 20 2>&1', 'Server log 20 baris terakhir')

# Test langsung: apakah server control endpoint error?
print('\n=== Test control endpoint ===')
srv("curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", 'HTTP status fan/on')
srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on 2>&1 | head -c 200", 'Response fan/on')

# Cek apakah _cmd_queue ada di main.py
srv("docker exec tetasco-backend grep -n '_cmd_queue\\|cmd_queue' /app/main.py | head -10", '_cmd_queue in main.py')

sv.close()
