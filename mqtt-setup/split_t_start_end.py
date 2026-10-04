import paramiko, sys, io, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# ── PATCH 1: hydraulic_controller.py ─────────────────────────────────────────
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/hardware/hydraulic_controller.py')
ctrl = o.read().decode('utf-8','replace')

# Update signature: tambah t_start dan t_end
ctrl = re.sub(
    r'def start_timed_oscillation\([^)]+\)',
    lambda _: (
        'def start_timed_oscillation(\n'
        '        self,\n'
        '        n_cycles: int = 3,\n'
        '        t_center_to_edge: float = 3.0,\n'  # kept for backward compat
        '        t_full: float = 8.3,\n'
        '        t_up: float = None,\n'
        '        t_down: float = None,\n'
        '        t_start: float = None,\n'  # tengah → atas
        '        t_end: float = None,\n'    # atas → tengah
        '    )'
    ),
    ctrl, count=1, flags=re.DOTALL
)
print('[OK] Signature updated: t_start, t_end ditambah')

# Update body: ganti t_center_to_edge jadi _t_start/_t_end
OLD_RESOLVE = '''        # Resolusi t_up / t_down (fallback ke t_full)
        _t_up   = float(t_up)   if t_up   is not None else float(t_full)
        _t_down = float(t_down) if t_down is not None else float(t_full)'''

NEW_RESOLVE = '''        # Resolusi semua timing (fallback ke t_center_to_edge / t_full)
        _t_up    = float(t_up)    if t_up    is not None else float(t_full)
        _t_down  = float(t_down)  if t_down  is not None else float(t_full)
        _t_start = float(t_start) if t_start is not None else float(t_center_to_edge)
        _t_end   = float(t_end)   if t_end   is not None else float(t_center_to_edge)'''

ctrl = ctrl.replace(OLD_RESOLVE, NEW_RESOLVE, 1)
print('[OK] Resolve block updated')

# Update log dan sleep: ganti t_center_to_edge → _t_start/_t_end
ctrl = ctrl.replace(
    '"[TIMED] Mulai urutan: tengah→atas(%.1fs) × %d siklus (turun=%.1fs naik=%.1fs) → tengah(%.1fs)",\n'
    '                    t_center_to_edge, n_cycles, _t_down, _t_up, t_center_to_edge,',
    '"[TIMED] Mulai: tengah→atas(%.1fs) × %d siklus (turun=%.1fs naik=%.1fs) → atas→tengah(%.1fs)",\n'
    '                    _t_start, n_cycles, _t_down, _t_up, _t_end,'
)
ctrl = ctrl.replace(
    'logger.info("[TIMED] UP %.1f detik (tengah→atas)", t_center_to_edge)\n'
    '                self._interruptible_sleep(t_center_to_edge)',
    'logger.info("[TIMED] UP %.1f detik (tengah→atas)", _t_start)\n'
    '                self._interruptible_sleep(_t_start)'
)
ctrl = ctrl.replace(
    'logger.info("[TIMED] DOWN %.1f detik (atas→tengah/posisi awal)", t_center_to_edge)\n'
    '                self._interruptible_sleep(t_center_to_edge)',
    'logger.info("[TIMED] DOWN %.1f detik (atas→tengah/posisi awal)", _t_end)\n'
    '                self._interruptible_sleep(_t_end)'
)
print('[OK] Sleep calls updated')

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(ctrl.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/hydraulic_controller.py')
sftp.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/hardware/hydraulic_controller.py && echo OK', 'Syntax ctrl')

# ── PATCH 2: app.py endpoint ─────────────────────────────────────────────────
i2,o2,e2 = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app = o2.read().decode('utf-8','replace')

OLD_API_RESOLVE = '''        t_up             = float(data['t_up'])   if 't_up'   in data else None
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
        })'''

NEW_API_RESOLVE = '''        t_up             = float(data['t_up'])    if 't_up'    in data else None
        t_down           = float(data['t_down'])  if 't_down'  in data else None
        t_start          = float(data['t_start']) if 't_start' in data else None
        t_end            = float(data['t_end'])   if 't_end'   in data else None

        # Resolusi efektif
        _t_up    = t_up    if t_up    is not None else t_full
        _t_down  = t_down  if t_down  is not None else t_full
        _t_start = t_start if t_start is not None else t_center_to_edge
        _t_end   = t_end   if t_end   is not None else t_center_to_edge

        status = hydraulic_controller.start_timed_oscillation(
            n_cycles=n_cycles,
            t_center_to_edge=t_center_to_edge,
            t_full=t_full,
            t_up=t_up,
            t_down=t_down,
            t_start=t_start,
            t_end=t_end,
        )
        total_duration = _t_start + n_cycles * (_t_down + _t_up) + _t_end
        return jsonify({
            **status,
            'mode'              : 'timed_sequence',
            'n_cycles'          : n_cycles,
            't_start'           : _t_start,
            't_down'            : _t_down,
            't_up'              : _t_up,
            't_end'             : _t_end,
            'total_duration_sec': round(total_duration, 2),
        })'''

if OLD_API_RESOLVE in app:
    app = app.replace(OLD_API_RESOLVE, NEW_API_RESOLVE, 1)
    print('[OK] app.py endpoint updated')
else:
    print('[WARN] app.py pattern tidak cocok')

sftp2 = rp.open_sftp()
sftp2.putfo(io.BytesIO(app.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp2.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/app.py && echo OK', 'Syntax app.py')

# ── PATCH 3: kalibrasi.html ─────────────────────────────────────────────────
i3,o3,e3 = rp.exec_command('cat ~/Penetas-Telur/dist/kalibrasi.html')
html = o3.read().decode('utf-8','replace')

# Ganti 1 input t_edge → 2 input t_start dan t_end
OLD_EDGE_INPUT = '''  <div class="row">
    <label>Tengah → Atas / Atas → Tengah</label>
    <div class="inp-wrap">
      <input type="number" id="t_edge" value="3.0" min="0.5" max="10" step="0.1"/>
      <span class="unit">dtk</span>
    </div>
  </div>'''

NEW_EDGE_INPUT = '''  <div class="row">
    <label>Tengah → Atas (naik awal)</label>
    <div class="inp-wrap">
      <input type="number" id="t_start" value="3.0" min="0.5" max="10" step="0.1"/>
      <span class="unit">dtk</span>
    </div>
  </div>
  <div class="row">
    <label>Atas → Tengah (turun akhir)</label>
    <div class="inp-wrap">
      <input type="number" id="t_end" value="3.0" min="0.5" max="10" step="0.1"/>
      <span class="unit">dtk</span>
    </div>
  </div>'''

html = html.replace(OLD_EDGE_INPUT, NEW_EDGE_INPUT, 1)
print('[OK] HTML input t_start/t_end')

# Fix calcTotal
OLD_CALC = """function calcTotal() {
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

NEW_CALC = """function calcTotal() {
  const ts = +document.getElementById('t_start').value;
  const te = +document.getElementById('t_end').value;
  const td = +document.getElementById('t_down').value;
  const tu = +document.getElementById('t_up').value;
  const n  = +document.getElementById('n_cycles').value;
  const tot = ts + n * (td + tu) + te;
  document.getElementById('preview').innerHTML =
    `Tengah→Atas <b>${ts}s</b> | Siklus <b>${n}×(↓${td}s+↑${tu}s)</b> | Atas→Tengah <b>${te}s</b> | Total: <b>${tot.toFixed(1)}s</b>`;
  return tot;
}
['t_start','t_end','t_down','t_up','n_cycles'].forEach(id =>
  document.getElementById(id).addEventListener('input', calcTotal));"""

html = html.replace(OLD_CALC, NEW_CALC, 1)
print('[OK] calcTotal updated')

# Fix startSeq
OLD_SEQ = """async function startSeq() {
  const t_edge   = +document.getElementById('t_edge').value;
  const t_down   = +document.getElementById('t_down').value;
  const t_up     = +document.getElementById('t_up').value;
  const n_cycles = +document.getElementById('n_cycles').value;
  seqTotal = calcTotal();
  seqStart = Date.now();

  document.getElementById('btn-start').disabled = true;
  document.getElementById('btn-stop').disabled = false;
  document.getElementById('seq-visual').style.display = 'flex';
  setSeqStep(0);

  log(`▶ START: edge=${t_edge}s turun=${t_down}s naik=${t_up}s cycles=${n_cycles} total=${seqTotal.toFixed(1)}s`);
  try {
    const r = await fetch(`${API}/api/hydraulic/timed_oscillation`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({t_center_to_edge: t_edge, t_down, t_up, n_cycles})
    });"""

NEW_SEQ = """async function startSeq() {
  const t_start  = +document.getElementById('t_start').value;
  const t_end    = +document.getElementById('t_end').value;
  const t_down   = +document.getElementById('t_down').value;
  const t_up     = +document.getElementById('t_up').value;
  const n_cycles = +document.getElementById('n_cycles').value;
  seqTotal = calcTotal();
  seqStart = Date.now();

  document.getElementById('btn-start').disabled = true;
  document.getElementById('btn-stop').disabled = false;
  document.getElementById('seq-visual').style.display = 'flex';
  setSeqStep(0);

  log(`▶ START: tengah→atas=${t_start}s ↓${t_down}s ↑${t_up}s ×${n_cycles} atas→tengah=${t_end}s total=${seqTotal.toFixed(1)}s`);
  try {
    const r = await fetch(`${API}/api/hydraulic/timed_oscillation`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({t_start, t_end, t_down, t_up, n_cycles})
    });"""

html = html.replace(OLD_SEQ, NEW_SEQ, 1)
print('[OK] startSeq updated')

sftp3 = rp.open_sftp()
sftp3.putfo(io.BytesIO(html.encode()), '/home/tetasco1/Penetas-Telur/dist/kalibrasi.html')
sftp3.close()

# Cek sisa t_edge
sisa = [l.strip() for l in html.split('\n') if 't_edge' in l]
print('[Sisa t_edge]:', sisa if sisa else 'Tidak ada ✅')

rp.close()
print('\n✅ t_start dan t_end sudah terpisah! Refresh browser.')
