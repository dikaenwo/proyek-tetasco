import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/src/pages/DasborUtama.jsx')
content = o.read().decode()

# Look for fetchData logic
start = content.find('const fetchData = async () =>')
end = content.find('fetchData();', start)

if start != -1 and end != -1:
    print(content[start:end])
else:
    print("Could not find fetchData")

rp.close()
