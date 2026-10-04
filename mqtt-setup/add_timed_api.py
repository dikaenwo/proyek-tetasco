import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=15):
    if lbl: print(f'\n=== {lbl} ===')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Baca app.py
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app_py = o.read().decode('utf-8', 'replace')

# Cek endpoint hidrolik yang ada
ras("grep -n 'hydraulic\|motor\|oscillat' ~/Penetas-Telur/backend/app.py | head -20", 'Existing hydraulic endpoints')

# Cari anchor untuk menyisipkan endpoint baru
anchor_candidates = [
    "@app.route('/api/hydraulic/stop'",
    "@app.route('/api/hydraulic/status'",
    "@app.route('/api/hydraulic/up'",
]
anchor = None
for c in anchor_candidates:
    if c in app_py:
        anchor = c
        print(f'[OK] Found anchor: {c}')
        break

if not anchor:
    print('[ERR] Tidak ada anchor ditemukan!')
    rp.close()
    exit(1)

# Endpoint baru: POST /api/hydraulic/timed_oscillation
NEW_ENDPOINT = '''@app.route('/api/hydraulic/timed_oscillation', methods=['POST'])
def api_hydraulic_timed_oscillation():
    """
    POST /api/hydraulic/timed_oscillation
    Jalankan urutan bolak-balik telur berbasis WAKTU (tanpa limit switch).

    Body JSON (semua opsional):
      {
        "n_cycles"        : 3,    // jumlah siklus atas↔bawah (default 3)
        "t_center_to_edge": 4.0,  // durasi tengah→atas dan atas→tengah (detik)
        "t_full"          : 9.0   // durasi 1 gerakan atas↔bawah (detik)
      }

    Sequence:
      tengah→atas (4s) → [atas↔bawah (9s)] × 3 → atas→tengah (4s) → stop auto
    """
    try:
        data = request.get_json(silent=True) or {}
        n_cycles         = int(data.get('n_cycles', 3))
        t_center_to_edge = float(data.get('t_center_to_edge', 4.0))
        t_full           = float(data.get('t_full', 9.0))

        # Validasi
        if not (1 <= n_cycles <= 20):
            return jsonify({'error': 'n_cycles harus antara 1 dan 20'}), 400
        if not (1.0 <= t_center_to_edge <= 60.0):
            return jsonify({'error': 't_center_to_edge harus antara 1-60 detik'}), 400
        if not (1.0 <= t_full <= 60.0):
            return jsonify({'error': 't_full harus antara 1-60 detik'}), 400

        status = hydraulic_controller.start_timed_oscillation(
            n_cycles=n_cycles,
            t_center_to_edge=t_center_to_edge,
            t_full=t_full,
        )
        total_duration = t_center_to_edge + (n_cycles * 2 * t_full) + t_center_to_edge
        return jsonify({
            **status,
            'mode'          : 'timed_sequence',
            'n_cycles'      : n_cycles,
            't_center_to_edge': t_center_to_edge,
            't_full'        : t_full,
            'total_duration_sec': total_duration,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


'''

app_py = app_py.replace(anchor, NEW_ENDPOINT + anchor, 1)
print('[OK] Endpoint /api/hydraulic/timed_oscillation ditambah')

# Tulis balik
sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(app_py.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/app.py && echo SYNTAX_OK', 'Syntax check app.py')

# Restart
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
transport = rp.get_transport()
chan = transport.open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1)
chan.close()
print('[OK] Raspi restart')
time.sleep(8)

# Test endpoint
ras('curl -s http://localhost:5001/api/hydraulic/status', 'Hydraulic status')
ras('curl -s -X POST http://localhost:5001/api/hydraulic/timed_oscillation -H "Content-Type: application/json" -d "{}" | python3 -m json.tool', 'Test timed_oscillation endpoint')

rp.close()
print('\n✅ Endpoint timed_oscillation selesai!')
