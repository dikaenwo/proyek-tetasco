"""server_setup.py v2 — Setup Tetasco MQTT via Paramiko (tanpa apt-get)"""
import paramiko
import time
import sys
import random
import string

HOST = "192.168.1.14"
USER = "telur"
PASS = "telur"
PROJ = "/home/telur/tetasco-connect"

def run(client, cmd, label=""):
    if label:
        print(f"\n[{label}]", flush=True)
    try:
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=False)
        stdout.channel.settimeout(300)
        out_chunks = []
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                chunk = stdout.read(4096)
                decoded = chunk.decode("utf-8", "replace")
                out_chunks.append(decoded)
                sys.stdout.write(decoded)
                sys.stdout.flush()
        # Read remaining
        remaining = stdout.read().decode("utf-8", "replace")
        if remaining:
            out_chunks.append(remaining)
            sys.stdout.write(remaining)
            sys.stdout.flush()
        out = "".join(out_chunks)
        rc  = stdout.channel.recv_exit_status()
        return rc, out
    except Exception as e:
        print(f"  [ERR] {e}", flush=True)
        return 1, ""

def gen_pass(prefix="", length=16):
    """Generate random password locally"""
    chars = string.ascii_letters + string.digits
    rand  = "".join(random.choices(chars, k=length))
    return f"{prefix}{rand}" if prefix else rand

print("=" * 55, flush=True)
print("  Tetasco MQTT Server Setup v2", flush=True)
print("=" * 55, flush=True)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, 22, USER, PASS, timeout=10)
print(f"Connected to {HOST}!", flush=True)

# ── 1. Cek status ────────────────────────────────────────────
run(c, "docker ps --format 'table {{.Names}}\\t{{.Status}}'", "Running containers")
run(c, f"ls -la {PROJ}/mosquitto/config/", "Mosquitto config files")

# ── 2. Generate passwords LOKAL, upload ke server via SFTP ───
print("\n[2. Generate passwords locally]", flush=True)
PASSWD_FILE = f"{PROJ}/mosquitto/config/passwd"
LOG_FILE    = f"{PROJ}/mqtt_passwords.txt"

server_pass = gen_pass("srv-")
passwords   = {"server": server_pass}
for i in range(1, 16):
    passwords[f"lemari-{i}"] = gen_pass(f"lem{i}-")

# Build password entries menggunakan docker run (satu per satu)
# Reset file dulu
run(c, f"echo -n > {PASSWD_FILE} && echo -n > {LOG_FILE}")

for user, pwd in passwords.items():
    # Gunakan mosquitto docker image untuk hash password
    cmd = (
        f"docker run --rm -v {PROJ}/mosquitto/config:/mosquitto/config "
        f"eclipse-mosquitto:2 mosquitto_passwd -b /mosquitto/config/passwd {user} '{pwd}' "
        f"&& echo '{user} = {pwd}' >> {LOG_FILE}"
    )
    run(c, cmd)
    print(f"  {user} = {pwd}", flush=True)

run(c, f"chmod 600 {PASSWD_FILE} {LOG_FILE}", "Secure files")
run(c, f"wc -l {PASSWD_FILE} {LOG_FILE}", "Password count")

# ── 3. Buat .env ──────────────────────────────────────────────
print("\n[3. Create .env]", flush=True)
db_pass  = gen_pass("db-")
env_text = f"DB_PASS={db_pass}\nMQTT_SERVER_PASS={server_pass}\n"
sftp = c.open_sftp()
import io
sftp.putfo(io.BytesIO(env_text.encode()), f"{PROJ}/.env")
sftp.chmod(f"{PROJ}/.env", 0o600)
print(f"  DB_PASS   = {db_pass}", flush=True)
print(f"  MQTT_PASS = {server_pass}", flush=True)

# ── 4. Backend support files via SFTP ────────────────────────
print("\n[4. Backend files]", flush=True)

requirements = (
    "fastapi>=0.111.0\n"
    "uvicorn[standard]>=0.29.0\n"
    "paho-mqtt>=2.0.0\n"
    "asyncpg>=0.29.0\n"
    "psycopg2-binary>=2.9.9\n"
    "python-dotenv>=1.0.0\n"
)
sftp.putfo(io.BytesIO(requirements.encode()), f"{PROJ}/backend/requirements.txt")
print("  requirements.txt uploaded", flush=True)

dockerfile = (
    "FROM python:3.11-slim\n"
    "WORKDIR /app\n"
    "COPY requirements.txt .\n"
    "RUN pip install --no-cache-dir -r requirements.txt\n"
    "COPY . .\n"
    "EXPOSE 8000\n"
    'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]\n'
)
sftp.putfo(io.BytesIO(dockerfile.encode()), f"{PROJ}/backend/Dockerfile")
print("  Dockerfile uploaded", flush=True)

nginx_conf = (
    "events { worker_connections 1024; }\n"
    "http {\n"
    "    include mime.types;\n"
    "    default_type application/octet-stream;\n"
    "    upstream fastapi { server backend:8000; }\n"
    "    server {\n"
    "        listen 80;\n"
    "        server_name _;\n"
    "        location /api/ {\n"
    "            proxy_pass http://fastapi;\n"
    "            proxy_set_header Host $host;\n"
    "            proxy_set_header X-Real-IP $remote_addr;\n"
    "        }\n"
    "        location /docs         { proxy_pass http://fastapi/docs; }\n"
    "        location /openapi.json { proxy_pass http://fastapi/openapi.json; }\n"
    "        location / { root /usr/share/nginx/html; try_files $uri $uri/ /index.html; }\n"
    "    }\n"
    "}\n"
)
sftp.putfo(io.BytesIO(nginx_conf.encode()), f"{PROJ}/nginx/nginx.conf")
print("  nginx.conf uploaded", flush=True)

sftp.putfo(io.BytesIO(b"<h1>Tetasco Connect</h1>\n"), f"{PROJ}/frontend/index.html")
print("  frontend/index.html uploaded", flush=True)

sftp.close()

# ── 5. Docker Compose - stop old, start new (dengan Mosquitto) ─
print("\n[5. Docker Compose rebuild with Mosquitto]", flush=True)
run(c, f"cd {PROJ} && docker compose down 2>&1 | tail -5", "Stopping old containers")
time.sleep(2)
run(c, f"cd {PROJ} && docker compose pull mosquitto 2>&1 | tail -5", "Pull Mosquitto image")
run(c, f"cd {PROJ} && docker compose up -d --build 2>&1", "Starting all services (this takes a few minutes...)")

# ── 6. Health check ───────────────────────────────────────────
print("\n[6. Waiting 8s for services...]", flush=True)
time.sleep(8)
run(c, f"cd {PROJ} && docker compose ps", "Container status")
run(c, "curl -s http://localhost/api/health 2>/dev/null || echo 'API starting...'", "API health")

# ── 7. Test MQTT ─────────────────────────────────────────────
print("\n[7. Test MQTT broker]", flush=True)
run(c,
    f"docker exec tetasco-mosquitto mosquitto_pub "
    f"-h localhost -p 1883 -u server -P '{server_pass}' "
    f"-t 'test/setup' -m 'hello_tetasco' 2>&1 && echo 'MQTT PUBLISH OK'",
    "MQTT publish test")

# ── 8. Summary ───────────────────────────────────────────────
rc, ip_raw = run(c, "hostname -I | awk '{print $1}'")
server_ip = ip_raw.strip()

print("\n" + "=" * 55, flush=True)
print("  SETUP SELESAI!", flush=True)
print("=" * 55, flush=True)
print(f"""
  Server IP     : {server_ip}
  MQTT TCP      : {server_ip}:1883
  MQTT WS       : {server_ip}:9001
  API           : http://{server_ip}/api/health
  Passwords     : {LOG_FILE}
  Server pass   : {server_pass}

  Cloudflare sudah running -> cek: curl https://api.tetasco.my.id/api/health

  RASPI LEMARI SETUP:
  1. scp telur@{server_ip}:{PROJ}/relay_api_mqtt.py .
  2. pip install flask flask-cors paho-mqtt>=2.0.0 gpiozero
  3. DEVICE_ID=lemari-1 MQTT_PASS=<password> python relay_api_mqtt.py
""", flush=True)

c.close()
print("Done!", flush=True)
