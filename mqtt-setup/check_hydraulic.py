import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Lihat file hydraulic_controller
ras('cat ~/Penetas-Telur/backend/hardware/hydraulic_controller.py', 'hydraulic_controller.py')

# Cek GPIO config yang dipakai (pin berapa)
ras("grep -n 'motor\|hydraulic\|relay\|IN\|led\|button\|limit\|GPIO\|pin' ~/Penetas-Telur/backend/hardware/gpio_controller.py | head -20", 'GPIO pins')

rp.close()
