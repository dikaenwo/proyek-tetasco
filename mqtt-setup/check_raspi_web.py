import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

ras('find ~/Penetas-Telur -name "*.html" | head -20', 'HTML files')
ras('ls ~/Penetas-Telur/', 'Root dir')
ras('ls ~/Penetas-Telur/frontend/ 2>/dev/null || echo "no frontend dir"', 'Frontend dir')
ras('grep -n "static" ~/Penetas-Telur/backend/app.py | head -10', 'Static config in app.py')

rp.close()
