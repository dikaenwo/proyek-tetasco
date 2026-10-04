import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

print('Monitoring 90 detik...')
time.sleep(90)

i,o,e = rp.exec_command('grep -i "CamPush\|broken\|error\|reconnect\|terhubung\|disconnect" /tmp/tetasco_backend.log | grep "19:3[5-9]\|19:4[0-9]" | tail -20')
result = o.read().decode('utf-8','replace').strip()
print('[CamPush logs 90 detik terakhir]:')
print(result or '(tidak ada error — koneksi stabil!)')

rp.close()
