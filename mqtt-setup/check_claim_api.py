"""check_claim_api.py — Verifikasi claim API dan test lengkap"""
import paramiko, sys, json, time
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

# 1. Cek server running + CORS
r(cs, 'curl -s http://localhost:8000/api/health', '1. Health check')

# 2. Cek apakah claim endpoint ada
r(cs, 'docker exec tetasco-backend grep -n "api/claim\|claim_device\|CLAIM_MASTER" /app/main.py | head -10',
  '2. Claim code di container')

# 3. Test claim-token endpoint
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/claim-token | python3 -m json.tool',
  '3. Claim token lemari-1')

# 4. Cek syntax error di server logs
r(cs, 'docker logs tetasco-backend --since=5m 2>&1 | grep -iE "Error|error|Syntax|Traceback" | tail -10',
  '4. Server error logs')

# 5. Test full claim flow
r(cs, '''TOKEN=$(curl -s http://localhost:8000/api/tetasco/1/claim-token | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('token',''))")
echo "Token: $TOKEN"
curl -s -X POST http://localhost:8000/api/claim \
    -H "Content-Type: application/json" \
    -d "{\"tetascoId\":1,\"claimToken\":\"$TOKEN\",\"appId\":\"test-phone-uuid-dika\",\"farmName\":\"Kandang Dika\"}" | python3 -m json.tool''',
  '5. Full claim flow test')

r(cs, 'curl -s "http://localhost:8000/api/my-devices?appId=test-phone-uuid-dika" | python3 -m json.tool',
  '6. my-devices untuk Dika')

cs.close()
print('\nDone!', flush=True)
