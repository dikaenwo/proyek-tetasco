import paramiko, sys, time
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

# Cek topic MQTT yang dipakai server untuk control
srv("docker exec tetasco-backend cat /app/mqtt_manager.py 2>/dev/null | grep -A5 'publish_command\\|topic\\|TOPIC' | head -40", 'MQTT publish topic')

# Kalau tidak ada mqtt_manager.py, cek di main.py
srv("docker exec tetasco-backend grep -n 'publish\\|topic\\|mqtt.*command\\|command.*mqtt' /app/main.py | head -20", 'MQTT in main.py')

# Cek MQTT broker accessible dari luar
srv("mosquitto_pub -h localhost -p 1883 -u server -P \$(grep MQTT_SERVER_PASS ~/tetasco-connect/.env | cut -d= -f2) -t 'test/ping' -m 'hello' 2>&1 || echo 'no mosquitto_pub on host'", 'MQTT broker test')

# Subscribe test (lihat topic apa yang dipublish server)
print('\n[MQTT sniff - kirim control command lalu lihat topic]')
srv("timeout 3 mosquitto_sub -h localhost -p 1883 -u server -P \$(grep MQTT_SERVER_PASS ~/tetasco-connect/.env | cut -d= -f2) -t '#' -v 2>&1 | head -20 &", 'Subscribe all topics')
time.sleep(1)
srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on 2>&1 | head -c 100", 'Fan ON trigger')
time.sleep(3)

sv.close()
