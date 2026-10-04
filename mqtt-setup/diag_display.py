"""diag_display.py — Diagnosa display server Raspi (X11 vs Wayland) + cari cara start Chromium"""
import paramiko, sys
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

# Display server
r(rs, 'ls /tmp/.X* 2>/dev/null || echo "No X sockets"', '1. X11 sockets')
r(rs, 'ls /run/user/$(id -u)/wayland* 2>/dev/null || echo "No Wayland sockets"', '2. Wayland sockets')
r(rs, 'echo $XDG_SESSION_TYPE', '3. Session type ($XDG_SESSION_TYPE)')
r(rs, 'loginctl show-session $(loginctl | grep $(whoami) | awk "{print $1}" | head -1) -p Type 2>/dev/null || echo "n/a"', '4. loginctl session type')

# Env vars dari proses yang sudah running
r(rs, 'cat /proc/$(pgrep -f "backend/app.py" | head -1)/environ 2>/dev/null | tr "\\0" "\\n" | grep -E "DISPLAY|WAYLAND|XDG" | head -10', '5. Backend env vars')

# Cara Chromium dijalankan saat boot
r(rs, 'cat ~/.config/autostart/*.desktop 2>/dev/null | head -30', '6. Autostart desktop entries')
r(rs, 'cat /etc/xdg/autostart/*.desktop 2>/dev/null | grep -i "chrom" | head -5', '7. System autostart (chromium)')
r(rs, 'cat ~/tetasco_start.sh 2>/dev/null || cat ~/start_kiosk.sh 2>/dev/null || echo "No start script found"', '8. Custom start scripts')
r(rs, 'systemctl --user list-units --all | grep -i "chrom\|kiosk\|tetasco" 2>/dev/null | head -5', '9. User systemd units')

# Cari .service files
r(rs, 'find /home/tetasco1 /etc/systemd -name "*.service" 2>/dev/null | xargs grep -l "chromium" 2>/dev/null', '10. Service files with chromium')

# Cek proses yang ada di display
r(rs, 'ps aux | grep -E "chromium|wayfire|labwc|openbox|Xvnc|wayvnc|x11vnc" | grep -v grep | head -10', '11. Display processes running')

# Cek script startup di /opt atau /home
r(rs, 'find /opt /home/tetasco1 -name "*.sh" 2>/dev/null | xargs grep -l "chromium" 2>/dev/null | head -5', '12. Shell scripts with chromium')

rs.close()
print('\n✅ Done diagnosa!', flush=True)
