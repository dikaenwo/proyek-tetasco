import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(cmd, lbl='', timeout=15):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)')
    return out

# Baca full main.py
i,o,e = sv.exec_command('cat ~/tetasco-connect/backend/main.py')
main_py = o.read().decode('utf-8','replace')
print(f'main.py: {len(main_py)} chars, {main_py.count(chr(10))} lines')
print('--- IMPORTS & AWAL ---')
print(main_py[:2000])
print('\n--- AKHIR ---')
print(main_py[-500:])

sv.close()
