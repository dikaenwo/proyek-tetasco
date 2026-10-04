"""
deploy_auto_control.py — Upload auto_control.py & restart backend di VPS telur
"""
import paramiko, time

HOST = "192.168.1.14"
USER = "telur"
PASS = "telur"

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect(HOST, 22, USER, PASS, timeout=15)

# Upload auto_control.py ke server
sftp = sv.open_sftp()
sftp.put(
    r"d:\Proyek Penetas Telur\mqtt-setup\backend\auto_control.py",
    "/home/telur/tetasco-connect/backend/auto_control.py"
)
sftp.put(
    r"d:\Proyek Penetas Telur\mqtt-setup\backend\main.py",
    "/home/telur/tetasco-connect/backend/main.py"
)
sftp.close()
print("[1] File auto_control.py & main.py berhasil diupload.")

# Restart backend container
def run(cmd):
    i, o, e = sv.exec_command(cmd)
    out = o.read().decode()
    err = e.read().decode()
    if out: print(out)
    if err: print("[STDERR]", err)
    return out

time.sleep(1)
print("\n[2] Merestart backend container...")
run("cd ~/tetasco-connect && docker compose restart backend")

time.sleep(5)
print("\n[3] Cek status container...")
run("cd ~/tetasco-connect && docker compose ps")

print("\n[4] Cek log backend (5 detik terakhir)...")
run("cd ~/tetasco-connect && docker compose logs backend --tail=20")

sv.close()
print("\nDeploy auto control selesai!")
