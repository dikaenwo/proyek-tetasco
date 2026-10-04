"""update_nginx_mqtt.py — Tambah MQTT WebSocket proxy ke Nginx"""
import paramiko, sys, time, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)
PROJ = '/home/telur/tetasco-connect'

def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, get_pty=True)
    o.channel.settimeout(60)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8', 'replace')); sys.stdout.flush()
        except: break
    return o.channel.recv_exit_status()

# nginx.conf baru: tambah /mqtt WebSocket proxy ke Mosquitto
NGINX_CONF = """events {
    worker_connections 1024;
}

http {
    include      mime.types;
    default_type application/octet-stream;

    # Upstream FastAPI backend
    upstream fastapi {
        server backend:8000;
    }

    # Upstream Mosquitto WebSocket
    upstream mosquitto_ws {
        server mosquitto:9001;
    }

    server {
        listen 80;
        server_name _;

        # ── REST API & FastAPI ──────────────────────────────────────────────
        location /api/ {
            proxy_pass         http://fastapi;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_read_timeout 60s;
        }

        location /docs {
            proxy_pass http://fastapi/docs;
        }

        location /openapi.json {
            proxy_pass http://fastapi/openapi.json;
        }

        # ── MQTT over WebSocket ────────────────────────────────────────────
        # Raspi Lemari connect ke: wss://tetasco.my.id/mqtt
        # (via Cloudflare Tunnel yang sudah ada, GRATIS!)
        location /mqtt {
            proxy_pass             http://mosquitto_ws;
            proxy_http_version     1.1;
            proxy_set_header       Upgrade    $http_upgrade;
            proxy_set_header       Connection "upgrade";
            proxy_set_header       Host       $host;
            proxy_set_header       X-Real-IP  $remote_addr;
            proxy_read_timeout     86400s;
            proxy_send_timeout     86400s;
            proxy_connect_timeout  10s;
        }

        # ── Static Frontend ────────────────────────────────────────────────
        location / {
            root      /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }
    }
}
"""

sftp = c.open_sftp()
sftp.putfo(io.BytesIO(NGINX_CONF.encode()), f'{PROJ}/nginx/nginx.conf')
sftp.close()
print('[OK] nginx.conf updated: added /mqtt WebSocket proxy', flush=True)

# Reload Nginx (tidak perlu restart, hanya reload config)
r('docker exec tetasco-nginx nginx -t 2>&1', 'Nginx config test')
r('docker exec tetasco-nginx nginx -s reload 2>&1 && echo "Nginx reloaded!"', 'Nginx reload')

time.sleep(2)

# Test MQTT via WebSocket path lokal (dari dalam server)
r('curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost/mqtt '
  '-H "Connection: Upgrade" -H "Upgrade: websocket" '
  '-H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" '
  '-H "Sec-WebSocket-Version: 13" 2>&1', 'Test WS upgrade /mqtt')

# Test API masih jalan
r('curl -s http://localhost/api/health', 'API health (harus tetap OK)')

c.close()
print('\nDone! MQTT WebSocket sekarang di: wss://tetasco.my.id/mqtt', flush=True)
