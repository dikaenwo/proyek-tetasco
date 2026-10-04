import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/src/pages/DasborUtama.jsx')
content = o.read().decode('utf-8', 'replace')

# 1. Fix null values on render (toFixed)
content = content.replace('{tempVal.toFixed(1)}', '{tempVal != null && !isNaN(tempVal) ? Number(tempVal).toFixed(1) : "--"}')
content = content.replace('{targetTemp.toFixed(1)}', '{targetTemp != null && !isNaN(targetTemp) ? Number(targetTemp).toFixed(1) : "--"}')
content = content.replace('{Math.round(targetHum)}', '{targetHum != null && !isNaN(targetHum) ? Math.round(Number(targetHum)) : "--"}')
content = content.replace('{Math.round(humVal)}', '{humVal != null && !isNaN(humVal) ? Math.round(Number(humVal)) : "--"}')

# 2. Fix undefined setSensorType in fetchData
content = content.replace('if (sensor.sensor !== undefined) setSensorType(sensor.sensor);', '// if (sensor.sensor !== undefined) setSensorType(sensor.sensor);')

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(content.encode()), '/home/tetasco1/Penetas-Telur/src/pages/DasborUtama.jsx')
sftp.close()

# Rebuild
print("Rebuilding Raspi HMI...")
i,o,e = rp.exec_command('cd ~/Penetas-Telur && npm run build')
print(o.read().decode())
print(e.read().decode())

# Refresh browser
rp.exec_command('export DISPLAY=:0 && xdotool key F5')

rp.close()
print("Done!")
