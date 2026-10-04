import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/dist/kalibrasi.html')
html = o.read().decode('utf-8','replace')

import re

# Ganti const t_edge = ... dan pakai t_start/t_end via regex
html = re.sub(
    r"const t_edge = \+document\.getElementById\('t_edge'\)\.value;",
    "const t_start = +document.getElementById('t_start').value;\n    const t_end   = +document.getElementById('t_end').value;",
    html
)
html = re.sub(r'if\(elapsed < t_edge\)', 'if(elapsed < t_start)', html)
html = re.sub(r'else if\(elapsed < seqTotal - t_edge\)', 'else if(elapsed < seqTotal - t_end)', html)

# Verifikasi
sisa = [l.strip() for l in html.split('\n') if 't_edge' in l]
print('[Sisa t_edge]:', sisa if sisa else 'Tidak ada ✅')

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(html.encode()), '/home/tetasco1/Penetas-Telur/dist/kalibrasi.html')
sftp.close()
rp.close()
print('✅ HTML bersih! Refresh browser kalibrasi.')
