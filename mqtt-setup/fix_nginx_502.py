"""fix_nginx_502.py — Fix Nginx 502: resolver + upstream service name"""
import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(15)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# Nginx config baru: resolver + variable upstream (dynamic DNS)
NEW_NGINX_CONF = r"""events {
    worker_connections 1024;
}

http {
    include      mime.types;
    default_type application/octet-stream;

    # Docker internal DNS resolver (refresh tiap 30 detik)
    resolver 127.0.0.11 valid=30s ipv6=off;

    server {
        listen 80;
        server_name _;

        # ── REST API & FastAPI ──────────────────────────────────────────────
        location /api/ {
            # Gunakan variable agar resolver aktif (dynamic DNS)
            set $backend_upstream "http://tetasco-backend:8000";
            proxy_pass         $backend_upstream;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;
            proxy_read_timeout 60s;
            proxy_connect_timeout 10s;

            # CORS untuk Android
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type, Accept' always;

            # Preflight request
            if ($request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' '*';
                add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
                add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type, Accept';
                add_header 'Access-Control-Max-Age' 1728000;
                add_header 'Content-Length' 0;
                return 204;
            }
        }

        location /docs {
            set $backend_upstream "http://tetasco-backend:8000";
            proxy_pass $backend_upstream/docs;
        }

        location /openapi.json {
            set $backend_upstream "http://tetasco-backend:8000";
            proxy_pass $backend_upstream/openapi.json;
        }

        # ── MQTT over WebSocket ────────────────────────────────────────────
        # Raspi Lemari connect ke: wss://tetasco.my.id/mqtt
        location /mqtt {
            set $mosquitto_upstream "http://tetasco-mosquitto:9001";
            proxy_pass             $mosquitto_upstream;
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

# Tulis ke host file
NGINX_CONF_PATH = '/home/telur/tetasco-connect/nginx/nginx.conf'
sftp = cs.open_sftp()
sftp.putfo(io.BytesIO(NEW_NGINX_CONF.encode()), NGINX_CONF_PATH)
print('[OK] nginx.conf updated di host', flush=True)

# docker cp ke container
r(cs, f'docker cp {NGINX_CONF_PATH} tetasco-nginx:/etc/nginx/nginx.conf && echo "docker cp OK"',
  '1. docker cp nginx.conf ke container')

# Test nginx config
r(cs, 'docker exec tetasco-nginx nginx -t', '2. Test Nginx config')

# Reload nginx
r(cs, 'docker exec tetasco-nginx nginx -s reload && echo "Nginx reload OK"', '3. Reload Nginx')

import time; time.sleep(3)

# Verifikasi
r(cs, 'curl -si http://localhost/api/health | head -8', '4. Test Nginx /api/health')
r(cs, 'curl -s http://localhost/api/tetasco/1/sensor | python3 -m json.tool', '5. Test Nginx /api/tetasco/1/sensor')
r(cs, 'curl -s https://tetasco.my.id/api/health --max-time 10 2>&1', '6. Test Cloudflare /api/health')

sftp.close()
cs.close()
print('\nDone!', flush=True)
