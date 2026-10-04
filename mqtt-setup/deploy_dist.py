import paramiko, sys, os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)
sftp = rp.open_sftp()

dist = Path(r'd:\Proyek Penetas Telur\TernakTelur-Cap\dist')
remote = '/home/tetasco1/Penetas-Telur/dist'

count = 0
for f in dist.rglob('*'):
    if f.is_file():
        rel = f.relative_to(dist).as_posix()
        remote_path = f'{remote}/{rel}'
        remote_dir  = remote_path.rsplit('/', 1)[0]
        try: sftp.mkdir(remote_dir)
        except: pass
        sftp.put(str(f), remote_path)
        count += 1

sftp.close()
rp.close()
print(f'[OK] {count} file di-upload ke Raspi dist/')
print('✅ Buka/refresh aplikasi di Android!')
