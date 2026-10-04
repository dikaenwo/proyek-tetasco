"""restore_raspi_kiosk.py — Restore kiosk interface di Raspi dari git / backup"""
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

# 1. Cek git status dist/
r(rs, 'cd ~/Penetas-Telur && git log --oneline -5 2>/dev/null || echo "No git"', '1. Git log')
r(rs, 'cd ~/Penetas-Telur && git status dist/ 2>/dev/null | head -15', '2. Git status dist/')
r(rs, 'ls -la ~/Penetas-Telur/dist/', '3. Current dist/ contents')

# 2. Coba restore dari git
r(rs, 'cd ~/Penetas-Telur && git stash 2>/dev/null; git checkout -- dist/ 2>/dev/null && echo "✓ Restored from git" || echo "No git restore possible"', '4. Git restore')

# 3. Cek backup
r(rs, 'ls ~/Penetas-Telur/dist_backup/ 2>/dev/null || echo "No backup"', '5. Backup dist/')
r(rs, 'find ~/Penetas-Telur -name "*.html" | grep -v "node_modules" | head -15', '6. HTML files di project')

# 4. Cek isi dist/ setelah restore
r(rs, 'ls -la ~/Penetas-Telur/dist/', '7. dist/ setelah restore')
r(rs, 'head -5 ~/Penetas-Telur/dist/index.html 2>/dev/null || echo "No index.html"', '8. index.html preview')

rs.close()
