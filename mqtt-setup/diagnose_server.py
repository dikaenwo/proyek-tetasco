import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=15):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek isi main.py — apakah ada "app = FastAPI" atau "app = "
srv('docker exec tetasco-backend python3 -c "import main; print(type(main.app))" 2>&1', 'Import test')
srv('grep -n "^app " /home/telur/tetasco-connect/backend/main.py | head -5', 'app= declaration')
srv('grep -n "FastAPI\|app = " /home/telur/tetasco-connect/backend/main.py | head -10', 'FastAPI init')

# Cek syntax
srv('docker exec tetasco-backend python3 -m py_compile /app/main.py && echo SYNTAX_OK || echo SYNTAX_ERROR', 'Syntax check')

# Cek apakah file di container dan di host sinkron
srv('wc -l /home/telur/tetasco-connect/backend/main.py', 'File size host')
srv('docker exec tetasco-backend wc -l /app/main.py 2>/dev/null || echo "container might be stopped"', 'File size container')

# Lihat akhir file
srv('tail -30 /home/telur/tetasco-connect/backend/main.py', 'Tail main.py')

sv.close()
