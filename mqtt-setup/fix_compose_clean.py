import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(cmd, lbl='', timeout=30):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i,o,e = sv.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)'); sys.stdout.flush()
    return out

# Baca current compose
i,o,e = sv.exec_command('cat ~/tetasco-connect/docker-compose.yml')
raw = o.read().decode('utf-8','replace')

# Parse baris per baris dan rebuild
lines = raw.split('\n')

# Strategy:
# 1. Hapus blok "volumes:\n  tetasco-claims:" yang standalone (biasanya di akhir)
# 2. Tambahkan "  tetasco-claims:" ke blok volumes yang sudah ada (postgres_data dll)
# 3. Pastikan backend service punya volume mount

out_lines = []
skip_next_vol = False
in_duplicate_vol = False

i_vol = None  # indeks baris "volumes:" pertama yang berisi postgres_data

for idx, line in enumerate(lines):
    # Tandai blok volumes utama (yang berisi postgres_data)
    if line.strip() == 'volumes:' and not line.startswith(' '):
        # Cek apakah ini yang sudah ada (punya postgres_data) atau yang baru (tetasco-claims)
        # Lihat baris berikutnya
        next_lines = '\n'.join(lines[idx+1:idx+5])
        if 'postgres_data' in next_lines:
            # Ini volumes utama
            out_lines.append(line)
            # Tambahkan postgres, mosquitto, lalu tetasco-claims
            # Baris berikutnya akan di-handle normal
        elif 'tetasco-claims' in next_lines and 'postgres_data' not in next_lines:
            # Ini duplikat volumes block, skip sampai ketemu non-volume line
            in_duplicate_vol = True
            continue
        else:
            out_lines.append(line)
    elif in_duplicate_vol:
        # Skip isi dari duplicate volumes block
        if line.startswith(' ') or line.strip() == '':
            if line.strip() == '' and idx + 1 < len(lines) and not lines[idx+1].startswith(' '):
                in_duplicate_vol = False
            continue
        else:
            in_duplicate_vol = False
            out_lines.append(line)
    else:
        out_lines.append(line)

# Rebuild sebagai string
dc_clean = '\n'.join(out_lines)

# Pastikan tetasco-claims ada di volumes section
if 'tetasco-claims' not in dc_clean:
    dc_clean = dc_clean.replace(
        'volumes:\n  postgres_data:\n  mosquitto_data:\n  mosquitto_log:',
        'volumes:\n  postgres_data:\n  mosquitto_data:\n  mosquitto_log:\n  tetasco-claims:',
        1
    )
    print('[OK] tetasco-claims ditambahkan ke volumes')

# Pastikan backend volume mount ada
if 'tetasco-claims:/app/data' not in dc_clean:
    dc_clean = dc_clean.replace(
        '      - ./backend:/app\n',
        '      - ./backend:/app\n      - tetasco-claims:/app/data\n',
        1
    )
    print('[OK] Volume mount /app/data ditambahkan')

print('\n=== Final docker-compose.yml (40 baris terakhir) ===')
print('\n'.join(dc_clean.split('\n')[-40:]))

# Upload
sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(dc_clean.encode()), '/home/telur/tetasco-connect/docker-compose.yml')
sftp.close()
print('\n[OK] docker-compose.yml uploaded')

# Validate
r('cd ~/tetasco-connect && docker compose config --quiet 2>&1 | head -3 || echo "YAML VALID"', '1. Validate YAML')

# Build dan restart
r('cd ~/tetasco-connect && docker compose build backend 2>&1 | tail -5', '2. Build backend', timeout=120)
r('cd ~/tetasco-connect && docker compose up -d 2>&1 | tail -8', '3. Docker up', timeout=30)
time.sleep(12)

r('curl -s http://localhost:8000/api/health', '4. Health check')
r('curl -s -X POST http://localhost:8000/api/tetasco/1/share-token -H "Content-Type: application/json" -d \'{"appId":"test"}\'',
  '5. Test share token → harus berhasil')

sv.close()
print('\n✅ Done!')
