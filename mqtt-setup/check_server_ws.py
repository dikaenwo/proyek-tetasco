import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Baca camera_push function dari server
srv('sed -n "482,515p" /home/telur/tetasco-connect/backend/main.py', 'camera_push function')

# Cek apakah ada asyncio import dan wait_for
srv('grep -n "asyncio\|wait_for\|timeout" /home/telur/tetasco-connect/backend/main.py | head -10', 'asyncio usage')

sv.close()
