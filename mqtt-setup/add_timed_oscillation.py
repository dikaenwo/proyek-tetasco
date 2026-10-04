import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=15):
    if lbl: print(f'\n=== {lbl} ===')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Baca file
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/hardware/hydraulic_controller.py')
src = o.read().decode('utf-8', 'replace')
print(f'File size: {len(src)} chars')

# ══════════════════════════════════════════════════════════════════
# PATCH 1: Tambah _timed_mode flag di __init__
# ══════════════════════════════════════════════════════════════════
OLD_INIT_END = '''        self._running = True
        self._init_hardware()'''

NEW_INIT_END = '''        # Timed sequence mode: jika True, monitor loop skip oscillation reversal
        # (arah dikendalikan oleh timer sequence thread, bukan limit switch)
        self._timed_mode = False
        self._seq_running = False   # True selama timer sequence berjalan
        self._timed_seq_thread = None

        self._running = True
        self._init_hardware()'''

if OLD_INIT_END in src:
    src = src.replace(OLD_INIT_END, NEW_INIT_END, 1)
    print('[OK] Patch 1: _timed_mode flag ditambah')
else:
    print('[ERR] Patch 1 gagal')

# ══════════════════════════════════════════════════════════════════
# PATCH 2: Monitor loop — skip oscillation reversal jika _timed_mode
# ══════════════════════════════════════════════════════════════════
OLD_OSC_CHECK = '''                    # 1. KONTROL OSILASI BOLAK-BALIK KETIKA SLIDER PENGGERAK RAK AKTIF
                    if self.is_oscillating:'''

NEW_OSC_CHECK = '''                    # 1. KONTROL OSILASI BOLAK-BALIK KETIKA SLIDER PENGGERAK RAK AKTIF
                    if self.is_oscillating and not self._timed_mode:
                        # Normal oscillation (limit switch based)'''

if OLD_OSC_CHECK in src:
    # Also need to indent the block under the if - but it's already indented
    # Just replace the condition
    src = src.replace(OLD_OSC_CHECK, NEW_OSC_CHECK, 1)
    # Now fix the IDLE branch indent (it was under if self.is_oscillating:)
    print('[OK] Patch 2: timed_mode check ditambah')
else:
    print('[ERR] Patch 2 gagal')

# ══════════════════════════════════════════════════════════════════
# PATCH 3: stop_oscillation — reset _timed_mode dan _seq_running
# ══════════════════════════════════════════════════════════════════
OLD_STOP = '''    def stop_oscillation(self) -> dict:
        """
        Dipanggil saat slider \'Penggerak Rak\' dimatikan (OFF).
        Segera mematikan seluruh sinyal hidrolik (STOP).
        """
        with self.lock:
            self.is_oscillating = False
            self.state = "IDLE"
            self._hw_set_outputs(up_state=False, down_state=False)
            logger.info("Penggerak Rak DIMATIKAN: Seluruh Sinyal Hidrolik Berhenti (STOP)")
            return self.get_status()'''

NEW_STOP = '''    def stop_oscillation(self) -> dict:
        """
        Dipanggil saat slider \'Penggerak Rak\' dimatikan (OFF).
        Segera mematikan seluruh sinyal hidrolik (STOP).
        """
        # Batalkan timer sequence jika sedang berjalan
        self._seq_running = False
        self._timed_mode = False
        with self.lock:
            self.is_oscillating = False
            self.state = "IDLE"
            self._hw_set_outputs(up_state=False, down_state=False)
            logger.info("Penggerak Rak DIMATIKAN: Seluruh Sinyal Hidrolik Berhenti (STOP)")
            return self.get_status()'''

if OLD_STOP in src:
    src = src.replace(OLD_STOP, NEW_STOP, 1)
    print('[OK] Patch 3: stop_oscillation reset timed flags')
else:
    print('[ERR] Patch 3 gagal')

# ══════════════════════════════════════════════════════════════════
# PATCH 4: Tambah metode start_timed_oscillation
# ══════════════════════════════════════════════════════════════════
NEW_METHOD = '''
    def _interruptible_sleep(self, duration: float, step: float = 0.1):
        """Sleep yang bisa diinterrupt jika _seq_running menjadi False."""
        import time as _t
        elapsed = 0.0
        while elapsed < duration and self._seq_running:
            _t.sleep(min(step, duration - elapsed))
            elapsed += step

    def start_timed_oscillation(
        self,
        n_cycles: int = 3,
        t_center_to_edge: float = 4.0,
        t_full: float = 9.0,
    ) -> dict:
        """
        Jalankan urutan bolak-balik telur berbasis WAKTU (tanpa limit switch).

        Sequence:
          tengah → atas    : UP  t_center_to_edge detik
          (atas ↔ bawah)  : n_cycles kali (masing-masing t_full detik)
          atas → tengah   : DOWN t_center_to_edge detik
          → auto-stop (is_oscillating = False)

        Parameters:
          n_cycles         : jumlah siklus bolak-balik (default 3)
          t_center_to_edge : durasi tengah→atas dan atas→tengah (detik)
          t_full           : durasi satu gerakan penuh atas↔bawah (detik)
        """
        import threading as _thr

        # Hentikan sequence sebelumnya jika ada
        self._seq_running = False
        if self._timed_seq_thread and self._timed_seq_thread.is_alive():
            self._timed_seq_thread.join(timeout=1.0)

        def _run_sequence():
            try:
                logger.info(
                    "[TIMED] Mulai urutan: tengah→atas(%.1fs) × %d siklus(%.1fs) → tengah(%.1fs)",
                    t_center_to_edge, n_cycles, t_full, t_center_to_edge,
                )

                # ── Step 1: Tengah → Atas ───────────────────────────────
                with self.lock:
                    self.is_oscillating = True
                    self._timed_mode    = True
                    self.state          = "UP"
                    self.target_direction = "UP"
                    self._hw_set_outputs(True, False)
                logger.info("[TIMED] UP %.1f detik (tengah→atas)", t_center_to_edge)
                self._interruptible_sleep(t_center_to_edge)
                if not self._seq_running: return

                # ── Step 2: Siklus Atas ↔ Bawah (n_cycles kali) ─────────
                for cyc in range(n_cycles):
                    # Atas → Bawah
                    with self.lock:
                        self.state          = "DOWN"
                        self.target_direction = "DOWN"
                        self._hw_set_outputs(False, True)
                    logger.info("[TIMED] DOWN %.1f detik (siklus %d/%d: atas→bawah)", t_full, cyc+1, n_cycles)
                    self._interruptible_sleep(t_full)
                    if not self._seq_running: return

                    # Bawah → Atas
                    with self.lock:
                        self.state          = "UP"
                        self.target_direction = "UP"
                        self._hw_set_outputs(True, False)
                    logger.info("[TIMED] UP %.1f detik (siklus %d/%d: bawah→atas)", t_full, cyc+1, n_cycles)
                    self._interruptible_sleep(t_full)
                    if not self._seq_running: return

                # ── Step 3: Atas → Tengah ────────────────────────────────
                with self.lock:
                    self.state = "DOWN"
                    self.target_direction = "DOWN"
                    self._hw_set_outputs(False, True)
                logger.info("[TIMED] DOWN %.1f detik (atas→tengah/posisi awal)", t_center_to_edge)
                self._interruptible_sleep(t_center_to_edge)

                # ── Selesai: Stop & Deactivate ───────────────────────────
                logger.info("[TIMED] ✅ Urutan selesai! Motor berhenti, pembolak-balik nonaktif.")

            except Exception as exc:
                logger.error("[TIMED] Error sequence: %s", exc)
            finally:
                with self.lock:
                    self._hw_set_outputs(False, False)
                    self.is_oscillating = False
                    self._timed_mode    = False
                    self._seq_running   = False
                    self.state          = "IDLE"

        self._seq_running = True
        t = _thr.Thread(target=_run_sequence, daemon=True, name="timed-osc-seq")
        self._timed_seq_thread = t
        t.start()

        logger.info("[TIMED] Thread sequence dimulai (n_cycles=%d, t_edge=%.1fs, t_full=%.1fs)",
                    n_cycles, t_center_to_edge, t_full)
        return self.get_status()

'''

# Sisipkan SEBELUM `def move_up`
if 'def move_up(self)' in src:
    src = src.replace('    def move_up(self)', NEW_METHOD + '    def move_up(self)', 1)
    print('[OK] Patch 4: start_timed_oscillation + _interruptible_sleep ditambah')
else:
    print('[ERR] Patch 4 gagal — move_up tidak ditemukan')

# Tulis balik
sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(src.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/hydraulic_controller.py')
sftp.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/hardware/hydraulic_controller.py && echo SYNTAX_OK', 'Syntax check')

print('\n[INFO] hydraulic_controller.py updated. Sekarang tambah endpoint API di app.py...')

rp.close()
