import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n=== {lbl} ===')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Bagian tengah: _read_limits, start_oscillation, step_dt
ras("sed -n '200,420p' ~/Penetas-Telur/backend/hardware/hydraulic_controller.py", '_read_limits & start_oscillation')

# Config aktual
ras("cat ~/Penetas-Telur/backend/hardware/hydraulic_config.json 2>/dev/null || echo NOT_FOUND", 'hydraulic_config.json')

# Pin raw sekarang
ras("pinctrl get 5 6 2>/dev/null || raspi-gpio get 5 6 2>/dev/null || echo 'cannot read'", 'Pin 5&6 raw')

# Status hidrolik via API
ras("curl -s http://localhost:5001/api/hydraulic/status 2>/dev/null || curl -s http://localhost:5001/api/hydraulic 2>/dev/null", 'Hydraulic status API')

rp.close()
