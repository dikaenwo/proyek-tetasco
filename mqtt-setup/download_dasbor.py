import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/src/pages/DasborUtama.jsx')
content = o.read().decode()
with open("d:\\Proyek Penetas Telur\\mqtt-setup\\DasborUtama.jsx", "w", encoding="utf-8") as f:
    f.write(content)

rp.close()
print("Downloaded DasborUtama.jsx")
