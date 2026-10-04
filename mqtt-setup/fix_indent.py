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

i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')

# Fix: return di dalam except → pindah ke luar try/except
# Bug: 
#     except Exception as _qe:
#         pass
#         return DeviceCommandResponse(   ← SALAH (inside except)
# Fix:
#     except Exception as _qe:
#         pass
#     return DeviceCommandResponse(       ← BENAR (outside try/except)

BUGGY = (
    '    except Exception as _qe:\n'
    '        pass\n'
    '        return DeviceCommandResponse(\n'
    '        success=True,\n'
    '        device_id=device_id,\n'
    '        actuator=actuator,\n'
    '        state=state,\n'
    '        mqtt_sent=mqtt_sent,\n'
    '        message=f\"{actuator.upper()} {\'ON\' if state else \'OFF\'} — perintah dikirim ke {device_id}\",\n'
    '    )\n'
)

FIXED = (
    '    except Exception as _qe:\n'
    '        pass\n'
    '    return DeviceCommandResponse(\n'
    '        success=True,\n'
    '        device_id=device_id,\n'
    '        actuator=actuator,\n'
    '        state=state,\n'
    '        mqtt_sent=mqtt_sent,\n'
    '        message=f\"{actuator.upper()} {\'ON\' if state else \'OFF\'} — perintah dikirim ke {device_id}\",\n'
    '    )\n'
)

if BUGGY in main_py:
    main_py = main_py.replace(BUGGY, FIXED, 1)
    print('[OK] Indentasi return diperbaiki (keluar dari except block)')
else:
    # Coba deteksi pola lain
    print('[DEBUG] Pattern not found, scanning lines 154-170...')
    lines = main_py.split('\n')
    for i2, l in enumerate(lines[153:172], 154):
        print(f'{i2}: {repr(l)}')
    # Manual fix dengan line replacement
    for i2, l in enumerate(lines):
        if '        return DeviceCommandResponse(' in l and i2 > 150 and i2 < 175:
            print(f'Found at line {i2+1}: {repr(l)}')
            # Ganti 8-space indent → 4-space
            lines[i2] = l.replace('        return DeviceCommandResponse(', '    return DeviceCommandResponse(')
            # Fix baris berikutnya juga (argumen DeviceCommandResponse)
            for j in range(i2+1, min(i2+10, len(lines))):
                if lines[j].startswith('        ') and not lines[j].startswith('            '):
                    lines[j] = '    ' + lines[j][4:]  # dedent 4 spasi
                elif lines[j].strip() == ')' or lines[j].strip().startswith(')'):
                    break
            main_py = '\n'.join(lines)
            print('[OK] Manual line fix applied')
            break

# Verifikasi baris 154-170
lines2 = main_py.split('\n')
print('\n[Lines 154-172 setelah fix]:')
for i2, l in enumerate(lines2[153:172], 154):
    print(f'{i2}: {l}')

# Deploy
sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.putfo(io.BytesIO(main_py.encode()), '/tmp/main_indent_fix.py')
sftp.close()
srv('docker cp /tmp/main_indent_fix.py tetasco-backend:/app/main.py && echo ok', 'Deploy')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart', t=25)
time.sleep(12)
srv('curl -s http://localhost:8000/api/health', 'Health')

result = srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", 'Fan ON')
if '"success":true' in result:
    print('\n✅ CONTROL BERFUNGSI SEMPURNA!')
else:
    srv('docker logs tetasco-backend --tail 10 2>&1', 'Error log')

time.sleep(1)
srv('curl -s http://localhost:8000/api/tetasco/1/pending-commands', 'Pending commands')
srv('curl -s http://localhost:8000/api/tetasco/1/sensor', 'Sensor data')

sv.close()
print('\n✅ Done!')
