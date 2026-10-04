import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek nama-nama aktuator di GPIO controller
ras("grep -n 'actuator\\|ACTUATOR\\|relay\\|gpio\\|fan\\|mist\\|humid\\|lamp\\|heater\\|motor\\|uv' ~/Penetas-Telur/backend/hardware/gpio_controller.py | grep -i 'dict\\|map\\|\\'fan\\'|\\'mist\\'|\\'humid\\'|\\'lamp\\'|\\'heater\\'' | head -30", 'GPIO actuator names')
ras("grep -n 'def set_actuator\\|def get_all\\|self\\._relays\\|self\\.relays\\|RELAY\\|_map' ~/Penetas-Telur/backend/hardware/gpio_controller.py | head -20", 'GPIO relay map')
ras("sed -n '1,60p' ~/Penetas-Telur/backend/hardware/gpio_controller.py", 'GPIO controller top (relay definitions)')

# Test langsung: apakah set_actuator("humidifier") benar-benar mengubah relay?
print('\n=== Test: set_actuator("humidifier") vs ("mist_maker") ===')
ras("curl -s -X POST http://localhost:5001/api/actuators/humidifier -H 'Content-Type: application/json' -d '{\"state\":false}'", 'OFF via humidifier name')
time.sleep(0.5)
ras("curl -s http://localhost:5001/api/actuators | python3 -c \"import sys,json;d=json.load(sys.stdin);print('humidifier:',d.get('humidifier'),'mist_maker:',d.get('mist_maker'))\"", 'State setelah set humidifier=false')
ras("curl -s -X POST http://localhost:5001/api/actuators/mist_maker -H 'Content-Type: application/json' -d '{\"state\":false}'", 'OFF via mist_maker name')
time.sleep(0.5)
ras("curl -s http://localhost:5001/api/actuators | python3 -c \"import sys,json;d=json.load(sys.stdin);print('humidifier:',d.get('humidifier'),'mist_maker:',d.get('mist_maker'))\"", 'State setelah set mist_maker=false')

rp.close()
