import paramiko, sys, os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)
sftp = rp.open_sftp()

web_src = Path(r'd:\Proyek Penetas Telur\TernakTelur-Web')
remote_dist = '/home/tetasco1/Penetas-Telur/dist'

print('Menghapus file android (TernakTelur-Cap) di Raspi...')
rp.exec_command(f'rm -rf {remote_dist}/*')
import time; time.sleep(1)

print('Mengunggah versi Web (TernakTelur-Web) ke Raspi...')
count = 0
for f in web_src.rglob('*'):
    if f.is_file():
        rel = f.relative_to(web_src).as_posix()
        remote_path = f'{remote_dist}/{rel}'
        remote_dir  = remote_path.rsplit('/', 1)[0]
        try: sftp.mkdir(remote_dir)
        except: pass
        sftp.put(str(f), remote_path)
        count += 1

# Restart browser di Raspi agar merefresh halamannya (optional, tapi kita refresh via xdotool jika bisa)
rp.exec_command('export DISPLAY=:0 && xdotool key F5')

sftp.close()
rp.close()
print(f'[OK] {count} file web berhasil dikembalikan ke Raspi dist/')
