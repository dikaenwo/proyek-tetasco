#!/bin/bash
# =============================================================================
#  install_lemari.sh — Setup MQTT Client di Raspi Lemari
#  Jalankan di MASING-MASING Raspi Lemari:
#    chmod +x install_lemari.sh
#    DEVICE_ID=lemari-1 MQTT_PASS=password-lemari-1 sudo -E ./install_lemari.sh
# =============================================================================

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

DEVICE_ID="${DEVICE_ID:-lemari-1}"
MQTT_PASS="${MQTT_PASS:-GANTI_INI}"
INSTALL_DIR="/home/pi/tetasco-lemari"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║      Tetasco — Install Raspi Lemari: $DEVICE_ID          "
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ─── 1. Install dependencies ──────────────────────────────────────────────────
info "Menginstall dependencies Python..."
apt-get update -qq
apt-get install -y python3-pip python3-venv python3-gpiozero

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# ─── 2. Virtual environment ───────────────────────────────────────────────────
info "Membuat virtual environment..."
python3 -m venv venv
source venv/bin/activate

pip install --quiet \
    flask \
    flask-cors \
    "paho-mqtt>=2.0.0" \
    gpiozero \
    RPi.GPIO

log "Dependencies terinstall"

# ─── 3. Copy file ─────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/relay_api_mqtt.py" "$INSTALL_DIR/"
log "relay_api_mqtt.py disalin"

# ─── 4. Buat systemd service ──────────────────────────────────────────────────
info "Membuat systemd service..."
cat > "/etc/systemd/system/tetasco-relay.service" <<EOF
[Unit]
Description=Tetasco Relay API + MQTT Client ($DEVICE_ID)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python relay_api_mqtt.py
Environment=DEVICE_ID=$DEVICE_ID
Environment=MQTT_BROKER=mqtt.tetasco.my.id
Environment=MQTT_PORT=443
Environment=MQTT_TRANSPORT=websockets
Environment=MQTT_USE_TLS=true
Environment=MQTT_WEBSOCKET_PATH=/mqtt
Environment=MQTT_USER=$DEVICE_ID
Environment=MQTT_PASS=$MQTT_PASS
Environment=FLASK_PORT=5001
Environment=SENSOR_INTERVAL=10
Environment=HEARTBEAT_INTERVAL=30
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable tetasco-relay
systemctl start  tetasco-relay

sleep 2
systemctl status tetasco-relay --no-pager

log "Service tetasco-relay aktif sebagai $DEVICE_ID!"
echo ""
info "Cek log: journalctl -fu tetasco-relay"
