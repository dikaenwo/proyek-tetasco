import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

print('Monitor 2 menit...')
time.sleep(120)

i,o,e = rp.exec_command('grep -iE "CamPush|broken|reconnect|terhubung" /tmp/tetasco_backend.log | grep -E "19:4[8-9]|19:5[0-9]|20:0" | tail -20')
result = o.read().decode('utf-8', 'replace').strip()
print('[Log 2 menit terakhir]:')
print(result or '✅ TIDAK ADA broken pipe — koneksi STABIL!')

# Cek berapa kali connect (idealnya hanya 1x setelah restart)
i2,o2,e2 = rp.exec_command('grep -c "broken pipe" /tmp/tetasco_backend.log')
print(f'\n[Total broken pipe sepanjang log]: {o2.read().decode().strip()} kali')

rp.close()
