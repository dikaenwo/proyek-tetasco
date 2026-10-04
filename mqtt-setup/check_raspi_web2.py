import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Baca 200 baris terakhir untuk lihat JS dan kontrol yang ada
ras('tail -200 ~/Penetas-Telur/Stich/stitch_smart_incubator_industrial_hmi/kontrol_rak_id_v3/code.html', 'Tail kontrol_rak')
# Cek di mana Flask serve file ini
ras('grep -n "kontrol_rak\|Stich\|stitch\|index" ~/Penetas-Telur/backend/app.py | head -15', 'Flask route untuk Stich')
# Cek apakah accessible via browser
ras('curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/', 'Flask root status')

rp.close()
