# Tetasco Connect — MQTT IoT Multi-Lemari

## Struktur File

```
mqtt-setup/
├── deploy.py                    ← Script deploy otomatis via Paramiko SSH
├── JALANKAN_DI_SERVER.sh        ← Fallback: copy-paste ke terminal SSH
├── docker-compose.yml           ← All services (Mosquitto + FastAPI + DB + Nginx)
│
├── mosquitto/
│   └── config/
│       ├── mosquitto.conf       ← Config broker (TCP:1883 + WebSocket:9001)
│       └── acl.conf             ← Access control per lemari
│
├── backend/
│   ├── mqtt_manager.py          ← MQTT publisher/subscriber untuk FastAPI
│   └── main.py                  ← FastAPI endpoints dengan MQTT integration
│
├── raspberry_pi/
│   ├── relay_api_mqtt.py        ← SALIN KE TIAP RASPI LEMARI
│   ├── tetasco-relay.service    ← systemd service template
│   └── install_lemari.sh        ← Auto-install script tiap Raspi
│
└── cloudflare/
    └── config.yml               ← Cloudflare Tunnel config
```

---

## Topik MQTT

| Topik | Arah | Payload |
|-------|------|---------|
| `tetasco/{id}/command/{aktuator}` | Server → Lemari | `{"state": true, "ts": 123}` |
| `tetasco/{id}/command/emergency_stop` | Server → Lemari | `{"ts": 123}` |
| `tetasco/ALL/command/emergency_stop` | Server → SEMUA | `{"ts": 123}` |
| `tetasco/{id}/status` | Lemari → Server | `{"fan": true, "heater": false, ...}` |
| `tetasco/{id}/sensor` | Lemari → Server | `{"temperature": 37.5, "humidity": 60.2}` |
| `tetasco/{id}/heartbeat` | Lemari → Server | `{"ts": 123, "ip": "192.168.1.x"}` |

---

## Setup Raspi Lemari (tiap lemari)

```bash
# 1. Install dependencies
pip install flask flask-cors "paho-mqtt>=2.0.0" gpiozero RPi.GPIO

# 2. Copy relay_api_mqtt.py ke Raspi
scp telur@<server-ip>:/home/telur/tetasco-connect/relay_api_mqtt.py .

# 3. Lihat password lemari dari server
cat /home/telur/tetasco-connect/mqtt_passwords.txt

# 4. Jalankan (ganti DEVICE_ID dan MQTT_PASS sesuai lemari)
DEVICE_ID=lemari-1 \
MQTT_BROKER=mqtt.tetasco.my.id \
MQTT_PORT=443 \
MQTT_TRANSPORT=websockets \
MQTT_USE_TLS=true \
MQTT_PASS="password-dari-file" \
python relay_api_mqtt.py

# 5. Atau install sebagai systemd service
sudo nano /etc/systemd/system/tetasco-relay.service
# (edit DEVICE_ID dan MQTT_PASS di file service)
sudo systemctl enable --now tetasco-relay
```

---

## Setup Cloudflare Tunnel (di Server Pusat)

```bash
# 1. Install cloudflared
curl -L https://pkg.cloudflare.com/cloudflare-main.gpg \
  | sudo tee /usr/share/keyrings/cloudflare-archive-keyring.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-archive-keyring.gpg] \
  https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt-get update && sudo apt-get install -y cloudflared

# 2. Login & buat tunnel
cloudflared tunnel login
cloudflared tunnel create tetasco-mqtt   # catat TUNNEL_ID dari output!

# 3. Konfigurasi
nano ~/.cloudflared/config.yml
# Isi dengan konten dari cloudflare/config.yml, ganti TUNNEL_ID

# 4. Route DNS
cloudflared tunnel route dns tetasco-mqtt mqtt.tetasco.my.id
cloudflared tunnel route dns tetasco-mqtt api.tetasco.my.id

# 5. Jalankan sebagai service
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# 6. Verifikasi
curl https://api.tetasco.my.id/api/health
```

---

## Test MQTT Manual

```bash
# Di server (internal) — test publish ke lemari-1
mosquitto_pub -h localhost -p 1883 \
  -u server -P "<server-password>" \
  -t "tetasco/lemari-1/command/fan" \
  -m '{"state": true}'

# Monitor semua topik
mosquitto_sub -h localhost -p 1883 \
  -u server -P "<server-password>" \
  -t "tetasco/#" -v

# Test dari luar via WebSocket (setelah Cloudflare aktif)
mosquitto_pub -h mqtt.tetasco.my.id -p 443 \
  --cafile /etc/ssl/certs/ca-certificates.crt \
  -u server -P "<server-password>" \
  --websocket-path /mqtt \
  -t "tetasco/lemari-1/command/fan" \
  -m '{"state": true}'
```

---

## API Endpoints Baru (dengan MQTT)

| Method | Endpoint | Fungsi |
|--------|----------|--------|
| GET | `/api/health` | Health check (include mqtt status) |
| GET | `/api/mqtt/status` | Status koneksi MQTT broker |
| POST | `/api/tetasco/{id}/devices/{aktuator}/{on\|off}` | Kontrol via MQTT |
| POST | `/api/tetasco/{id}/devices/emergency-stop` | Emergency stop satu lemari |
| POST | `/api/emergency-stop-all` | Emergency stop SEMUA lemari |
| GET | `/api/tetasco/{id}/devices` | Status aktuator dari MQTT cache |
| GET | `/api/tetasco/{id}/sensors` | Data sensor terakhir dari MQTT |
| GET | `/api/tetasco/{id}/heartbeat` | Status online/offline lemari |
| GET | `/api/tetasco/all/status` | Status semua lemari sekaligus |
