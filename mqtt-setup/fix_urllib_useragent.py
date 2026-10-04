"""fix_urllib_useragent.py — Fix urllib 403 dengan tambah User-Agent header"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(c, cmd, lbl='', timeout=20):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace')
    err = e.read().decode('utf-8','replace')
    sys.stdout.write(out or err); sys.stdout.flush()
    return out

# Baca app.py
i, o, e = rs.exec_command('cat ~/Penetas-Telur/backend/app.py')
content = o.read().decode('utf-8','replace')
print(f'[INFO] app.py: {len(content)} chars', flush=True)

# Ganti polling code yang pakai urllib tanpa header → dengan Request + User-Agent
OLD_URLLIB = '''    # 2. Poll server pusat (https://tetasco.my.id)
    try:
        import urllib.request as _ur, json as _j, ssl as _ssl
        tid = int(os.getenv('TETASCO_ID', 1))
        ctx = _ssl.create_default_context()
        with _ur.urlopen(
            f'https://tetasco.my.id/api/tetasco/{tid}/is-claimed',
            context=ctx, timeout=5
        ) as resp:
            d = _j.loads(resp.read().decode())
            if d.get('claimed'):
                # Simpan lokal supaya check berikutnya lebih cepat
                _CLAIMED_FILE.write_text(_json.dumps({
                    'farm_name': d.get('farm_name', f'Lemari #{tid}')
                }))
                return jsonify({'claimed': True, 'farm_name': d.get('farm_name', f'Lemari #{tid}')})
    except Exception as ex:
        logger.debug(f'[claim-status] Poll server error: {ex}')'''

NEW_URLLIB = '''    # 2. Poll server pusat (https://tetasco.my.id)
    try:
        import urllib.request as _ur, json as _j, ssl as _ssl
        tid = int(os.getenv('TETASCO_ID', 1))
        ctx = _ssl.create_default_context()
        # Tambah User-Agent agar tidak diblokir server
        req_obj = _ur.Request(
            f'https://tetasco.my.id/api/tetasco/{tid}/is-claimed',
            headers={
                'User-Agent': 'TetascoRaspi/1.0',
                'Accept': 'application/json',
            }
        )
        with _ur.urlopen(req_obj, context=ctx, timeout=8) as resp:
            d = _j.loads(resp.read().decode())
            if d.get('claimed'):
                _CLAIMED_FILE.write_text(_json.dumps({
                    'farm_name': d.get('farm_name', f'Lemari #{tid}')
                }))
                return jsonify({'claimed': True, 'farm_name': d.get('farm_name', f'Lemari #{tid}')})
    except Exception as ex:
        logger.warning(f'[claim-status] Poll server error: {type(ex).__name__} {ex}')'''

if OLD_URLLIB in content:
    content = content.replace(OLD_URLLIB, NEW_URLLIB, 1)
    sftp = rs.open_sftp()
    sftp.putfo(io.BytesIO(content.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
    sftp.close()
    print('[OK] urllib User-Agent diperbaiki', flush=True)
else:
    print('[WARN] Pattern tidak ditemukan, cek manual', flush=True)
    r(rs, 'grep -n "urlopen\\|User-Agent\\|urllib" ~/Penetas-Telur/backend/app.py | head -10', 'Cek urllib usage')

# Restart
r(rs, 'pkill -f "backend/app.py" 2>/dev/null; echo killed', 'Kill backend')
time.sleep(2)
rs.exec_command('cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &')
print('[OK] Backend restarted', flush=True)
time.sleep(4)

# Quick test urllib dengan user-agent
r(rs, '''python3 -c "
import urllib.request, ssl, json
ctx = ssl.create_default_context()
req = urllib.request.Request(
    'https://tetasco.my.id/api/tetasco/1/is-claimed',
    headers={'User-Agent':'TetascoRaspi/1.0','Accept':'application/json'}
)
try:
    with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
        print('OK:', json.loads(r.read().decode()))
except Exception as e:
    print('ERROR:', type(e).__name__, str(e))
"''', '1. Test urllib + User-Agent')

# Test claim lalu poll
import requests as req
SERVER = 'https://tetasco.my.id'
print('\n[2. Claim di server...]', flush=True)
tok = req.get(f'{SERVER}/api/tetasco/1/claim-token', timeout=10).json()['token']
res = req.post(f'{SERVER}/api/claim', json={
    'tetascoId': 1, 'claimToken': tok,
    'appId': 'test-ua-fix-001', 'farmName': 'Test UA Fix'
}, timeout=10).json()
print(f'  Claim result: {res}', flush=True)

time.sleep(2)
r(rs, 'curl -s http://localhost:5001/api/claim-status', '3. Raspi claim-status (setelah klaim di server)')

# Check backend log for the warning
time.sleep(2)
r(rs, 'grep -E "claim-status|Poll server|Raspi" /tmp/tetasco_backend.log | tail -10', '4. Backend log')

# Cleanup
rs.exec_command('rm -f ~/.tetasco_claimed')
req.delete(f'{SERVER}/api/claim/1?appId=test-ua-fix-001', timeout=5)
print('\n[OK] Cleanup', flush=True)

rs.close()
print('\n✅ Done!', flush=True)
