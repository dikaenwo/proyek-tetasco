"""restore_and_reopen.py — Cek index.html restored + buka ulang Chromium ke kiosk interface"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(c, cmd, lbl='', timeout=20):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)'); sys.stdout.flush()
    return out

# 1. Lihat isi index.html yang sudah di-restore
r(rs, 'cat ~/Penetas-Telur/dist/index.html', '1. index.html (restored)')

# 2. Lihat isi assets
r(rs, 'ls -lh ~/Penetas-Telur/dist/assets/', '2. dist/assets/')

# 3. Bersihkan JS React mobile (untracked) yang kita upload tadi — biarkan hanya yg asli
r(rs, '''
# Hapus file React mobile app yang kita upload (bukan milik kiosk)
rm -f ~/Penetas-Telur/dist/assets/index-BHWDxDoo.js
rm -f ~/Penetas-Telur/dist/assets/index-iIc0Zb_o.css
rm -f ~/Penetas-Telur/dist/bg-card-ayam.png
rm -f ~/Penetas-Telur/dist/telur-ayam.png
rm -f ~/Penetas-Telur/dist/icon.png
echo "✓ Cleaned untracked React mobile files"
''', '3. Cleanup React mobile files')

r(rs, 'ls ~/Penetas-Telur/dist/assets/', '4. dist/assets/ after cleanup')

# 4. Buka ulang Chromium ke kiosk interface (http://127.0.0.1:5001)
print('\n[5. Buka Chromium ke kiosk interface...]', flush=True)
rs.exec_command(
    'bash ~/redirect_chromium.sh http://127.0.0.1:5001 >> /tmp/chromium_redirect.log 2>&1 &'
)
time.sleep(6)
r(rs, 'ps aux | grep chromium | grep -v grep | wc -l', '6. Chromium procs')
r(rs, 'tail -3 /tmp/chromium_redirect.log', '7. Redirect log')

# 5. Cek claim status untuk confirm
r(rs, 'curl -s http://localhost:5001/api/claim-status', '8. Claim status')

rs.close()
print('\n✅ Done! Kiosk interface seharusnya tampil di LCD lagi', flush=True)
