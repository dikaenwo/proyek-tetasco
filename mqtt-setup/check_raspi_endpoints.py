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

# 1. Cek endpoint actuator Raspi
ras("grep -n 'route.*actuat\\|route.*relay\\|route.*set_act\\|set_actuator\\|def set_act' ~/Penetas-Telur/backend/app.py | head -15", 'Actuator endpoints')
# Test langsung dari server ke Raspi
srv("curl -sv http://192.168.1.27:5001/api/actuators 2>&1 | tail -10", 'Test Raspi from server')
ras("curl -s http://localhost:5001/api/actuators | head -c 300", 'Raspi actuators lokal')

rp.close()
sv.close()
