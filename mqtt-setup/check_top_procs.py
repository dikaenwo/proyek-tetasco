import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('ps aux --sort=-%cpu | head -n 15')
print("[Top CPU processes]")
print(o.read().decode())

i,o,e = rp.exec_command('crontab -l')
print("\n[Crontab]")
print(o.read().decode())

rp.close()
