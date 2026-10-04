import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('tail -n 100 /tmp/tetasco_backend.log')
print("[tetasco_backend.log last 100 lines]")
print(o.read().decode())

rp.close()
