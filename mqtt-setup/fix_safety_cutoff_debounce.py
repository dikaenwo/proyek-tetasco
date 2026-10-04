import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n=== {lbl} ===')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/hardware/hydraulic_controller.py')
src = o.read().decode('utf-8','replace')

# ══════════════════════════════════════════════════════════════════
# PATCH: Pindahkan debounce update ke sebelum if-oscillating, 
#        pakai max_confirmed di safety cutoff juga
# ══════════════════════════════════════════════════════════════════

OLD = '''                    # 1. KONTROL OSILASI BOLAK-BALIK KETIKA SLIDER PENGGERAK RAK AKTIF
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
                                self._hw_set_outputs(False, True)

                    else:
                        # JIKA SLIDER OFF / MANUAL:
                        # Safety Cutoff agar tidak menabrak batas jika digerakkan manual
                        if self.state == "UP" and max_act:
                            logger.info("[SAFETY] Limit MAX tercapai! Menghentikan motor UP.")
                            self._hw_set_outputs(False, False)
                            self.state = "IDLE"'''

NEW = '''                    # ── Debounce counter (berlaku untuk SEMUA mode: osilasi & manual) ──
                    # Butuh N iterasi berturut sebelum limit dianggap tersentuh sungguhan.
                    # Mencegah noise pin / relay-kick memicu limit palsu (3 × 50ms = 150ms).
                    self._db_max = (self._db_max + 1) if max_act else 0
                    self._db_min = (self._db_min + 1) if min_act else 0
                    max_confirmed = (self._db_max >= self._DEBOUNCE_N)
                    min_confirmed = (self._db_min >= self._DEBOUNCE_N)

                    # 1. KONTROL OSILASI BOLAK-BALIK KETIKA SLIDER PENGGERAK RAK AKTIF
                    if self.is_oscillating:
                        if self.state == "UP" and max_confirmed:
                            logger.info("[LIMIT MAX TERCAPAI] Sudut maksimum tersentuh! Membalik arah ke TURUN (DOWN)...")
                            self._db_max = 0
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
                                self._hw_set_outputs(False, True)

                    else:
                        # JIKA SLIDER OFF / MANUAL:
                        # Safety Cutoff — pakai max_confirmed agar tidak stop karena noise pin
                        if self.state == "UP" and max_confirmed:
                            logger.info("[SAFETY] Limit MAX tercapai! Menghentikan motor UP.")
                            self._db_max = 0
                            self._hw_set_outputs(False, False)
                            self.state = "IDLE"'''

if OLD in src:
    src = src.replace(OLD, NEW, 1)
    print('[OK] Debounce dipindah ke sebelum oscillation check, safety cutoff juga pakai max_confirmed')
else:
    print('[ERR] Pattern tidak cocok! Cari context...')
    idx = src.find('KONTROL OSILASI')
    print(repr(src[max(0,idx-200):idx+100]))

# Cek juga safety MIN
OLD_MIN = '''                        elif self.state == "DOWN" and min_act:
                            logger.info("[SAFETY] Limit MIN tercapai! Menghentikan motor DOWN.")
                            self._hw_set_outputs(False, False)
                            self.state = "IDLE"'''

NEW_MIN = '''                        elif self.state == "DOWN" and min_confirmed:
                            logger.info("[SAFETY] Limit MIN tercapai! Menghentikan motor DOWN.")
                            self._db_min = 0
                            self._hw_set_outputs(False, False)
                            self.state = "IDLE"'''

if OLD_MIN in src:
    src = src.replace(OLD_MIN, NEW_MIN, 1)
    print('[OK] Safety cutoff MIN juga pakai min_confirmed')
elif 'min_act' in src[src.find('JIKA SLIDER'):src.find('JIKA SLIDER')+300]:
    print('[WARN] Safety MIN patch tidak cocok')

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(src.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/hydraulic_controller.py')
sftp.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/hardware/hydraulic_controller.py && echo SYNTAX_OK', 'Syntax check')

# Restart
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

# Verifikasi pin raw dalam keadaan idle
ras('curl -s http://localhost:5001/api/hydraulic/raw_limits 2>/dev/null || echo "no endpoint"', 'Raw limits')
ras('grep -i "SAFETY\|LIMIT\|debounce\|noise\|confirmed" /tmp/tetasco_backend.log | tail -5', 'Recent logs')

rp.close()
print('\n✅ Safety cutoff debounce fix selesai!')
