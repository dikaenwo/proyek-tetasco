"""fix2.py — Upload fixed configs dan restart dengan benar"""
import paramiko, sys, time, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)
PROJ = '/home/telur/tetasco-connect'

def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, get_pty=True)
    o.channel.settimeout(180)
    buf = []
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            d = chunk.decode('utf-8', 'replace')
            buf.append(d)
            sys.stdout.write(d); sys.stdout.flush()
        except: break
    o.channel.recv_exit_status()
    return ''.join(buf)

# ── Upload fixed mosquitto.conf (tanpa pid_file) ──────────────────────────────
MOSQ_CONF = """persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout

# Listener TCP port 1883
listener 1883
protocol mqtt

# Listener WebSocket port 9001 (untuk Cloudflare Tunnel)
listener 9001
protocol websockets

# Autentikasi
allow_anonymous false
password_file /mosquitto/config/passwd
acl_file /mosquitto/config/acl.conf

# Tuning
max_keepalive 120
max_inflight_messages 20
max_queued_messages 100
log_type error
log_type warning
log_type notice
log_type information
log_timestamp true
"""

# ── Upload fixed docker-compose.yml (healthcheck disederhanakan) ──────────────
DC_YML = """services:

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
      test: ["CMD-SHELL", "nc -z localhost 1883 || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 6
      start_period: 15s

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
    depends_on:
      database:
        condition: service_healthy
      mosquitto:
        condition: service_healthy
    networks:
      - tetasco-net

  database:
    image: postgres:15-alpine
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
      start_period: 10s

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

networks:
  tetasco-net:
    driver: bridge
"""

sftp = c.open_sftp()
sftp.putfo(io.BytesIO(MOSQ_CONF.encode()), f'{PROJ}/mosquitto/config/mosquitto.conf')
print('[OK] mosquitto.conf (fixed: no pid_file) uploaded', flush=True)
sftp.putfo(io.BytesIO(DC_YML.encode()), f'{PROJ}/docker-compose.yml')
print('[OK] docker-compose.yml (fixed: simple healthcheck) uploaded', flush=True)
sftp.close()

# Stop semua lalu restart fresh
r(f'cd {PROJ} && docker compose down 2>&1', 'Stop all')
time.sleep(2)
r(f'cd {PROJ} && docker compose --env-file .env up -d 2>&1', 'Start all services')

# Tunggu 15 detik
print('\n[Waiting 15s for services to stabilize...]', flush=True)
time.sleep(15)

r('docker ps', 'Container status')
r('docker logs tetasco-mosquitto --tail=10 2>&1', 'Mosquitto logs')
r('curl -s http://localhost/api/health 2>/dev/null || echo "not ready"', 'API health')

# Test MQTT jika mosquitto running
r('docker exec tetasco-mosquitto mosquitto_pub '
  '-h localhost -p 1883 '
  '-u server -P "srv-7043imRswI0lSdZ3" '
  '-t "tetasco/test" -m "OK!" 2>&1 && echo "MQTT PUBLISH OK!"', 'MQTT test')

r('docker logs tetasco-backend --tail=15 2>&1', 'Backend logs')
c.close()
print('\nDone!', flush=True)
