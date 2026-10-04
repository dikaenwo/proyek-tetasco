import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip())

r("wc -l ~/Penetas-Telur/backend/app.py", 'Line count')
r("grep -n 'def \\|TETASCO\\|cloud_sync\\|push_frame\\|if __name__\\|cam_push\\|CamPush' ~/Penetas-Telur/backend/app.py", 'Key sections')
r("tail -80 ~/Penetas-Telur/backend/app.py", 'Last 80 lines')

rp.close()
