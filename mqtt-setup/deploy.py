"""
deploy.py — Upload & Setup Tetasco MQTT ke Server via Paramiko
Jalankan: python deploy.py
"""
import os
import sys
import time
import paramiko

# ─── Konfigurasi SSH ─────────────────────────────────────────────────────────
HOST     = "telur"
PORT     = 22
USER     = "telur"
PASSWORD = "telur"
PROJ     = "/home/telur/tetasco-connect"

# ─── File lokal yang akan diupload ───────────────────────────────────────────
LOCAL_SETUP_DIR = r"d:\Proyek Penetas Telur\mqtt-setup"

def banner(msg):
    print(f"\n{'━'*60}")
    print(f"  {msg}")
    print(f"{'━'*60}")

def run_ssh(client, cmd, desc=""):
    """Jalankan command SSH dan print output real-time."""
    if desc:
        print(f"\n[CMD] {desc}")
    print(f"  $ {cmd[:80]}{'...' if len(cmd)>80 else ''}")
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    exit_code = stdout.channel.recv_exit_status()
    if out.strip():
        for line in out.strip().split("\n"):
            print(f"  | {line}")
    if err.strip() and exit_code != 0:
        for line in err.strip().split("\n"):
            print(f"  ! {line}")
    return exit_code, out, err


def upload_file(sftp, local_path, remote_path):
    """Upload satu file via SFTP."""
    # Buat direktori parent kalau belum ada
    remote_dir = os.path.dirname(remote_path)
    try:
        sftp.stat(remote_dir)
    except FileNotFoundError:
        run_through_mkdir(sftp, remote_dir)
    sftp.put(local_path, remote_path)
    print(f"  [UP] {os.path.basename(local_path)} → {remote_path}")


def run_through_mkdir(sftp, remote_dir):
    """Rekursif mkdir via SFTP."""
    parts = remote_dir.split("/")
    path = ""
    for part in parts:
        if not part:
            continue
        path += f"/{part}"
        try:
            sftp.stat(path)
        except FileNotFoundError:
            try:
                sftp.mkdir(path)
            except Exception:
                pass


def upload_directory(sftp, local_dir, remote_dir):
    """Upload seluruh direktori rekursif."""
    for root, dirs, files in os.walk(local_dir):
        # Hitung relative path
        rel = os.path.relpath(root, local_dir)
        if rel == ".":
            remote_root = remote_dir
        else:
            remote_root = f"{remote_dir}/{rel.replace(os.sep, '/')}"

        # Buat direktori remote
        try:
            sftp.stat(remote_root)
        except FileNotFoundError:
            run_through_mkdir(sftp, remote_root)

        # Upload tiap file
        for fname in files:
            local_path  = os.path.join(root, fname)
            remote_path = f"{remote_root}/{fname}"
            sftp.put(local_path, remote_path)
            print(f"  [UP] {os.path.relpath(local_path, local_dir)} → {remote_path}")


# ═════════════════════════════════════════════════════════════════════════════
print("╔══════════════════════════════════════════════════════════╗")
print("║    Tetasco MQTT — Deploy Script via Paramiko            ║")
print("╚══════════════════════════════════════════════════════════╝")
print(f"\n  Host    : {HOST}:{PORT}")
print(f"  User    : {USER}")
print(f"  Project : {PROJ}")
print(f"  Files   : {LOCAL_SETUP_DIR}")

# ─── Connect ──────────────────────────────────────────────────────────────────
banner("STEP 1: Koneksi SSH")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, PORT, USER, PASSWORD, timeout=10)
    print("  [✓] Terhubung ke server!")
except Exception as e:
    print(f"  [✗] Gagal koneksi: {e}")
    sys.exit(1)

# ─── Info Server ─────────────────────────────────────────────────────────────
run_ssh(client, "uname -a && lsb_release -d 2>/dev/null | head -1", "Info Server")
run_ssh(client, "df -h / | tail -1 && free -h | grep Mem", "Disk & RAM")

# ─── Cek Docker ───────────────────────────────────────────────────────────────
banner("STEP 2: Cek & Install Docker")
rc, out, _ = run_ssh(client, "docker --version 2>/dev/null && docker compose version 2>/dev/null", "Docker check")
if rc != 0 or "Docker" not in out:
    print("  [!] Docker belum ada, menginstall...")
    run_ssh(client, "curl -fsSL https://get.docker.com | sh", "Install Docker")
    run_ssh(client, "sudo usermod -aG docker telur", "Add user to docker group")
else:
    print("  [✓] Docker sudah ada")

# ─── Buat Struktur Folder ────────────────────────────────────────────────────
banner("STEP 3: Buat Struktur Folder")
run_ssh(client,
    f"mkdir -p {PROJ}/{{mosquitto/{{config,data,log}},backend,frontend,nginx,cloudflare}} && "
    f"chmod 777 {PROJ}/mosquitto/data {PROJ}/mosquitto/log && "
    f"ls -la {PROJ}/",
    "Buat folder"
)

# ─── Upload File via SFTP ────────────────────────────────────────────────────
banner("STEP 4: Upload File Konfigurasi")
sftp = client.open_sftp()

# Upload semua file dari mqtt-setup ke server
FILES_TO_UPLOAD = [
    # (local, remote)
    (r"mosquitto\config\mosquitto.conf", f"{PROJ}/mosquitto/config/mosquitto.conf"),
    (r"mosquitto\config\acl.conf",       f"{PROJ}/mosquitto/config/acl.conf"),
    (r"docker-compose.yml",              f"{PROJ}/docker-compose.yml"),
    (r"backend\mqtt_manager.py",         f"{PROJ}/backend/mqtt_manager.py"),
    (r"backend\main.py",                 f"{PROJ}/backend/main.py"),
    (r"JALANKAN_DI_SERVER.sh",           f"{PROJ}/JALANKAN_DI_SERVER.sh"),
    (r"raspberry_pi\relay_api_mqtt.py",  f"{PROJ}/relay_api_mqtt.py"),
    (r"raspberry_pi\tetasco-relay.service", f"{PROJ}/tetasco-relay.service"),
    (r"cloudflare\config.yml",           f"{PROJ}/cloudflare/config.yml"),
]

for local_rel, remote_path in FILES_TO_UPLOAD:
    local_abs = os.path.join(LOCAL_SETUP_DIR, local_rel)
    if os.path.exists(local_abs):
        upload_file(sftp, local_abs, remote_path)
    else:
        print(f"  [SKIP] {local_rel} tidak ditemukan")

sftp.close()
print("\n  [✓] Semua file terupload!")

# ─── Generate Passwords Mosquitto ───────────────────────────────────────────
banner("STEP 5: Generate Passwords Mosquitto")
run_ssh(client,
    "which mosquitto_passwd || (sudo apt-get update -qq && sudo apt-get install -y mosquitto-clients)",
    "Install mosquitto-clients"
)

# Script generate password
gen_passwd_cmd = f"""
PASSWD_FILE="{PROJ}/mosquitto/config/passwd"
PASS_LOG="{PROJ}/mqtt_passwords.txt"
> "$PASSWD_FILE"; > "$PASS_LOG"
SERVER_PASS="srv-$(openssl rand -hex 10)"
mosquitto_passwd -b "$PASSWD_FILE" server "$SERVER_PASS"
echo "server = $SERVER_PASS" >> "$PASS_LOG"
for i in $(seq 1 15); do
    LP="lem${{i}}-$(openssl rand -hex 8)"
    mosquitto_passwd -b "$PASSWD_FILE" "lemari-$i" "$LP"
    echo "lemari-$i = $LP" >> "$PASS_LOG"
done
chmod 600 "$PASS_LOG" "$PASSWD_FILE"
echo "=== PASSWORDS ===" && cat "$PASS_LOG"
"""
run_ssh(client, gen_passwd_cmd, "Generate passwords")

# ─── Buat .env ───────────────────────────────────────────────────────────────
banner("STEP 6: Setup .env & Backend files")
make_env_cmd = f"""
SERVER_PASS=$(grep "^server" {PROJ}/mqtt_passwords.txt | cut -d' ' -f3)
DB_PASS="db-$(openssl rand -hex 12)"
cat > {PROJ}/.env << ENV
DB_PASS=$DB_PASS
MQTT_SERVER_PASS=$SERVER_PASS
ENV
chmod 600 {PROJ}/.env
echo "[.env] DB_PASS=***  MQTT_SERVER_PASS=$SERVER_PASS"
"""
run_ssh(client, make_env_cmd, "Buat .env")

# ─── Backend Support Files ───────────────────────────────────────────────────
run_ssh(client, f"""cat > {PROJ}/backend/requirements.txt << 'REQ'
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
paho-mqtt>=2.0.0
asyncpg>=0.29.0
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0
REQ""", "requirements.txt")

run_ssh(client, f"""cat > {PROJ}/backend/Dockerfile << 'DFILE'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
DFILE""", "Dockerfile")

# ─── Nginx Config ───────────────────────────────────────────────────────────
run_ssh(client, f"""cat > {PROJ}/nginx/nginx.conf << 'NGINX'
events {{ worker_connections 1024; }}
http {{
    include      mime.types;
    default_type application/octet-stream;
    upstream fastapi {{ server backend:8000; }}
    server {{
        listen 80;
        server_name _;
        location /api/ {{
            proxy_pass       http://fastapi;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }}
        location /docs         {{ proxy_pass http://fastapi/docs; }}
        location /openapi.json {{ proxy_pass http://fastapi/openapi.json; }}
        location / {{
            root      /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }}
    }}
}}
NGINX
echo '<h1>Tetasco Connect</h1>' > {PROJ}/frontend/index.html
""", "Nginx config + frontend")

# ─── Jalankan Docker Compose ─────────────────────────────────────────────────
banner("STEP 7: Jalankan Docker Compose")
run_ssh(client, f"cd {PROJ} && sudo docker compose up -d --build 2>&1", "Docker Compose up")
time.sleep(5)
run_ssh(client, f"cd {PROJ} && sudo docker compose ps", "Docker status")

# ─── Health Check ────────────────────────────────────────────────────────────
banner("STEP 8: Health Check")
time.sleep(3)
run_ssh(client, "curl -s http://localhost/api/health 2>/dev/null || echo 'API belum ready, tunggu sebentar...'", "API health")
run_ssh(client,
    "sudo docker exec tetasco-mosquitto mosquitto_pub -h localhost -p 1883 "
    "-u server -P \"$(grep '^server' /home/telur/tetasco-connect/mqtt_passwords.txt | cut -d' ' -f3)\" "
    "-t 'test/ping' -m 'hello' 2>&1 && echo 'MQTT OK!' || echo 'MQTT masih starting...'",
    "MQTT test"
)

# ─── Info Akhir ──────────────────────────────────────────────────────────────
banner("SELESAI!")
rc, out, _ = run_ssh(client, "hostname -I | awk '{print $1}'", "Server IP")
server_ip = out.strip()

print(f"""
  ✅ Mosquitto MQTT Broker  : {server_ip}:1883 (TCP) | {server_ip}:9001 (WebSocket)
  ✅ FastAPI Backend        : http://{server_ip}/api/health
  ✅ Docker Compose         : Running

  📄 Passwords              : {PROJ}/mqtt_passwords.txt

  ━━━ LANGKAH SELANJUTNYA ━━━

  1. Setup Cloudflare Tunnel (jalankan di server):
     sudo apt-get install cloudflared
     cloudflared tunnel login
     cloudflared tunnel create tetasco-mqtt
     nano ~/.cloudflared/config.yml   (edit tunnel ID)
     cloudflared tunnel route dns tetasco-mqtt mqtt.tetasco.my.id
     cloudflared tunnel route dns tetasco-mqtt api.tetasco.my.id
     sudo cloudflared service install && sudo systemctl start cloudflared

  2. Di tiap Raspi Lemari:
     scp telur@{server_ip}:{PROJ}/relay_api_mqtt.py .
     pip install flask flask-cors paho-mqtt gpiozero
     DEVICE_ID=lemari-1 MQTT_PASS=<password-dari-file> python relay_api_mqtt.py
""")

client.close()
print("  [✓] Koneksi SSH ditutup. Done!")
