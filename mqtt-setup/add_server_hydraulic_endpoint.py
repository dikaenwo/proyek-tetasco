import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=15):
    if lbl: print(f'\n=== {lbl} ===')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Baca main.py server
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')
print(f'Server main.py size: {len(main_py)} chars')

# Cari anchor untuk menyisipkan endpoint baru (setelah _forward_to_raspi def atau sebelum control_device)
ANCHOR = '@app.get("/api/tetasco/{tetasco_id}/status")'
if ANCHOR not in main_py:
    ANCHOR = '@app.get("/api/tetasco/{tetasco_id}/sensor")'
if ANCHOR in main_py:
    print(f'[OK] Anchor: {ANCHOR}')
else:
    print('[ERR] Anchor tidak ditemukan!')
    # show available routes
    import re
    routes = re.findall(r'@app\.\w+\("(/api[^"]+)"', main_py)
    print('Available routes:', routes[:10])

# Endpoint server baru: POST /api/tetasco/{id}/hydraulic/timed_oscillation
NEW_ENDPOINT = '''@app.post("/api/tetasco/{tetasco_id}/hydraulic/timed_oscillation")
async def hydraulic_timed_oscillation(tetasco_id: int, request: _Req):
    """
    POST /api/tetasco/{id}/hydraulic/timed_oscillation
    Forward ke Raspi Flask: POST /api/hydraulic/timed_oscillation
    Jalankan urutan bolak-balik telur berbasis waktu (tanpa limit switch).

    Body JSON (semua opsional, default sesuai user requirement):
      { "n_cycles": 3, "t_center_to_edge": 4.0, "t_full": 9.0 }
    """
    import httpx as _hx, json as _json_h
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    # Validasi parameter
    n_cycles         = int(body.get("n_cycles", 3))
    t_center_to_edge = float(body.get("t_center_to_edge", 4.0))
    t_full           = float(body.get("t_full", 9.0))

    # Resolve Raspi IP
    did = f"lemari-{tetasco_id}"
    raspi_ip = device_heartbeat_cache.get(did, {}).get("ip") or RASPI_LOCAL_IPS.get(tetasco_id)
    if not raspi_ip:
        raise _HTTPEx(status_code=503, detail="Raspi tidak ditemukan atau tidak online")

    try:
        async with _hx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"http://{raspi_ip}:5001/api/hydraulic/timed_oscillation",
                json={"n_cycles": n_cycles, "t_center_to_edge": t_center_to_edge, "t_full": t_full},
            )
        result = res.json()
        logger.info(f"[Hydraulic] timed_oscillation → Raspi {raspi_ip}: {result.get('state')}")
        return {
            **result,
            "forwarded_to": raspi_ip,
        }
    except Exception as e:
        logger.warning(f"[Hydraulic] timed_oscillation forward error: {e}")
        raise _HTTPEx(status_code=502, detail=f"Gagal forward ke Raspi: {e}")


@app.post("/api/tetasco/{tetasco_id}/hydraulic/stop")
async def hydraulic_stop(tetasco_id: int):
    """Hentikan semua gerakan hidrolik di Raspi."""
    import httpx as _hx
    did = f"lemari-{tetasco_id}"
    raspi_ip = device_heartbeat_cache.get(did, {}).get("ip") or RASPI_LOCAL_IPS.get(tetasco_id)
    if not raspi_ip:
        raise _HTTPEx(status_code=503, detail="Raspi tidak online")
    try:
        async with _hx.AsyncClient(timeout=5.0) as client:
            res = await client.post(f"http://{raspi_ip}:5001/api/hydraulic/command",
                                    json={"action": "stop"})
        return res.json()
    except Exception as e:
        raise _HTTPEx(status_code=502, detail=str(e))


'''

if ANCHOR in main_py:
    main_py = main_py.replace(ANCHOR, NEW_ENDPOINT + ANCHOR, 1)
    print('[OK] Endpoint hydraulic/timed_oscillation + stop ditambah')

# Cek apakah _Req dan _HTTPEx sudah di-import
if '_Req' not in main_py:
    print('[INFO] _Req belum di-import, cek import...')
    srv('docker exec tetasco-backend grep -n "Request\|HTTPException\|_Req\|_HTTPEx" /app/main.py | head -10', 'Import check')

# Deploy
sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.close()

# Copy ke container dan restart
srv('docker cp /home/telur/tetasco-connect/backend/main.py tetasco-backend:/app/main.py && echo ok', 'Deploy')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart server', t=20)
time.sleep(12)
srv('curl -s http://localhost:8000/api/health', 'Server health')

# Test endpoint
srv('curl -s -X POST http://localhost:8000/api/tetasco/1/hydraulic/stop | head -c 200', 'Test stop')
print('\n[TEST] timed_oscillation:')
srv('curl -s -X POST http://localhost:8000/api/tetasco/1/hydraulic/timed_oscillation -H "Content-Type: application/json" -d \'{"n_cycles":1,"t_center_to_edge":2,"t_full":3}\' | head -c 300', 'Test timed_oscillation (quick: 1 cycle 2+3+3+2=10s)')

sv.close()
print('\n✅ Server endpoint selesai!')
