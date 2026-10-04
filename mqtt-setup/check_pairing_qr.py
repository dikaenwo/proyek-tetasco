import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rs.exec_command(cmd, timeout=15)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)')
    return out

# Cek library QR yang dipakai di pairing.html
r('grep -i "qr\|canvas\|svg" ~/Penetas-Telur/pairing.html | head -20', 'QR library di pairing.html')
r('wc -l ~/Penetas-Telur/pairing.html', 'panjang pairing.html')

# Lihat bagian QR generation
r('grep -n "qr\|token\|pair\|claim" ~/Penetas-Telur/pairing.html | head -30', 'kode QR/token/claim')

rs.close()
