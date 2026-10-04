import paramiko, sys, io
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

# Baca pairing.html
i,o,e = rs.exec_command('cat ~/Penetas-Telur/pairing.html')
html = o.read().decode('utf-8', 'replace')
print(f'[INFO] pairing.html: {len(html)} chars')

# Fix QR generation: warna hitam murni, ukuran lebih besar, margin lebih
OLD_QR = """    await QRCode.toCanvas(canvas, qrData, {
      width: 220,
      margin: 1,
      color: { dark: '#1A2B1C', light: '#FFFFFF' },
      errorCorrectionLevel: 'M',
    });"""

NEW_QR = """    await QRCode.toCanvas(canvas, qrData, {
      width: 260,
      margin: 2,
      color: { dark: '#000000', light: '#FFFFFF' },
      errorCorrectionLevel: 'H',
    });"""

if OLD_QR in html:
    html = html.replace(OLD_QR, NEW_QR, 1)
    print('[OK] QR settings fixed: hitam murni, 260px, margin 2, errorLevel H')
else:
    print('[WARN] Pattern tidak ditemukan!')
    # cari manual
    idx = html.find('QRCode.toCanvas')
    if idx > -1:
        print(f'Found at char {idx}:', html[idx:idx+200])

# Upload
sftp = rs.open_sftp()
sftp.putfo(io.BytesIO(html.encode()), '/home/tetasco1/Penetas-Telur/pairing.html')
sftp.close()
print('[OK] pairing.html uploaded')

# Reload Chromium ke /pair untuk lihat hasil
import time
rs.exec_command('bash ~/redirect_chromium.sh http://127.0.0.1:5001/pair >> /tmp/chromium_redirect.log 2>&1 &')
time.sleep(5)
r('ps aux | grep chromium | grep -v grep | wc -l', 'Chromium procs')
r('curl -s http://localhost:5001/api/claim-status', 'Claim status')

rs.close()
print('\n✅ Done! QR sekarang: hitam murni, 260px, error correction HIGH')
