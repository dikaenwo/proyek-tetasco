import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=15):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek git history
srv('cd /home/telur/tetasco-connect && git log --oneline -5 2>/dev/null || echo "no git"', 'Git log')
srv('ls /home/telur/tetasco-connect/backend/', 'Backend dir')

# Cek apakah ada backup
srv('ls /home/telur/tetasco-connect/backend/*.bak 2>/dev/null || echo "no bak"', 'Backup files')

# Cek docker image — extract main.py dari image asli
srv('docker images | grep tetasco', 'Docker images')

# Coba ambil dari docker image layer (bukan container yg crash)
srv('docker create tetasco-backend:latest 2>/dev/null || docker create tetasco_tetasco-backend:latest 2>/dev/null | head -1', 'Create temp container')

# Cek git stash atau reflog
srv('cd /home/telur/tetasco-connect && git stash list 2>/dev/null | head -5', 'Git stash')
srv('cd /home/telur/tetasco-connect && git diff HEAD backend/main.py 2>/dev/null | head -20', 'Git diff main.py')

sv.close()
