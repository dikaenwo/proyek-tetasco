#!/bin/bash
# =============================================================================
#  setup.sh — Tetasco Connect MQTT Setup Script
#  Jalankan di Server Pusat Raspberry Pi:
#    chmod +x setup.sh && sudo ./setup.sh
# =============================================================================

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║       Tetasco Connect — MQTT Setup Server Pusat          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ─── 1. Cek Docker ────────────────────────────────────────────────────────────
info "Mengecek Docker..."
if ! command -v docker &>/dev/null; then
    warn "Docker tidak ditemukan. Menginstall..."
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker telur
    log "Docker terinstall"
else
    log "Docker sudah ada: $(docker --version)"
fi

if ! command -v docker compose &>/dev/null 2>&1 && ! docker compose version &>/dev/null 2>&1; then
    warn "Docker Compose plugin tidak ditemukan. Menginstall..."
    apt-get install -y docker-compose-plugin
fi

# ─── 2. Buat Struktur Folder ──────────────────────────────────────────────────
PROJ_DIR="/home/telur/tetasco-connect"
info "Membuat struktur folder di $PROJ_DIR..."

mkdir -p "$PROJ_DIR/mosquitto/config"
mkdir -p "$PROJ_DIR/mosquitto/data"
mkdir -p "$PROJ_DIR/mosquitto/log"
mkdir -p "$PROJ_DIR/backend"
mkdir -p "$PROJ_DIR/frontend"
mkdir -p "$PROJ_DIR/nginx"

chown -R telur:telur "$PROJ_DIR"
log "Struktur folder dibuat"

# ─── 3. Copy File Konfigurasi ─────────────────────────────────────────────────
info "Menyalin file konfigurasi..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "$SCRIPT_DIR/mosquitto/config/mosquitto.conf" "$PROJ_DIR/mosquitto/config/"
cp "$SCRIPT_DIR/mosquitto/config/acl.conf"       "$PROJ_DIR/mosquitto/config/"
cp "$SCRIPT_DIR/docker-compose.yml"              "$PROJ_DIR/"
cp "$SCRIPT_DIR/backend/mqtt_manager.py"         "$PROJ_DIR/backend/"
cp "$SCRIPT_DIR/backend/main.py"                 "$PROJ_DIR/backend/"
log "File konfigurasi disalin"

# ─── 4. Generate Password Mosquitto ──────────────────────────────────────────
info "Membuat file password Mosquitto..."
PASSWD_FILE="$PROJ_DIR/mosquitto/config/passwd"

# Install mosquitto-clients untuk mosquitto_passwd
if ! command -v mosquitto_passwd &>/dev/null; then
    apt-get install -y mosquitto-clients
fi

# Password bisa diganti sesuai kebutuhan
SERVER_PASS="server-$(openssl rand -hex 8)"
echo "" > "$PASSWD_FILE"

# Generate password untuk server dan semua lemari (1-15)
mosquitto_passwd -b "$PASSWD_FILE" server "$SERVER_PASS"
for i in $(seq 1 15); do
    LEMARI_PASS="lemari${i}-$(openssl rand -hex 6)"
    mosquitto_passwd -b "$PASSWD_FILE" "lemari-$i" "$LEMARI_PASS"
    echo "lemari-$i = $LEMARI_PASS" >> "$PROJ_DIR/mqtt_passwords.txt"
done

# Simpan password server
echo "server = $SERVER_PASS" >> "$PROJ_DIR/mqtt_passwords.txt"
chmod 600 "$PROJ_DIR/mqtt_passwords.txt"

log "Password dibuat → $PROJ_DIR/mqtt_passwords.txt"
warn "SIMPAN FILE PASSWORDS INI DI TEMPAT AMAN!"

# ─── 5. Buat .env ─────────────────────────────────────────────────────────────
info "Membuat .env..."
DB_PASS="db-$(openssl rand -hex 12)"
cat > "$PROJ_DIR/.env" <<EOF
DB_PASS=$DB_PASS
MQTT_SERVER_PASS=$SERVER_PASS
EOF
chmod 600 "$PROJ_DIR/.env"
log ".env dibuat"

# ─── 6. Nginx Config ──────────────────────────────────────────────────────────
info "Membuat nginx.conf..."
cat > "$PROJ_DIR/nginx/nginx.conf" <<'EOF'
events { worker_connections 1024; }
http {
    include      mime.types;
    default_type application/octet-stream;

    upstream fastapi { server backend:8000; }

    server {
        listen 80;
        server_name _;

        location /api/ {
            proxy_pass http://fastapi;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        location /docs    { proxy_pass http://fastapi/docs; }
        location /openapi.json { proxy_pass http://fastapi/openapi.json; }
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }
    }
}
EOF
log "nginx.conf dibuat"

# ─── 7. Backend requirements.txt ─────────────────────────────────────────────
cat > "$PROJ_DIR/backend/requirements.txt" <<EOF
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
paho-mqtt>=2.0.0
asyncpg>=0.29.0
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0
EOF

# ─── 8. Backend Dockerfile ───────────────────────────────────────────────────
cat > "$PROJ_DIR/backend/Dockerfile" <<EOF
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
log "Backend Dockerfile dibuat"

# ─── 9. Jalankan Docker Compose ──────────────────────────────────────────────
info "Menjalankan Docker Compose..."
cd "$PROJ_DIR"
docker compose pull mosquitto database nginx 2>/dev/null || true
docker compose build backend
docker compose up -d

log "Semua service berjalan!"
echo ""
docker compose ps

# ─── 10. Cloudflare Tunnel ───────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
info "LANGKAH SELANJUTNYA: Setup Cloudflare Tunnel"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. Install cloudflared:"
echo "     curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o /usr/local/bin/cloudflared"
echo "     chmod +x /usr/local/bin/cloudflared"
echo ""
echo "  2. Login ke Cloudflare:"
echo "     cloudflared tunnel login"
echo ""
echo "  3. Buat tunnel:"
echo "     cloudflared tunnel create tetasco-mqtt"
echo ""
echo "  4. Copy config:"
echo "     cp $SCRIPT_DIR/cloudflare/config.yml ~/.cloudflared/"
echo "     (Edit tunnel ID di config.yml sesuai output step 3)"
echo ""
echo "  5. Route DNS:"
echo "     cloudflared tunnel route dns tetasco-mqtt mqtt.tetasco.my.id"
echo "     cloudflared tunnel route dns tetasco-mqtt api.tetasco.my.id"
echo ""
echo "  6. Install sebagai service:"
echo "     cloudflared service install"
echo "     systemctl enable cloudflared"
echo "     systemctl start cloudflared"
echo ""
echo "  📄 Passwords tersimpan di: $PROJ_DIR/mqtt_passwords.txt"
echo ""
log "Setup selesai!"
