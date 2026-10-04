import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('grep -n "imencode\\|JPEG_QUALITY\\|IMWRITE" ~/Penetas-Telur/backend/app.py')
print('[imencode lines]:')
print(o.read().decode().strip())

rp.close()
