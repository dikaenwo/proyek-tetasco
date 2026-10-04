"""deploy_pairing_page.py — Upload pairing.html + patch backend/app.py di Raspi"""
import paramiko, sys, io, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

RASPI_HOST = '192.168.1.27'
RASPI_USER = 'tetasco1'
RASPI_PASS = 'saumata1192'

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect(RASPI_HOST, 22, RASPI_USER, RASPI_PASS, timeout=15)

def r(c, cmd, lbl='', timeout=30):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace')
    err = e.read().decode('utf-8','replace')
    sys.stdout.write(out or err); sys.stdout.flush()
    return out

def sudo_r(c, cmd, lbl='', timeout=30):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(f'echo "{RASPI_PASS}" | sudo -S {cmd} 2>&1', timeout=timeout)
    out = o.read().decode('utf-8','replace')
    sys.stdout.write(out); sys.stdout.flush()
    return out

# ── 1. Upload pairing.html ────────────────────────────────────────────────────
with open('raspberry_pi/pairing.html', 'rb') as f:
    sftp = rs.open_sftp()
    sftp.putfo(f, '/home/tetasco1/Penetas-Telur/pairing.html')
    sftp.close()
print('[OK] pairing.html uploaded', flush=True)

# ── 2. Baca backend/app.py ────────────────────────────────────────────────────
i, o, e = rs.exec_command('cat ~/Penetas-Telur/backend/app.py')
content = o.read().decode('utf-8', 'replace')
print(f'[INFO] app.py: {len(content)} chars', flush=True)

# ── 3. Tambah endpoints baru ke app.py ──────────────────────────────────────
CLAIM_STATUS_CODE = '''

# ═══════════════════════════════════════════════════════════════
#  PAIRING — Welcome screen & claim status endpoints
# ═══════════════════════════════════════════════════════════════
import hmac as _hmac, hashlib as _hsha, json as _json, socket as _sock
from pathlib import Path as _Path

_CLAIM_KEY    = 'tetasco-secret-2026'
_CLAIMED_FILE = _Path('/home/tetasco1/.tetasco_claimed')

def _get_local_ip():
    try:
        s = _sock.socket(_sock.AF_INET, _sock.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except: return '127.0.0.1'


@app.route('/pair')
def pairing_page():
    """Serve halaman welcome/pairing di HDMI."""
    from flask import send_from_directory
    return send_from_directory('/home/tetasco1/Penetas-Telur', 'pairing.html')


@app.route('/api/pairing-info')
def api_pairing_info():
    """Info device untuk welcome screen."""
    cfg = {}
    cfg_file = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    if os.path.exists(cfg_file):
        try: cfg = _json.loads(open(cfg_file).read())
        except: pass

    tetasco_id = int(os.getenv('TETASCO_ID', cfg.get('tetasco_id', 1)))
    temp = humidity = None
    try:
        from sensor_manager import SensorManager as _SM
        _sm = _SM(); data = _sm.read()
        if data: temp, humidity = data.get('temperature'), data.get('humidity')
    except: pass

    return jsonify({
        'tetasco_id': tetasco_id,
        'ip':         _get_local_ip(),
        'online':     True,
        'temperature': temp,
        'humidity':    humidity,
        'claimed':     _CLAIMED_FILE.exists(),
    })


@app.route('/api/claim-status')
def api_claim_status():
    """Cek apakah lemari sudah diklaim."""
    if _CLAIMED_FILE.exists():
        try:
            data = _json.loads(_CLAIMED_FILE.read_text())
            return jsonify({'claimed': True, 'farm_name': data.get('farm_name', 'Lemari Saya')})
        except:
            return jsonify({'claimed': True, 'farm_name': 'Lemari Saya'})
    return jsonify({'claimed': False})


@app.route('/api/mark-claimed', methods=['POST'])
def api_mark_claimed():
    """
    Dipanggil setelah user berhasil claim di HP.
    Simpan flag claimed ke disk → pairing page auto-redirect.
    """
    body = request.get_json(silent=True) or {}
    data = {
        'farm_name':  body.get('farmName', 'Lemari Saya'),
        'app_id':     body.get('appId', ''),
        'claimed_at': int(__import__('time').time()),
    }
    _CLAIMED_FILE.write_text(_json.dumps(data))
    logger.info(f"[Pairing] Diklaim: {data['farm_name']} by {data['app_id'][:8]}...")
    return jsonify({'ok': True})

'''

if '/api/pairing-info' in content:
    print('[SKIP] Pairing endpoints sudah ada', flush=True)
else:
    # Tambah sebelum serve_frontend atau di akhir routes
    if 'def serve_frontend' in content:
        content = content.replace('# Static Web Server', CLAIM_STATUS_CODE + '\n# Static Web Server', 1)
    elif 'if __name__' in content:
        content = content.replace('if __name__', CLAIM_STATUS_CODE + '\nif __name__', 1)
    else:
        content += CLAIM_STATUS_CODE

    # Pastikan flask Request diimport
    if 'from flask import' in content and 'request' not in content.lower().split('from flask import')[1].split('\n')[0]:
        content = content.replace('from flask import', 'from flask import request,', 1)

    sftp = rs.open_sftp()
    sftp.putfo(io.BytesIO(content.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
    sftp.close()
    print(f'[OK] app.py patched ({len(content)} chars)', flush=True)

# ── 4. Update Chromium start URL ke /pair jika belum claimed ─────────────────
r(rs, 'cat /etc/chromium/chromium 2>/dev/null || cat ~/.config/chromium/Default/Preferences 2>/dev/null | head -5 || echo "Cek startup"', 
  '4. Chromium config')

# Cek autostart
r(rs, 'cat ~/.config/autostart/*.desktop 2>/dev/null || ls ~/.config/autostart/ 2>/dev/null || echo "no autostart"',
  '5. Autostart config')

# Lihat service yang nyalain Chromium
r(rs, 'systemctl --user list-units | grep chromium; cat /etc/systemd/system/*chromium* 2>/dev/null | head -20; cat ~/.config/autostart/chromium*.desktop 2>/dev/null',
  '6. Chromium service')

# ── 5. Restart backend ────────────────────────────────────────────────────────
r(rs, 'pkill -f "python.*app.py" 2>/dev/null; sleep 2; nohup python3 ~/Penetas-Telur/backend/app.py > /tmp/raspi_app.log 2>&1 &; sleep 3; curl -s http://localhost:5001/api/pairing-info | python3 -m json.tool',
  '7. Restart backend + test pairing-info')

# Cek /pair endpoint
r(rs, 'curl -si http://localhost:5001/pair | head -5', '8. Test /pair endpoint')

rs.close()
print('\n✅ Done!', flush=True)
