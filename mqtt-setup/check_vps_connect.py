import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

i,o,e = sv.exec_command('ls -la ~/tetasco-connect')
print("[tetasco-connect dir]")
print(o.read().decode())

i,o,e = sv.exec_command('cat ~/tetasco-connect/docker-compose.yml')
print("\n[docker-compose.yml]")
print(o.read().decode())

sv.close()
