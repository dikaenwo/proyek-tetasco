import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(cmd, lbl='', timeout=30):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i,o,e = sv.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)'); sys.stdout.flush()
    return out

# ── Tulis docker-compose.yml yang bersih ─────────────────────────────────────
CLEAN_COMPOSE = '''services:

  # ─── Mosquitto MQTT Broker ──────────────────────────────────────────────────
  mosquitto:
    image: eclipse-mosquitto:2
    container_name: tetasco-mosquitto
    restart: unless-stopped
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - ./mosquitto/config:/mosquitto/config:ro
      - mosquitto_data:/mosquitto/data
      - mosquitto_log:/mosquitto/log
    networks:
      - tetasco-net
    healthcheck:
      test: ["CMD-SHELL", "mosquitto_pub -h localhost -p 1883 -u server -P \\"$$MQTT_SERVER_PASS\\" -t health -m ping --quiet 2>/dev/null || nc -z localhost 1883 || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 10s

  # ─── FastAPI Backend ────────────────────────────────────────────────────────
  backend:
    build: ./backend
    container_name: tetasco-backend
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://telur:${DB_PASS}@database:5432/tetasco
      MQTT_BROKER: mosquitto
      MQTT_PORT: 1883
      MQTT_USER: server
      MQTT_PASS: ${MQTT_SERVER_PASS}
    ports:
      - "8000:8000"
    volumes:
      - tetasco-claims:/app/data
    depends_on:
      database:
        condition: service_healthy
      mosquitto:
        condition: service_healthy
    networks:
      - tetasco-net

  # ─── PostgreSQL Database ────────────────────────────────────────────────────
  database:
    image: postgres:16-alpine
    container_name: tetasco-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: telur
      POSTGRES_PASSWORD: ${DB_PASS}
      POSTGRES_DB: tetasco
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - tetasco-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U telur -d tetasco"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─── Nginx Reverse Proxy ────────────────────────────────────────────────────
  nginx:
    image: nginx:alpine
    container_name: tetasco-nginx
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend:/usr/share/nginx/html:ro
    depends_on:
      - backend
    networks:
      - tetasco-net

volumes:
  postgres_data:
  mosquitto_data:
  mosquitto_log:
  tetasco-claims:

networks:
  tetasco-net:
    driver: bridge
'''

sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(CLEAN_COMPOSE.encode()), '/home/telur/tetasco-connect/docker-compose.yml')
sftp.close()
print('[OK] docker-compose.yml ditulis ulang bersih')

# Validate
out = r('cd ~/tetasco-connect && docker compose config --quiet 2>&1 | head -5 || echo "VALID"', '1. Validate YAML')
if 'error' in out.lower():
    print('ERROR! Cek YAML'); sys.exit(1)

# ── SEMENTARA: patch langsung main.py di container yang jalan ─────────────────
# Ini agar share-token langsung bekerja tanpa rebuild dulu
print('\n[Patch langsung di container]')
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')
print(f'main.py di container: {len(main_py)} chars')

# Cek apakah sudah ada soft validation
if 'has_camera' in main_py:
    print('[INFO] Soft validation sudah ada di container')
elif 'has_sensor  = bool(device_sensor_cache.get(did))' in main_py:
    # Tambah camera check
    main_py = main_py.replace(
        'has_sensor  = bool(device_sensor_cache.get(did))\n    device_active = in_claims or has_hb or has_sensor',
        'has_sensor  = bool(device_sensor_cache.get(did))\n    has_camera  = str(tetasco_id) in _cam_frames\n    device_active = in_claims or has_hb or has_sensor or has_camera',
        1
    )
    # Upload ke container
    tmp_path = '/tmp/main_patched.py'
    sftp = sv.open_sftp()
    sftp.putfo(io.BytesIO(main_py.encode()), tmp_path)
    sftp.close()
    r(f'docker cp {tmp_path} tetasco-backend:/app/main.py && echo "copied"', '2. Copy patched main.py ke container')
    r('docker exec tetasco-backend kill -HUP 1 2>/dev/null || docker restart tetasco-backend', '3. Reload uvicorn', timeout=20)
    time.sleep(8)
    print('[OK] Container di-patch langsung')
elif 'device_active = in_claims or has_hb or has_sensor' in main_py:
    main_py = main_py.replace(
        'device_active = in_claims or has_hb or has_sensor',
        'has_camera  = str(tetasco_id) in _cam_frames\n    device_active = in_claims or has_hb or has_sensor or has_camera',
        1
    )
    sftp = sv.open_sftp()
    sftp.putfo(io.BytesIO(main_py.encode()), '/tmp/main_patched.py')
    sftp.close()
    r('docker cp /tmp/main_patched.py tetasco-backend:/app/main.py && echo "copied"', '2. Copy patched')
    r('docker restart tetasco-backend 2>&1 | tail -2', '3. Restart container', timeout=20)
    time.sleep(10)
else:
    print('[WARN] Pattern tidak ditemukan, rebuild manual perlu')

# Build dengan compose baru
r('curl -s http://localhost:8000/api/health', '4. Health check')
r('curl -s -X POST http://localhost:8000/api/tetasco/1/share-token -H "Content-Type: application/json" -d \'{"appId":"test"}\'',
  '5. Test share token')

# Rebuild dengan compose yang sudah bersih
r('cd ~/tetasco-connect && docker compose build backend 2>&1 | tail -5', '6. Build backend (clean compose)', timeout=120)
r('cd ~/tetasco-connect && docker compose up -d 2>&1 | tail -6', '7. Docker up', timeout=30)
time.sleep(12)
r('curl -s http://localhost:8000/api/health', '8. Final health check')
r('curl -s -X POST http://localhost:8000/api/tetasco/1/share-token -H "Content-Type: application/json" -d \'{"appId":"test"}\'',
  '9. Final test share token')

sv.close()
print('\n✅ Done!')
