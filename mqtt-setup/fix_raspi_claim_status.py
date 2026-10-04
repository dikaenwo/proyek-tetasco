"""fix_raspi_claim_status.py — Fix claim-status endpoint agar polling server pusat"""
import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(c, cmd, lbl='', timeout=20):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace')
    sys.stdout.write(out); sys.stdout.flush()
    return out

# Baca app.py dari Raspi
i, o, e = rs.exec_command('cat ~/Penetas-Telur/backend/app.py')
content = o.read().decode('utf-8', 'replace')
print(f'[INFO] app.py: {len(content)} chars', flush=True)

# Lihat fungsi claim-status yang ada sekarang
r(rs, 'grep -n "claim.status\\|claim_status\\|poll\\|is-claimed" ~/Penetas-Telur/backend/app.py | head -20',
  '1. Current claim-status code')

# Temukan dan ganti fungsi claim-status
OLD_PATTERN = "@app.route('/api/claim-status')\ndef api_claim_status():"

if OLD_PATTERN not in content:
    # Cari pattern yang mirip
    print('[WARN] Pattern tidak ditemukan, cek manual...', flush=True)
    r(rs, "grep -n 'claim' ~/Penetas-Telur/backend/app.py | head -20", 'Claim references')
else:
    # Ambil blok fungsi lama
    start = content.find(OLD_PATTERN)
    # Cari awal fungsi berikutnya
    next_func = content.find('\n@app.route', start + 50)
    if next_func < 0:
        next_func = content.find('\nif __name__', start + 50)
    
    old_func = content[start:next_func]
    print(f'[INFO] Fungsi lama ditemukan ({len(old_func)} chars):', flush=True)
    print(old_func[:200], flush=True)
    
    # Fungsi baru dengan polling ke server pusat
    new_func = '''@app.route('/api/claim-status')
def api_claim_status():
    """Cek apakah lemari sudah diklaim: cek lokal DULU, lalu poll server pusat."""
    # 1. Cek flag lokal (tercepat)
    if _CLAIMED_FILE.exists():
        try:
            data = _json.loads(_CLAIMED_FILE.read_text())
            return jsonify({'claimed': True, 'farm_name': data.get('farm_name', 'Lemari Saya')})
        except:
            return jsonify({'claimed': True, 'farm_name': 'Lemari Saya'})

    # 2. Poll server pusat (https://tetasco.my.id)
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
        logger.debug(f'[claim-status] Poll server error: {ex}')

    return jsonify({'claimed': False})
'''
    
    content = content[:start] + new_func + content[next_func:]
    
    sftp = rs.open_sftp()
    sftp.putfo(io.BytesIO(content.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
    sftp.close()
    print('[OK] claim-status updated (polling dengan urllib bawaan Python)', flush=True)

# Restart backend
import time
r(rs, 'pkill -f "backend/app.py" 2>/dev/null; echo killed', '2. Kill old backend')
time.sleep(2)
rs.exec_command('cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &')
print('[OK] Backend restarted', flush=True)
time.sleep(4)

# Test
r(rs, 'curl -s http://localhost:5001/api/claim-status', '3. Test (belum claimed)')

# Simulasi claim dari server
import requests as req
SERVER = 'https://tetasco.my.id'
tok = req.get(f'{SERVER}/api/tetasco/1/claim-token', timeout=10).json()['token']
req.post(f'{SERVER}/api/claim', json={
    'tetascoId': 1, 'claimToken': tok,
    'appId': 'test-fix-001', 'farmName': 'Kandang Fix Test'
}, timeout=10)
print('[OK] Claimed di server pusat', flush=True)
time.sleep(3)

r(rs, 'curl -s http://localhost:5001/api/claim-status', '4. Test (setelah claimed di server)')
r(rs, 'cat ~/.tetasco_claimed 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d)" 2>/dev/null || echo "file belum ada"',
  '5. Flag file lokal')

# Cleanup
rs.exec_command('rm -f ~/.tetasco_claimed')
req.delete(f'{SERVER}/api/claim/1?appId=test-fix-001', timeout=5)
print('\n[OK] Cleanup done', flush=True)

rs.close()
print('\n✅ Done! Raspi sekarang polling server pusat untuk detect klaim.', flush=True)
