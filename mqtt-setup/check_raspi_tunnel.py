import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(cmd, lbl='', timeout=15):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rs.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)')
    return out

# Cek tunnel
r('ps aux | grep -E "cloudflare|ngrok|frp|tunnel|bore|localtunnel" | grep -v grep | head -10', '1. Running tunnel procs')
r('which cloudflared ngrok frpc 2>/dev/null || echo "not in PATH"', '2. Tunnel binaries')
r('systemctl list-units --state=running 2>/dev/null | grep -E "cloudflare|ngrok|frp|tunnel" | head -10 || echo "(none)"', '3. Systemd services')
r('cat /etc/systemd/system/cloudflared.service 2>/dev/null || echo "no cloudflared service"', '4. Cloudflared service')
r('cloudflared tunnel list 2>/dev/null || echo "cloudflared not available"', '5. Cloudflared tunnels')
r('cat ~/.cloudflared/config.yml 2>/dev/null || echo "no config"', '6. Cloudflared config')
r('curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); [print(t[\'public_url\']) for t in d[\'tunnels\']]" 2>/dev/null || echo "no ngrok api"', '7. Ngrok public URLs')
r('ls ~/Penetas-Telur/scripts/ 2>/dev/null || ls ~/scripts/ 2>/dev/null | head -20', '8. Scripts dir')
r('cat ~/Penetas-Telur/scripts/start_tetasco.sh 2>/dev/null || echo "no start script"', '9. Start script')

rs.close()
