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
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# 1. Cek body format set_actuator di Raspi
ras("grep -n -A 20 'def set_actuator' ~/Penetas-Telur/backend/app.py | head -25", 'set_actuator body')

# 2. Test direct POST ke Raspi dari server
srv("curl -s -X POST http://192.168.1.27:5001/api/actuators/fan -H 'Content-Type: application/json' -d '{\"state\": true}'", 'Test fan ON direct')
time.sleep(0.5)
srv("curl -s -X POST http://192.168.1.27:5001/api/actuators/fan -H 'Content-Type: application/json' -d '{\"state\": false}'", 'Test fan OFF direct')

# 3. Cek nama actuator Raspi vs nama di API server
ras("grep -n 'lamp_1\\|lamp_2\\|mist_maker\\|fan\\|motor\\|uv_light' ~/Penetas-Telur/backend/app.py | grep 'set_actuator\\|gpio_controller.set' | head -15", 'Actuator names')

rp.close()
sv.close()
