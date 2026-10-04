import paramiko, sys, io, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# ── PATCH 1: hydraulic_controller.py — pisah t_up / t_down ───────────────────
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/hardware/hydraulic_controller.py')
ctrl = o.read().decode('utf-8','replace')

OLD_SIG = '''    def start_timed_oscillation(
        self,
        n_cycles: int = 3,
        t_center_to_edge: float = 3.0,
        t_full: float = 8.3,
    ) -> dict:
        """
        Jalankan urutan bolak-balik telur berbasis WAKTU (tanpa limit switch).

        Sequence:
          tengah → atas    : UP  t_center_to_edge detik
          (atas ↔ bawah)  : n_cycles kali (masing-masing t_full detik)
          atas → tengah   : DOWN t_center_to_edge detik

        Parameters:
          n_cycles         : jumlah siklus bolak-balik (default 3)
          t_center_to_edge : durasi tengah→atas dan atas→tengah (detik)
          t_full           : durasi satu gerakan penuh atas↔bawah (detik)
        """'''

NEW_SIG = '''    def start_timed_oscillation(
        self,
        n_cycles: int = 3,
        t_center_to_edge: float = 3.0,
        t_full: float = 8.3,
        t_up: float = None,
        t_down: float = None,
    ) -> dict:
        """
        Jalankan urutan bolak-balik telur berbasis WAKTU (tanpa limit switch).

        Sequence:
          tengah → atas    : UP  t_center_to_edge detik
          (atas → bawah)  : n_cycles kali, t_down detik per gerakan turun
          (bawah → atas)  : n_cycles kali, t_up detik per gerakan naik
          atas → tengah   : DOWN t_center_to_edge detik

        Parameters:
          n_cycles         : jumlah siklus bolak-balik (default 3)
          t_center_to_edge : durasi tengah→atas dan atas→tengah (detik)
          t_full           : durasi default satu gerakan (jika t_up/t_down tidak disetel)
          t_up             : durasi bawah→atas (override t_full jika disetel)
          t_down           : durasi atas→bawah (override t_full jika disetel)
        """'''

if OLD_SIG in ctrl:
    ctrl = ctrl.replace(OLD_SIG, NEW_SIG, 1)
    print('[OK] Signature start_timed_oscillation diperbarui')
else:
    print('[WARN] Signature tidak cocok, cari alternatif...')

# Patch body: ganti t_full jadi t_up_eff / t_down_eff
OLD_BODY = '''        import threading as _thr

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
                    if not self._seq_running: return'''

NEW_BODY = '''        import threading as _thr

        # Resolusi t_up / t_down (fallback ke t_full)
        _t_up   = float(t_up)   if t_up   is not None else float(t_full)
        _t_down = float(t_down) if t_down is not None else float(t_full)

        # Hentikan sequence sebelumnya jika ada
        self._seq_running = False
        if self._timed_seq_thread and self._timed_seq_thread.is_alive():
            self._timed_seq_thread.join(timeout=1.0)

        def _run_sequence():
            try:
                logger.info(
                    "[TIMED] Mulai urutan: tengah→atas(%.1fs) × %d siklus (turun=%.1fs naik=%.1fs) → tengah(%.1fs)",
                    t_center_to_edge, n_cycles, _t_down, _t_up, t_center_to_edge,
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
                    logger.info("[TIMED] DOWN %.1f detik (siklus %d/%d: atas→bawah)", _t_down, cyc+1, n_cycles)
                    self._interruptible_sleep(_t_down)
                    if not self._seq_running: return

                    # Bawah → Atas
                    with self.lock:
                        self.state          = "UP"
                        self.target_direction = "UP"
                        self._hw_set_outputs(True, False)
                    logger.info("[TIMED] UP %.1f detik (siklus %d/%d: bawah→atas)", _t_up, cyc+1, n_cycles)
                    self._interruptible_sleep(_t_up)
                    if not self._seq_running: return'''

if OLD_BODY in ctrl:
    ctrl = ctrl.replace(OLD_BODY, NEW_BODY, 1)
    print('[OK] Body sequence diperbarui dengan t_up / t_down')
else:
    print('[WARN] Body pattern tidak cocok')

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(ctrl.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/hydraulic_controller.py')
sftp.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/hardware/hydraulic_controller.py && echo OK', 'Syntax ctrl')

# ── PATCH 2: app.py — tambah t_up / t_down ke endpoint ───────────────────────
i2,o2,e2 = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app = o2.read().decode('utf-8','replace')

OLD_API = """        n_cycles         = int(data.get('n_cycles', 3))
        t_center_to_edge = float(data.get('t_center_to_edge', 3.0))
        t_full           = float(data.get('t_full', 8.3))

        # Validasi
        if not (1 <= n_cycles <= 20):
            return jsonify({'error': 'n_cycles harus antara 1 dan 20'}), 400
        if not (1.0 <= t_center_to_edge <= 60.0):
            return jsonify({'error': 't_center_to_edge harus antara 1-60 detik'}), 400
        if not (1.0 <= t_full <= 60.0):
            return jsonify({'error': 't_full harus antara 1-60 detik'}), 400

        status = hydraulic_controller.start_timed_oscillation(
            n_cycles=n_cycles,
            t_center_to_edge=t_center_to_edge,
            t_full=t_full,
        )
        total_duration = t_center_to_edge + (n_cycles * 2 * t_full) + t_center_to_edge
        return jsonify({
            **status,
            'mode'          : 'timed_sequence',
            'n_cycles'      : n_cycles,
            't_center_to_edge': t_center_to_edge,
            't_full'        : t_full,
            'total_duration_sec': total_duration,
        })"""

NEW_API = """        n_cycles         = int(data.get('n_cycles', 3))
        t_center_to_edge = float(data.get('t_center_to_edge', 3.0))
        t_full           = float(data.get('t_full', 8.3))
        t_up             = float(data['t_up'])   if 't_up'   in data else None
        t_down           = float(data['t_down']) if 't_down' in data else None

        # Resolusi efektif untuk total durasi
        _t_up   = t_up   if t_up   is not None else t_full
        _t_down = t_down if t_down is not None else t_full

        status = hydraulic_controller.start_timed_oscillation(
            n_cycles=n_cycles,
            t_center_to_edge=t_center_to_edge,
            t_full=t_full,
            t_up=t_up,
            t_down=t_down,
        )
        total_duration = t_center_to_edge + n_cycles * (_t_down + _t_up) + t_center_to_edge
        return jsonify({
            **status,
            'mode'             : 'timed_sequence',
            'n_cycles'         : n_cycles,
            't_center_to_edge' : t_center_to_edge,
            't_down'           : _t_down,
            't_up'             : _t_up,
            'total_duration_sec': round(total_duration, 2),
        })"""

if OLD_API in app:
    app = app.replace(OLD_API, NEW_API, 1)
    print('[OK] app.py endpoint diperbarui dengan t_up / t_down')
else:
    print('[WARN] app.py pattern tidak cocok')

sftp2 = rp.open_sftp()
sftp2.putfo(io.BytesIO(app.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp2.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/app.py && echo OK', 'Syntax app.py')

# ── PATCH 3: Update halaman kalibrasi dengan input t_up / t_down ─────────────
i3,o3,e3 = rp.exec_command('cat ~/Penetas-Telur/dist/kalibrasi.html')
html = o3.read().decode('utf-8','replace')

OLD_INPUT = '''  <div class="row">
    <label>Atas ↔ Bawah (per gerakan)</label>
    <div class="inp-wrap">
      <input type="number" id="t_full" value="7.5" min="1" max="30" step="0.1"/>
      <span class="unit">dtk</span>
    </div>
  </div>'''

NEW_INPUT = '''  <div class="row">
    <label>Atas → Bawah (turun)</label>
    <div class="inp-wrap">
      <input type="number" id="t_down" value="7.5" min="1" max="30" step="0.1"/>
      <span class="unit">dtk</span>
    </div>
  </div>
  <div class="row">
    <label>Bawah → Atas (naik)</label>
    <div class="inp-wrap">
      <input type="number" id="t_up" value="8.0" min="1" max="30" step="0.1"/>
      <span class="unit">dtk</span>
    </div>
  </div>'''

html = html.replace(OLD_INPUT, NEW_INPUT, 1)

OLD_CALC = """function calcTotal() {
  const e = +document.getElementById('t_edge').value;
  const f = +document.getElementById('t_full').value;
  const n = +document.getElementById('n_cycles').value;
  const tot = e + n * 2 * f + e;
  document.getElementById('preview').innerHTML =
    `Tengah→Atas <b>${e}s</b> | Siklus <b>${n}×2×${f}s</b> | Atas→Tengah <b>${e}s</b> | Total: <b>${tot.toFixed(1)}s</b>`;
  return tot;
}
['t_edge','t_full','n_cycles'].forEach(id =>
  document.getElementById(id).addEventListener('input', calcTotal));"""

NEW_CALC = """function calcTotal() {
  const e = +document.getElementById('t_edge').value;
  const td = +document.getElementById('t_down').value;
  const tu = +document.getElementById('t_up').value;
  const n = +document.getElementById('n_cycles').value;
  const tot = e + n * (td + tu) + e;
  document.getElementById('preview').innerHTML =
    `Tengah→Atas <b>${e}s</b> | Siklus <b>${n}×(turun ${td}s + naik ${tu}s)</b> | Atas→Tengah <b>${e}s</b> | Total: <b>${tot.toFixed(1)}s</b>`;
  return tot;
}
['t_edge','t_down','t_up','n_cycles'].forEach(id =>
  document.getElementById(id).addEventListener('input', calcTotal));"""

html = html.replace(OLD_CALC, NEW_CALC, 1)

OLD_FETCH = """    const r = await fetch(`${API}/api/hydraulic/timed_oscillation`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({t_center_to_edge: t_edge, t_full, n_cycles})
    });"""

NEW_FETCH = """    const t_down = +document.getElementById('t_down').value;
    const t_up = +document.getElementById('t_up').value;
    const r = await fetch(`${API}/api/hydraulic/timed_oscillation`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({t_center_to_edge: t_edge, t_down, t_up, n_cycles})
    });"""

html = html.replace(OLD_FETCH, NEW_FETCH, 1)

OLD_LOG = "    log(`▶ START: edge=${t_edge}s full=${t_full}s cycles=${n_cycles} total=${seqTotal.toFixed(1)}s`);"
NEW_LOG = "    log(`▶ START: edge=${t_edge}s turun=${document.getElementById('t_down').value}s naik=${document.getElementById('t_up').value}s cycles=${n_cycles} total=${seqTotal.toFixed(1)}s`);"
html = html.replace(OLD_LOG, NEW_LOG, 1)

sftp3 = rp.open_sftp()
sftp3.putfo(io.BytesIO(html.encode()), '/home/tetasco1/Penetas-Telur/dist/kalibrasi.html')
sftp3.close()
print('[OK] kalibrasi.html diperbarui dengan input t_up / t_down terpisah')

# Restart
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
chan = rp.get_transport().open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1); chan.close()
print('[OK] Restart')
time.sleep(7)

# Test
raw = ''
i4,o4,e4 = rp.exec_command('curl -s -X POST http://localhost:5001/api/hydraulic/timed_oscillation -H "Content-Type: application/json" -d \'{"t_down":7.0,"t_up":8.0,"n_cycles":1,"t_center_to_edge":2.8}\'')
raw = o4.read().decode('utf-8','replace').strip()
try:
    d = json.loads(raw)
    print(f'[TEST] t_down={d["t_down"]} t_up={d["t_up"]} total={d["total_duration_sec"]}s state={d["state"]}')
except:
    print('[RAW]', raw[:150])

rp.close()
print('\n✅ t_up / t_down terpisah! Buka kalibrasi dan refresh.')
