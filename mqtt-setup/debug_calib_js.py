import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/dist/kalibrasi.html')
html = o.read().decode('utf-8','replace')

# Cek startSeq function
start_idx = html.find('async function startSeq()')
end_idx = html.find('\nasync function ', start_idx + 10)
if end_idx < 0:
    end_idx = html.find('\nfunction ', start_idx + 10)
print('[startSeq current]:')
print(html[start_idx:start_idx+800])

rp.close()
