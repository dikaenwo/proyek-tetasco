import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

print("Memaksa Chromium kembali ke halaman utama...")
# 1. Fokus ke Chromium
rp.exec_command('export DISPLAY=:0 && xdotool search --onlyvisible --class chromium windowfocus')
time.sleep(1)
# 2. Ketik URL dan tekan enter
cmd = 'export DISPLAY=:0 && xdotool key ctrl+l && xdotool type "http://127.0.0.1:5001/#/" && xdotool key Return'
rp.exec_command(cmd)

# Atau alternatif, jalankan chromium-browser url --kiosk
rp.exec_command('export DISPLAY=:0 && chromium-browser http://127.0.0.1:5001/#/ &')

rp.close()
print("Selesai")
