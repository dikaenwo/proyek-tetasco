import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip())
    return o

# Lihat apa yang cloud_sync lakukan
r('head -60 ~/Penetas-Telur/backend/hardware/cloud_sync.py', 'cloud_sync.py head')
r('grep -n "mqtt\\|MQTT\\|paho\\|publish\\|subscribe\\|topic" ~/Penetas-Telur/backend/hardware/cloud_sync.py', 'cloud_sync MQTT usage')

# Cek MQTT credentials dari config
r('cat ~/Penetas-Telur/backend/hardware/cloud_sync.py | grep -E "config|tetasco_id|cloud_base|mqtt|user|pass|broker" | head -20', 'cloud_sync config')

# Cek apakah paho-mqtt terinstall
r('python3 -c "import paho.mqtt.client as mqtt; print(\"paho-mqtt: OK\", mqtt.__version__ if hasattr(mqtt,\"__version__\") else \"installed\")" 2>&1', 'paho-mqtt installed?')

rp.close()
