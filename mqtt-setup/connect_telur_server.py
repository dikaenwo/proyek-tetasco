import paramiko, sys, socket
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Resolve "telur" hostname dari PC lokal
print('[Resolve hostname "telur"]')
try:
    ip = socket.gethostbyname('telur')
    print(f'IP: {ip}')
except Exception as e:
    print(f'Gagal resolve: {e}')
    ip = 'telur'

# Coba connect
print(f'\n[Connect SSH ke telur@{ip}]')
sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    sv.connect(ip, 22, 'telur', 'telur', timeout=10)
    print('✅ Connected!')

    def r(cmd, lbl='', timeout=15):
        if lbl: print(f'\n[{lbl}]')
        i,o,e = sv.exec_command(cmd, timeout=timeout)
        out = o.read().decode('utf-8','replace').strip()
        err = e.read().decode('utf-8','replace').strip()
        print(out or err or '(kosong)')
        return out

    r('whoami && hostname && uname -a', 'Server info')
    r('ls ~/', 'Home dir')
    r('ls ~/app/ 2>/dev/null || ls ~/backend/ 2>/dev/null || ls /var/www/ 2>/dev/null | head -10', 'App dir')
    r('ps aux | grep -E "python|node|gunicorn|uvicorn|nginx|flask" | grep -v grep | head -10', 'Running services')
    r('netstat -tlnp 2>/dev/null | grep LISTEN | head -10 || ss -tlnp | head -10', 'Listening ports')
    r('cat /etc/nginx/sites-enabled/* 2>/dev/null | grep -E "server_name|location|proxy_pass" | head -20 || echo "no nginx config found"', 'Nginx config')

    sv.close()
except Exception as e:
    print(f'❌ Gagal: {e}')
    print('\nCoba port 2222...')
    try:
        sv2 = paramiko.SSHClient()
        sv2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sv2.connect(ip, 2222, 'telur', 'telur', timeout=10)
        print('✅ Connected on port 2222!')
        i,o,e = sv2.exec_command('whoami && hostname')
        print(o.read().decode())
        sv2.close()
    except Exception as e2:
        print(f'❌ Port 2222 juga gagal: {e2}')
