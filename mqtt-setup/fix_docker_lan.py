import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# Konfirmasi: container tidak bisa reach Raspi
srv("docker exec tetasco-backend curl -s --connect-timeout 2 http://192.168.1.27:5001/api/actuators 2>&1 | head -c 150", 'Docker → Raspi test')
# Host bisa?
srv("curl -s --connect-timeout 2 http://192.168.1.27:5001/api/actuators 2>&1 | head -c 100", 'Host → Raspi test')

# Baca docker-compose.yml
i,o,e = sv.exec_command('cat ~/tetasco-connect/docker-compose.yml')
dc = o.read().decode('utf-8','replace')
print(f'\ndocker-compose.yml:\n{dc[:2000]}')

# Cek apakah bisa tambah extra_hosts atau network_mode
# Opsi 1: extra_hosts — tambahkan raspi ke /etc/hosts container
# Opsi 2: network_mode: host — tapi akan konflik dengan ports mapping

# Opsi terbaik: extra_hosts (tetap bisa pakai ports mapping)
# Tambahkan di service backend:
# extra_hosts:
#   - "raspi-lemari:192.168.1.27"
# Lalu ubah RASPI_LOCAL_IPS di main.py pakai hostname

# TAPI lebih simpel: cukup pastikan container routing ke LAN
# Docker bridge by default bisa reach LAN kalau iptables FORWARD enabled

srv('sysctl net.ipv4.ip_forward', 'IP Forward')
srv('iptables -L FORWARD -n | head -5', 'iptables FORWARD')

# Coba ping Raspi dari container
srv("docker exec tetasco-backend ping -c 1 192.168.1.27 2>&1 | tail -3", 'Container ping Raspi')

# Fix: tambahkan route jika perlu, atau pakai host networking
# Paling aman: jalankan forward via host menggunakan socat/nginx atau
# tambahkan host.docker.internal → gunakan host network untuk curl ke Raspi

# Cara paling cepat: gunakan host network KHUSUS untuk curl ke Raspi
# Tambahkan endpoint proxy di host yang forward ke Raspi
# Atau: ubah docker network ke host mode

# Cek docker-compose backend service
if 'network_mode' in dc:
    print('[INFO] network_mode sudah ada')
else:
    # Opsi: tambah --network=host ke backend saja lewat env var / restart dengan host network
    # Tapi ini akan break ports mapping
    # BETTER: tambah iptables rule agar container bisa reach LAN
    
    # Check container IP
    srv("docker inspect tetasco-backend --format '{{.NetworkSettings.Networks}}' 2>&1 | head -c 200", 'Container network')
    srv("docker exec tetasco-backend ip route show 2>&1", 'Container routes')

sv.close()
