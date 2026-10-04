import paramiko, sys, os, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

src_dir = r"d:\Proyek Penetas Telur\TernakTelur-Web"
zip_path = r"d:\Proyek Penetas Telur\mqtt-setup\web.zip"

print(f"Zipping {src_dir}...")
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, src_dir)
            zipf.write(file_path, arcname)

print("Connecting to VPS 192.168.1.14...")
sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

print("Uploading web.zip...")
sftp = sv.open_sftp()
sftp.put(zip_path, '/home/telur/tetasco-connect/web.zip')
sftp.close()

print("Extracting on VPS...")
# Hapus frontend yang lama, buat baru, unzip
cmd = (
    "cd ~/tetasco-connect && "
    "rm -rf frontend/* && "
    "unzip -o web.zip -d frontend/ && "
    "rm web.zip"
)
i, o, e = sv.exec_command(cmd)
print(o.read().decode())
print(e.read().decode())

sv.close()
print("Done! Web deployed to https://tetasco.my.id/")
