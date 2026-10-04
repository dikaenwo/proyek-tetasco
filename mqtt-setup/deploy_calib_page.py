import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# ── Buat halaman kalibrasi HTML ────────────────────────────────────────────────
CALIB_HTML = r"""<!DOCTYPE html>
<html lang="id" class="dark">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Kalibrasi Pembalik Telur</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet"/>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #121414; --surface: #1e2020; --surface-high: #282a2b;
    --primary: #c8c6c5; --tertiary: #78dc77; --outline: #444748;
    --on-surface: #e2e2e2; --on-surface-var: #c4c7c7; --error: #ffb4ab;
  }
  body { background: var(--bg); color: var(--on-surface); font-family: 'Inter', sans-serif;
         min-height: 100vh; padding: 16px; }
  h1 { font-size: 20px; font-weight: 700; color: var(--tertiary); margin-bottom: 4px; }
  .subtitle { font-size: 12px; color: var(--on-surface-var); margin-bottom: 20px; }

  .card { background: var(--surface); border: 1px solid var(--outline);
           border-radius: 12px; padding: 16px; margin-bottom: 16px; }
  .card-title { font-size: 11px; font-weight: 700; letter-spacing: 0.08em;
                 text-transform: uppercase; color: var(--on-surface-var); margin-bottom: 12px; }

  .row { display: flex; align-items: center; justify-content: space-between;
          margin-bottom: 10px; gap: 12px; }
  label { font-size: 13px; color: var(--on-surface-var); flex: 1; }
  .inp-wrap { display: flex; align-items: center; gap: 6px; }
  input[type=number] {
    width: 80px; background: var(--surface-high); border: 1px solid var(--outline);
    border-radius: 6px; padding: 8px 10px; color: var(--on-surface);
    font-family: 'JetBrains Mono', monospace; font-size: 15px; font-weight: 700;
    text-align: center; outline: none;
  }
  input[type=number]:focus { border-color: var(--tertiary); }
  .unit { font-size: 11px; color: var(--on-surface-var); }

  .preview { background: var(--surface-high); border-radius: 8px; padding: 10px 12px;
              font-size: 12px; color: var(--on-surface-var); margin-top: 4px; }
  .preview b { color: var(--tertiary); font-family: 'JetBrains Mono', monospace; }

  .btn-row { display: flex; gap: 10px; margin-top: 4px; }
  button {
    flex: 1; height: 52px; border: none; border-radius: 8px; font-size: 14px;
    font-weight: 700; cursor: pointer; transition: opacity 0.15s, transform 0.1s;
    letter-spacing: 0.04em;
  }
  button:active { transform: scale(0.97); }
  .btn-start { background: var(--tertiary); color: #00390a; }
  .btn-stop  { background: #ffb4ab; color: #690005; }
  .btn-up    { background: var(--surface-high); color: var(--primary); border: 1px solid var(--outline); }
  .btn-down  { background: var(--surface-high); color: var(--primary); border: 1px solid var(--outline); }
  button:disabled { opacity: 0.4; cursor: not-allowed; }

  .status-box {
    background: var(--surface-high); border-radius: 10px; padding: 14px 16px;
    border: 1px solid var(--outline); font-family: 'JetBrains Mono', monospace;
  }
  .status-state { font-size: 28px; font-weight: 700; color: var(--tertiary); }
  .status-state.idle { color: var(--on-surface-var); }
  .status-state.down { color: #7fd4ff; }
  .status-meta { font-size: 11px; color: var(--on-surface-var); margin-top: 4px; }

  .seq-visual {
    display: flex; flex-direction: column; gap: 4px; margin-top: 10px;
  }
  .seq-step { display: flex; align-items: center; gap: 8px; font-size: 12px;
               opacity: 0.4; transition: opacity 0.3s; }
  .seq-step.active { opacity: 1; color: var(--tertiary); font-weight: 600; }
  .seq-step.done { opacity: 0.6; color: var(--on-surface-var); }
  .seq-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor;
              flex-shrink: 0; }
  .seq-step.active .seq-dot { animation: pulse 1s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }

  .log { background: #0d0e0f; border-radius: 8px; padding: 10px 12px; margin-top: 8px;
          font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #78dc77;
          max-height: 90px; overflow-y: auto; }
  .log-err { color: var(--error); }

  .timer-bar { height: 4px; background: var(--outline); border-radius: 2px; margin-top: 8px;
                overflow: hidden; }
  .timer-fill { height: 100%; background: var(--tertiary); width: 0%; transition: width 0.1s linear; }
</style>
</head>
<body>
<h1>⚙ Pembalik Telur — Kalibrasi</h1>
<p class="subtitle">Atur timing dan test langsung via API Raspi</p>

<!-- Status -->
<div class="card" id="card-status">
  <div class="card-title">Status Motor</div>
  <div class="status-box">
    <div class="status-state idle" id="st-state">IDLE</div>
    <div class="status-meta" id="st-meta">Menunggu perintah...</div>
    <div class="timer-bar"><div class="timer-fill" id="timer-fill"></div></div>
  </div>
  <div class="seq-visual" id="seq-visual" style="display:none">
    <div class="seq-step" id="sq0"><span class="seq-dot"></span>Tengah → Atas</div>
    <div class="seq-step" id="sq1"><span class="seq-dot"></span>Siklus Atas ↔ Bawah</div>
    <div class="seq-step" id="sq2"><span class="seq-dot"></span>Atas → Tengah</div>
    <div class="seq-step" id="sq3"><span class="seq-dot"></span>Selesai</div>
  </div>
</div>

<!-- Timing Config -->
<div class="card">
  <div class="card-title">Konfigurasi Timing</div>
  <div class="row">
    <label>Tengah → Atas / Atas → Tengah</label>
    <div class="inp-wrap">
      <input type="number" id="t_edge" value="3.0" min="0.5" max="10" step="0.1"/>
      <span class="unit">dtk</span>
    </div>
  </div>
  <div class="row">
    <label>Atas ↔ Bawah (per gerakan)</label>
    <div class="inp-wrap">
      <input type="number" id="t_full" value="7.5" min="1" max="30" step="0.1"/>
      <span class="unit">dtk</span>
    </div>
  </div>
  <div class="row">
    <label>Jumlah Siklus Bolak-Balik</label>
    <div class="inp-wrap">
      <input type="number" id="n_cycles" value="3" min="1" max="10" step="1"/>
      <span class="unit">kali</span>
    </div>
  </div>
  <div class="preview" id="preview">Total: menghitung...</div>
</div>

<!-- Kontrol -->
<div class="card">
  <div class="card-title">Kontrol</div>
  <div class="btn-row">
    <button class="btn-start" id="btn-start" onclick="startSeq()">▶ MULAI SEQUENCE</button>
    <button class="btn-stop" id="btn-stop" onclick="stopMotor()" disabled>■ STOP</button>
  </div>
  <div class="btn-row" style="margin-top:8px">
    <button class="btn-up" onclick="manualMove('up')">↑ NAIK</button>
    <button class="btn-up" onclick="manualMove('stop')">■</button>
    <button class="btn-down" onclick="manualMove('down')">↓ TURUN</button>
  </div>
</div>

<!-- Log -->
<div class="card">
  <div class="card-title">Log</div>
  <div class="log" id="log">Siap.</div>
</div>

<script>
const API = 'http://' + location.hostname + ':5001';
let pollTimer = null;
let seqStart = null, seqTotal = 0;

function calcTotal() {
  const e = +document.getElementById('t_edge').value;
  const f = +document.getElementById('t_full').value;
  const n = +document.getElementById('n_cycles').value;
  const tot = e + n * 2 * f + e;
  document.getElementById('preview').innerHTML =
    `Tengah→Atas <b>${e}s</b> | Siklus <b>${n}×2×${f}s</b> | Atas→Tengah <b>${e}s</b> | Total: <b>${tot.toFixed(1)}s</b>`;
  return tot;
}
['t_edge','t_full','n_cycles'].forEach(id =>
  document.getElementById(id).addEventListener('input', calcTotal));
calcTotal();

function log(msg, err=false) {
  const el = document.getElementById('log');
  const t = new Date().toLocaleTimeString('id-ID');
  el.innerHTML += `<div class="${err?'log-err':''}">[${t}] ${msg}</div>`;
  el.scrollTop = el.scrollHeight;
}

async function startSeq() {
  const t_edge = +document.getElementById('t_edge').value;
  const t_full = +document.getElementById('t_full').value;
  const n_cycles = +document.getElementById('n_cycles').value;
  seqTotal = calcTotal();
  seqStart = Date.now();

  document.getElementById('btn-start').disabled = true;
  document.getElementById('btn-stop').disabled = false;
  document.getElementById('seq-visual').style.display = 'flex';
  setSeqStep(0);

  log(`▶ START: edge=${t_edge}s full=${t_full}s cycles=${n_cycles} total=${seqTotal.toFixed(1)}s`);
  try {
    const r = await fetch(`${API}/api/hydraulic/timed_oscillation`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({t_center_to_edge: t_edge, t_full, n_cycles})
    });
    const d = await r.json();
    log(`Response: state=${d.state} oscillating=${d.is_oscillating}`);
    startPoll();
    startTimerBar(seqTotal);
  } catch(e) {
    log('Error: ' + e.message, true);
    resetUI();
  }
}

async function stopMotor() {
  log('■ STOP dikirim');
  try {
    await fetch(`${API}/api/hydraulic/command`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({action:'stop'})
    });
  } catch(e) {}
  clearPoll();
  resetUI();
}

async function manualMove(dir) {
  log(`Manual: ${dir}`);
  try {
    await fetch(`${API}/api/hydraulic/command`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({action: dir})
    });
    startPoll();
  } catch(e) { log('Error: '+e.message, true); }
}

function startPoll() {
  clearPoll();
  pollTimer = setInterval(pollStatus, 500);
}

function clearPoll() {
  if(pollTimer) { clearInterval(pollTimer); pollTimer=null; }
}

async function pollStatus() {
  try {
    const r = await fetch(`${API}/api/hydraulic/status`);
    const d = await r.json();
    updateStatus(d);
    if(!d.is_oscillating && d.state==='IDLE') {
      clearPoll();
      resetUI();
      setSeqStep(3);
      log('✅ Sequence selesai, motor kembali ke IDLE');
    }
  } catch(e) {}
}

function updateStatus(d) {
  const el = document.getElementById('st-state');
  el.textContent = d.state;
  el.className = 'status-state ' + d.state.toLowerCase();
  document.getElementById('st-meta').textContent =
    `oscillating=${d.is_oscillating} | raw_max=${d.raw_max} raw_min=${d.raw_min} | ${d.backend}`;

  // Seq step visual
  if(d.is_oscillating) {
    const elapsed = (Date.now() - (seqStart||Date.now())) / 1000;
    const t_edge = +document.getElementById('t_edge').value;
    if(elapsed < t_edge) setSeqStep(0);
    else if(elapsed < seqTotal - t_edge) setSeqStep(1);
    else setSeqStep(2);
  }
}

function setSeqStep(n) {
  [0,1,2,3].forEach(i => {
    const el = document.getElementById('sq'+i);
    el.className = 'seq-step' + (i===n?' active':i<n?' done':'');
  });
}

let timerInterval = null;
function startTimerBar(total) {
  const fill = document.getElementById('timer-fill');
  const start = Date.now();
  if(timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    const pct = Math.min(100, (Date.now()-start)/1000/total*100);
    fill.style.width = pct+'%';
    if(pct >= 100) clearInterval(timerInterval);
  }, 100);
}

function resetUI() {
  document.getElementById('btn-start').disabled = false;
  document.getElementById('btn-stop').disabled = true;
  document.getElementById('timer-fill').style.width = '0%';
  if(timerInterval) clearInterval(timerInterval);
}

// Poll status saat load
pollStatus();
</script>
</body>
</html>"""

# Upload ke Raspi
sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(CALIB_HTML.encode()), '/home/tetasco1/Penetas-Telur/dist/kalibrasi.html')
sftp.close()
print('[OK] kalibrasi.html di-upload ke dist/')

# Tambah route Flask di app.py
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app_py = o.read().decode('utf-8','replace')

ROUTE = """@app.route('/kalibrasi')
def page_kalibrasi():
    \"\"\"Halaman kalibrasi timing pembalik telur\"\"\"
    return send_from_directory(DIST_DIR, 'kalibrasi.html')

"""

if '/kalibrasi' not in app_py:
    # Tambah setelah DIST_DIR assignment
    app_py = app_py.replace(
        "@app.route('/api/hydraulic/status'",
        ROUTE + "@app.route('/api/hydraulic/status'"
    )
    print('[OK] Route /kalibrasi ditambah ke app.py')
else:
    print('[INFO] Route /kalibrasi sudah ada')

sftp2 = rp.open_sftp()
sftp2.putfo(io.BytesIO(app_py.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp2.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/app.py && echo SYNTAX_OK', 'Syntax check')

# Restart
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
chan = rp.get_transport().open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1); chan.close()
print('[OK] Restart')
time.sleep(7)

ras('curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/kalibrasi', 'Test /kalibrasi route')
rp.close()

print('\n✅ Halaman kalibrasi siap!')
print('   Buka di browser: http://192.168.1.27:5001/kalibrasi')
