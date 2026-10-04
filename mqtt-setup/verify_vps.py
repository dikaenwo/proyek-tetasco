import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

# Check if locationSVG or speciesSVG still exist in VPS file
i,o,e = sv.exec_command('grep -n "locationSVG\\|speciesSVG\\|speciesEmoji\\|📍\\|🐔\\|🦆\\|🥚\\|🦢\\|🦃" ~/tetasco-connect/frontend/js/dashboard.js')
result = o.read().decode()
print("[Grep result in VPS dashboard.js]")
print(result if result else "CLEAN - tidak ada emoji/icon")

# Force nginx to serve fresh content by adding no-cache header
i,o,e = sv.exec_command('cat ~/tetasco-connect/nginx/nginx.conf | grep -i cache')
print("\n[Nginx cache config]")
print(o.read().decode())

sv.close()
