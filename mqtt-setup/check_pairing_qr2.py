import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rs.exec_command(cmd, timeout=15)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(kosong)')
    return out

# Lihat bagian JS yang generate QR content di pairing.html
r('sed -n "400,576p" ~/Penetas-Telur/pairing.html', 'JS pairing.html (generate QR)')

rs.close()
