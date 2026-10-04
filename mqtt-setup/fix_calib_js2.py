import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/dist/kalibrasi.html')
html = o.read().decode('utf-8','replace')

# Ganti seluruh startSeq function dengan versi bersih
import re

# Temukan startSeq sampai function berikutnya
m = re.search(r'async function startSeq\(\) \{.*?\n\}', html, re.DOTALL)
if m:
    print('[FOUND] startSeq:')
    print(m.group()[:400])
    
    CLEAN_START_SEQ = """async function startSeq() {
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
    });
    const d = await r.json();
    log(`Response: state=${d.state} oscillating=${d.is_oscillating}`);
    startPoll();
    startTimerBar(seqTotal);
  } catch(e) {
    log('Error: ' + e.message, true);
    resetUI();
  }
}"""
    
    html = html[:m.start()] + CLEAN_START_SEQ + html[m.end():]
    print('[OK] startSeq() ditulis ulang bersih')
else:
    print('[ERR] startSeq tidak ditemukan via regex')

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(html.encode()), '/home/tetasco1/Penetas-Telur/dist/kalibrasi.html')
sftp.close()

# Verifikasi tidak ada t_full tersisa
remaining = [l.strip() for l in html.split('\n') if 't_full' in l and 'calcTotal' not in l]
print('[Sisa t_full]:', remaining if remaining else 'Tidak ada ✅')

rp.close()
print('\n✅ Refresh browser — tombol seharusnya jalan sekarang!')
