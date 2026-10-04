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
print(f'File size: {len(src)} chars')

# ══════════════════════════════════════════════════════════════════
# Cek safety cutoff code yang ada
# ══════════════════════════════════════════════════════════════════
idx = src.find('JIKA SLIDER OFF')
if idx >= 0:
    print('\nSafety cutoff section:')
    print(src[idx:idx+400])
else:
    idx2 = src.find('Safety Cutoff')
    if idx2 >= 0:
        print('\nSafety Cutoff section:')
        print(src[max(0,idx2-100):idx2+400])

rp.close()
