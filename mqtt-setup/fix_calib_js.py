import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/dist/kalibrasi.html')
html = o.read().decode('utf-8','replace')

# Fix: hapus referensi t_full yang sudah tidak ada, pakai t_down/t_up
OLD_START = """async function startSeq() {
  const t_edge = +document.getElementById('t_edge').value;
  const t_full = +document.getElementById('t_full').value;
  const n_cycles = +document.getElementById('n_cycles').value;
  seqTotal = calcTotal();
  seqStart = Date.now();"""

NEW_START = """async function startSeq() {
  const t_edge = +document.getElementById('t_edge').value;
  const t_down = +document.getElementById('t_down').value;
  const t_up   = +document.getElementById('t_up').value;
  const n_cycles = +document.getElementById('n_cycles').value;
  seqTotal = calcTotal();
  seqStart = Date.now();"""

if OLD_START in html:
    html = html.replace(OLD_START, NEW_START, 1)
    print('[OK] t_full → t_down/t_up di startSeq()')
else:
    # Coba variasi
    import re
    m = re.search(r'async function startSeq\(\)[^{]+\{[^\n]+\n[^\n]+\n[^\n]+\n[^\n]+\n[^\n]+', html)
    if m:
        print('[DEBUG] startSeq found:\n', m.group())
    else:
        print('[WARN] startSeq tidak ditemukan')

# Pastikan tidak ada referensi getElementById('t_full') yang tersisa
remaining = [i for i,l in enumerate(html.split('\n')) if "getElementById('t_full')" in l]
if remaining:
    print(f'[WARN] Masih ada referensi t_full di baris: {remaining}')
    for ln in remaining:
        lines = html.split('\n')
        print(f'  L{ln}: {lines[ln]}')
else:
    print('[OK] Tidak ada referensi t_full tersisa')

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(html.encode()), '/home/tetasco1/Penetas-Telur/dist/kalibrasi.html')
sftp.close()
print('[OK] kalibrasi.html di-upload')
rp.close()
print('\n✅ Refresh halaman kalibrasi — tombol seharusnya sudah bisa!')
