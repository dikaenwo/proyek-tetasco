"""read_start_script.py — Baca start_tetasco.sh dan fix Chromium redirect untuk Wayland"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(c, cmd, lbl='', timeout=15):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)'); sys.stdout.flush()
    return out

# Baca script startup
r(rs, 'cat ~/Penetas-Telur/scripts/start_tetasco.sh', '1. start_tetasco.sh')

# Cek apakah ada Chromium proses sekarang
r(rs, 'ps aux | grep chromium | grep -v grep', '2. Chromium proses running')

# Cek env vars Chromium yang running
r(rs, 'cat /proc/$(pgrep chromium | head -1)/environ 2>/dev/null | tr "\\0" "\\n" | grep -E "DISPLAY|WAYLAND|XDG_RUN" | head -5',
  '3. Chromium env vars')

# Cek wlrctl (Wayland remote control)
r(rs, 'which wlrctl wtype ydotool 2>/dev/null', '4. Wayland control tools')

# Test start Chromium dengan Wayland env
print('\n[5. Test start Chromium dengan WAYLAND_DISPLAY...]', flush=True)
rs.exec_command(
    'WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 '
    'DISPLAY=:0 '
    '/usr/bin/chromium '
    '--kiosk --noerrdialogs --disable-infobars '
    '--no-first-run --disable-translate '
    'http://127.0.0.1:5001/pair > /tmp/chrom_test.log 2>&1 &'
)
time.sleep(5)
r(rs, 'ps aux | grep chromium | grep -v grep | wc -l', '6. Chromium procs (setelah test)')
r(rs, 'cat /tmp/chrom_test.log 2>/dev/null | head -10', '7. Chromium start log')

rs.close()
print('\n✅ Done!', flush=True)
