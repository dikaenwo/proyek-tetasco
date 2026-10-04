"""fix_is_claimed.py — Fix endpoint is-claimed di server pusat"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(c, cmd, lbl='', timeout=30):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace')
    err = e.read().decode('utf-8','replace')
    sys.stdout.write(out or err); sys.stdout.flush()
    return out

# Cek apakah endpoint sudah ada di main.py
r(cs, 'grep -n "is-claimed\\|is_claimed" /home/telur/tetasco-connect/backend/main.py | head -10',
  '1. Cek is-claimed di main.py')

# Cek container
r(cs, 'docker ps | grep backend', '2. Container status')

# Cek di dalam container
r(cs, 'docker exec tetasco-backend grep -n "is-claimed\\|is_claimed" /app/main.py 2>/dev/null | head -5',
  '3. Cek di dalam container')

# Test endpoint langsung
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/is-claimed', '4. Test is-claimed endpoint')
r(cs, 'curl -s https://tetasco.my.id/api/tetasco/1/is-claimed', '5. Test via domain')

# Cek routing pattern di main.py (mungkin FastAPI tidak redirect trailing slash)
r(cs, 'docker exec tetasco-backend python3 -c "import main; print([r.path for r in main.app.routes])" 2>/dev/null | tr "," "\n" | grep -i claim',
  '6. Registered routes')

cs.close()
print('\nDone!', flush=True)
