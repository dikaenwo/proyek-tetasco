"""fix_claim_request_import.py — Fix NameError Request + verify claim API"""
import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(20)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# Baca main.py dari container
i, o, e = cs.exec_command('docker exec tetasco-backend cat /app/main.py')
content = o.read().decode('utf-8', 'replace')
print(f'[INFO] Container main.py: {len(content)} chars', flush=True)

# Cek import FastAPI
r(cs, 'docker exec tetasco-backend grep -n "from fastapi import" /app/main.py | head -3', 'FastAPI imports')

# Fix 1: Tambah Request ke import fastapi jika belum ada
if 'Request' not in content:
    # Cari baris from fastapi import
    for line in content.split('\n'):
        if 'from fastapi import' in line:
            new_line = line.rstrip()
            if 'Request' not in new_line:
                if new_line.endswith(')'):
                    new_line = new_line[:-1] + ', Request)'
                else:
                    new_line = new_line + ', Request'
            content = content.replace(line.rstrip(), new_line, 1)
            print(f'[OK] Tambah Request ke import: {new_line}', flush=True)
            break
else:
    print('[OK] Request sudah diimport', flush=True)

# Fix 2: Cek hmac.new vs hmac.new (di Python 3 harusnya hmac.new)
if 'hmac.new(' in content:
    content = content.replace('hmac.new(', 'hmac.new(', 1)  # no-op tapi cek dulu
    # Actually Python 3 uses hmac.new() - that's correct
    pass

# Tulis ke host + docker cp
sftp = cs.open_sftp()
sftp.putfo(io.BytesIO(content.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.close()

r(cs, 'docker cp /home/telur/tetasco-connect/backend/main.py tetasco-backend:/app/main.py && echo "OK"',
  'docker cp')
r(cs, 'docker restart tetasco-backend && sleep 10', 'Restart')

# Test
import time; time.sleep(5)
r(cs, 'curl -s http://localhost:8000/api/health', 'Health')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/claim-token | python3 -m json.tool', 'Claim token')

# Full claim test
r(cs, '''TOKEN=$(curl -s http://localhost:8000/api/tetasco/1/claim-token | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('token',''))" 2>/dev/null)
echo "Token lemari-1: $TOKEN"
curl -s -X POST http://localhost:8000/api/claim \
    -H "Content-Type: application/json" \
    -d "{\"tetascoId\":1,\"claimToken\":\"$TOKEN\",\"appId\":\"dika-test-uuid\",\"farmName\":\"Kandang Dika\"}" | python3 -m json.tool
echo "---"
curl -s "http://localhost:8000/api/my-devices?appId=dika-test-uuid" | python3 -m json.tool''',
  'Full claim test')

cs.close()
print('\n✅ Done!', flush=True)
