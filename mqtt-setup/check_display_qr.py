import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('ps aux | grep -i display_qr')
print("[ps aux display_qr]")
print(o.read().decode())

i,o,e = rp.exec_command('sudo systemctl status tetasco-display.service')
print("\n[systemctl status tetasco-display]")
print(o.read().decode())

rp.close()
