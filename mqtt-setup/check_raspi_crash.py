import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('grep -n "fetch\\|axios\\|useEffect" ~/Penetas-Telur/src/pages/DasborUtama.jsx')
print("[DasborUtama API calls]")
print(o.read().decode())

i,o,e = rp.exec_command('cat ~/Penetas-Telur/src/pages/DasborUtama.jsx | head -n 50')
print("\n[DasborUtama head]")
print(o.read().decode())

rp.close()
