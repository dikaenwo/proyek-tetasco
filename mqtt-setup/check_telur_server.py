import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# SSH ke Raspi dulu, lalu dari Raspi SSH ke server "telur"
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

# Resolve hostname "telur"
r('getent hosts telur 2>/dev/null || host telur 2>/dev/null || nslookup telur 2>/dev/null | head -5 || echo "tidak bisa resolve"', '1. Resolve hostname telur')
r('cat /etc/hosts | grep -v "^#" | grep -v "^$"', '2. /etc/hosts')

# Cek apakah server tetasco.my.id accessible dari Raspi
r('curl -s -o /dev/null -w "%{http_code}" https://tetasco.my.id/api/tetasco/1/is-claimed', '3. tetasco.my.id dari Raspi')

# Coba SSH ke tetasco.my.id dengan berbagai user
r('nc -z -w3 tetasco.my.id 22 2>&1 && echo "port 22 open" || echo "port 22 closed"', '4. SSH port check dari Raspi')
r('nc -z -w3 telur 22 2>&1 && echo "port 22 open" || echo "closed/unresolved"', '5. SSH ke telur dari Raspi')

# Coba curl ke server "telur" dari Raspi
r('curl -s -I http://telur/ 2>/dev/null | head -5 || echo "not reachable"', '6. HTTP ke telur dari Raspi')
r('curl -s -I http://telur:8000/ 2>/dev/null | head -5 || echo "not reachable"', '7. HTTP:8000 ke telur')
r('curl -s -I http://telur:3000/ 2>/dev/null | head -5 || echo "not reachable"', '8. HTTP:3000 ke telur')

# Info jaringan Raspi
r('ip route | head -5', '9. IP route')

rs.close()
