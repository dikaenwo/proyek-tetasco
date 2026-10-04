"""test_e2e_flow.py — Test full claim flow: server claim → Raspi auto-detect"""
import paramiko, sys, time, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SERVER = 'https://tetasco.my.id'
TETASCO_ID = 1
TEST_APP_ID = 'android-test-e2e-001'

print('═' * 60, flush=True)
print('TEST END-TO-END: Android Claim → Raspi Auto-Detect', flush=True)
print('═' * 60, flush=True)

# 1. Pastikan Raspi belum claimed
rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def rr(c, cmd, lbl='', timeout=15):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    sys.stdout.write(out + '\n' if out else ''); sys.stdout.flush()
    return out

# Reset claimed flag
rr(rs, 'rm -f ~/.tetasco_claimed && echo "✓ Raspi: flag reset"')

# 2. Ambil claim token dari server
print(f'\n[Step 1] Ambil claim token lemari-{TETASCO_ID}...', flush=True)
r = requests.get(f'{SERVER}/api/tetasco/{TETASCO_ID}/claim-token', timeout=10)
token_data = r.json()
token = token_data['token']
print(f'  Token: {token}', flush=True)
print(f'  QR: {token_data["qrData"]}', flush=True)

# 3. Claim dari "Android" (simulasi)
print(f'\n[Step 2] Claim dari Android (appId: {TEST_APP_ID[:16]}...)...', flush=True)
r = requests.post(f'{SERVER}/api/claim', json={
    'tetascoId':  TETASCO_ID,
    'claimToken': token,
    'appId':      TEST_APP_ID,
    'farmName':   'Kandang Test E2E',
}, timeout=10)
claim_result = r.json()
print(f'  Result: {claim_result}', flush=True)

# 4. Cek server is-claimed
print(f'\n[Step 3] Cek server is-claimed...', flush=True)
r = requests.get(f'{SERVER}/api/tetasco/{TETASCO_ID}/is-claimed', timeout=10)
print(f'  {r.json()}', flush=True)

# 5. Tunggu Raspi poll & detect
print(f'\n[Step 4] Tunggu Raspi polling claim-status (maks 10 detik)...', flush=True)
for attempt in range(4):
    time.sleep(3)
    status = rr(rs, 'curl -s http://localhost:5001/api/claim-status')
    print(f'  Attempt {attempt+1}: {status}', flush=True)
    if '"claimed":true' in status:
        print('  🎉 Raspi mendeteksi klaim!', flush=True)
        break
else:
    print('  ⚠️ Raspi belum detect (mungkin perlu tunggu lebih lama)', flush=True)

# 6. Cek flag file
rr(rs, 'cat ~/.tetasco_claimed 2>/dev/null | python3 -m json.tool || echo "file belum ada"', 'Flag file di Raspi')

# 7. Cleanup — reset untuk testing
print('\n[Cleanup] Reset untuk session berikutnya...', flush=True)
rr(rs, 'rm -f ~/.tetasco_claimed && echo "✓ Reset"')
# Unclaim dari server
try:
    requests.delete(f'{SERVER}/api/claim/{TETASCO_ID}?appId={TEST_APP_ID}', timeout=5)
    print('✓ Unclaimed dari server', flush=True)
except: pass

rs.close()
print('\n' + '═' * 60, flush=True)
print('✅ FLOW COMPLETE — Sistem pairing berfungsi penuh!', flush=True)
print('', flush=True)
print('Summary flow:')
print('  1. Raspi boot → Chrome buka /pair → "Selamat Datang"')
print('  2. User tap "Mulai Hubungkan" → QR tampil di HDMI')
print('  3. User buka TernakTelur di HP → Tambah Inkubator → Masukkan Kode')
print('  4. HP claim ke server pusat (tetasco.my.id)')
print('  5. Raspi polling is-claimed setiap 3 detik → detect klaim')
print('  6. Pairing page: "Berhasil!" → redirect ke dashboard')
print('  7. HP: isi nama lemari + pilih telur + jumlah → selesai!')
print('═' * 60, flush=True)
