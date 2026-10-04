import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('grep -rn "location" ~/Penetas-Telur/src/')
print("[grep location]")
print(o.read().decode())

i,o,e = rp.exec_command('grep -rn "reload" ~/Penetas-Telur/src/')
print("\n[grep reload]")
print(o.read().decode())

rp.close()
