import paramiko, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Cek apakah tetasco.my.id bisa di-SSH (coba beberapa port)
import socket

def try_connect(host, port, timeout=5):
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except:
        return False

print('[Cek port SSH tetasco.my.id]')
for port in [22, 2222, 2200, 22022]:
    ok = try_connect('tetasco.my.id', port)
    print(f'  Port {port}: {"OPEN ✅" if ok else "closed"}')

# Cek endpoint yang ada di cloud server
import urllib.request, json
def get(url, lbl=''):
    if lbl: print(f'\n[{lbl}]')
    try:
        req = urllib.request.urlopen(url, timeout=8)
        data = req.read().decode()
        print(data[:500])
        return data
    except Exception as e:
        print(f'Error: {e}')
        return ''

get('https://tetasco.my.id/', 'GET /')
get('https://tetasco.my.id/api/', 'GET /api/')
get('https://tetasco.my.id/api/tetasco/1/is-claimed', 'GET /api/tetasco/1/is-claimed')
get('https://tetasco.my.id/health', 'GET /health')
get('https://tetasco.my.id/api/health', 'GET /api/health')
