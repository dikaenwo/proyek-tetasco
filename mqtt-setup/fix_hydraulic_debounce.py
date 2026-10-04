import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n=== {lbl} ===')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Baca file
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/hardware/hydraulic_controller.py')
src = o.read().decode('utf-8','replace')
original_len = len(src)
print(f'File size: {original_len} chars')

# ══════════════════════════════════════════════════════════════════
# PATCH 1: Tambah debounce counter ke __init__
# ══════════════════════════════════════════════════════════════════
OLD1 = '''        # State Limit Switch
        self.limit_max = False
        self.limit_min = False
        self.raw_max = None
        self.raw_min = None'''

NEW1 = '''        # State Limit Switch
        self.limit_max = False
        self.limit_min = False
        self.raw_max = None
        self.raw_min = None
        # Debounce: cegah noise/bounce GPIO → butuh N iterasi berturut-turut sebelum reversal
        self._db_max = 0          # counter berapa kali berturut-turut max_act=True
        self._db_min = 0          # counter berapa kali berturut-turut min_act=True
        self._DEBOUNCE_N = 3      # 3 × 50ms = 150ms sebelum reversal (sesuai referensi sleep(0.1))'''

if OLD1 in src:
    src = src.replace(OLD1, NEW1, 1)
    print('[OK] Patch 1: debounce counter ditambah ke __init__')
else:
    print('[ERR] Patch 1 gagal - pattern tidak cocok')

# ══════════════════════════════════════════════════════════════════
# PATCH 2: Ganti logic osilasi di monitor_loop dengan debounce
# ══════════════════════════════════════════════════════════════════
OLD2 = '''                    # 1. KONTROL OSILASI BOLAK-BALIK KETIKA SLIDER PENGGERAK RAK AKTIF
                    if self.is_oscillating:
                        if self.state == "UP" and max_act:
                            logger.info("[LIMIT MAX TERCAPAI] Sudut maksimum tersentuh! Membalik arah ke TURUN (DOWN)...")
                            self._hw_set_outputs(False, False)
                            time.sleep(DEAD_TIME_DELAY)
                            self.target_direction = "DOWN"
                            self.state = "DOWN"
                            self._hw_set_outputs(False, True)

                        elif self.state == "DOWN" and min_act:
                            logger.info("[LIMIT MIN TERCAPAI] Sudut minimum tersentuh! Membalik arah ke NAIK (UP)...")
                            self._hw_set_outputs(False, False)
                            time.sleep(DEAD_TIME_DELAY)
                            self.target_direction = "UP"
                            self.state = "UP"
                            self._hw_set_outputs(True, False)

                        elif self.state == "IDLE":
                            # Jika dalam status IDLE saat osilasi masih aktif, lanjutkan gerakan
                            if max_act and not min_act:
                                self.state = "DOWN"
                                self._hw_set_outputs(False, True)
                            elif min_act and not max_act:
                                self.state = "UP"
                                self._hw_set_outputs(True, False)
                            else:
                                self.state = self.target_direction
                                if self.target_direction == "UP":
                                    self._hw_set_outputs(True, False)
                                else:
                                    self._hw_set_outputs(False, True)'''

NEW2 = '''                    # 1. KONTROL OSILASI BOLAK-BALIK KETIKA SLIDER PENGGERAK RAK AKTIF
                    if self.is_oscillating:
                        # ── Debounce counter ──────────────────────────────────────
                        # Mengikuti logika referensi: hanya reversal jika limit aktif
                        # selama N iterasi berturut (N×step_dt ≈ 150ms debounce).
                        # Mencegah noise pin/relay-kick memicu reversal palsu.
                        self._db_max = (self._db_max + 1) if max_act else 0
                        self._db_min = (self._db_min + 1) if min_act else 0

                        max_confirmed = (self._db_max >= self._DEBOUNCE_N)
                        min_confirmed = (self._db_min >= self._DEBOUNCE_N)

                        if self.state == "UP" and max_confirmed:
                            logger.info("[LIMIT MAX TERCAPAI] Sudut maksimum tersentuh! Membalik arah ke TURUN (DOWN)...")
                            self._db_max = 0   # reset setelah reversal
                            self._db_min = 0
                            self._hw_set_outputs(False, False)
                            time.sleep(DEAD_TIME_DELAY)
                            self.target_direction = "DOWN"
                            self.state = "DOWN"
                            self._hw_set_outputs(False, True)

                        elif self.state == "DOWN" and min_confirmed:
                            logger.info("[LIMIT MIN TERCAPAI] Sudut minimum tersentuh! Membalik arah ke NAIK (UP)...")
                            self._db_max = 0
                            self._db_min = 0
                            self._hw_set_outputs(False, False)
                            time.sleep(DEAD_TIME_DELAY)
                            self.target_direction = "UP"
                            self.state = "UP"
                            self._hw_set_outputs(True, False)

                        elif self.state == "IDLE":
                            # Jika IDLE saat osilasi aktif, lanjutkan arah target
                            self.state = self.target_direction
                            if self.target_direction == "UP":
                                self._hw_set_outputs(True, False)
                            else:
                                self._hw_set_outputs(False, True)'''

if OLD2 in src:
    src = src.replace(OLD2, NEW2, 1)
    print('[OK] Patch 2: debounce logic ditambah ke oscillation monitor loop')
else:
    print('[ERR] Patch 2 gagal - pattern oscillation tidak cocok')
    # Debug: cari KONTROL OSILASI
    idx = src.find('KONTROL OSILASI')
    if idx >= 0:
        print('Found at', idx, ':')
        print(repr(src[idx:idx+400]))

print(f'\nFile size after: {len(src)} chars (diff: {len(src)-original_len})')

# Syntax check dan deploy
sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(src.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/hydraulic_controller.py')
sftp.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/hardware/hydraulic_controller.py && echo SYNTAX_OK', 'Syntax check')

# Restart Raspi app
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
transport = rp.get_transport()
chan = transport.open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1)
chan.close()
print('[OK] Raspi restart')

time.sleep(8)
ras('curl -s http://localhost:5001/api/hydraulic/status', 'Hydraulic status')

rp.close()
print('\n✅ Hydraulic debounce fix selesai!')
