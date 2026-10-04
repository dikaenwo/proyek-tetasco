import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

NEW_SHT20_SENSOR = """import time
import os
import glob
import serial
import subprocess
import logging

logger = logging.getLogger(__name__)
BAUDRATE = 9600
REQ_CMD = bytes.fromhex("01 04 00 01 00 02 20 0B")

def get_candidate_ports():
    candidates = sorted(glob.glob("/dev/ttyUSB*"))
    candidates += sorted(glob.glob("/dev/ttyACM*"))
    if os.path.exists("/dev/ttyAMA0"):
        candidates.append("/dev/ttyAMA0")
    if os.path.exists("/dev/ttyS0"):
        candidates.append("/dev/ttyS0")
    if os.path.exists("/dev/ttyAMA10"):
        candidates.append("/dev/ttyAMA10")
    return candidates

class SHT20RS485:
    def __init__(self):
        self.port = None
        self.ser = None
        self.is_connected = False
        self.last_error = None
        self.last_temp = None
        self.last_hum = None
        self.last_success_time = 0
        self.consecutive_fails = 0
        self.has_lgpio = False
        self.de_re_pin = "Auto (No GPIO)"
        self.active_cmd_index = 0
        self._init_sensor()

    def _init_sensor(self):
        candidates = get_candidate_ports()
        if not candidates:
            self.last_error = "Tidak ada port serial yang tersedia (/dev/ttyUSB* atau /dev/ttyAMA*)"
            self.is_connected = False
            return

        self.port = candidates[0]

        if self.ser and self.ser.is_open:
            try: self.ser.close()
            except: pass

        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=BAUDRATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.6
            )
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.is_connected = True
            self.last_error = None
            logger.info(f"Serial {self.port} berhasil dibuka @ {BAUDRATE} baud (Auto-direction).")
        except Exception as e:
            self.last_error = f"Gagal buka serial {self.port}: {e}"
            logger.warning(self.last_error)
            self.is_connected = False

    def read(self):
        if not self.is_connected or not self.ser or not self.ser.is_open:
            self._init_sensor()
            if not self.is_connected or not self.ser:
                return None, None, False

        for attempt in range(2):
            try:
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()

                t_send = time.time()
                # 1. Kirim request Modbus (USB converter: tidak perlu set DE/RE manual)
                self.ser.write(REQ_CMD)
                self.ser.flush()

                # 2. Tunggu respon
                t_wait_start = time.time()
                while self.ser.in_waiting < 7 and (time.time() - t_wait_start) < 0.15:
                    time.sleep(0.003)
                time.sleep(0.005)

                # 3. Baca seluruh respon buffer
                resp = self.ser.read(max(self.ser.in_waiting, 9))
                
                temp = None
                hum = None

                # 4. Cari frame Modbus valid di dalam buffer
                for idx in range(len(resp) - 6):
                    if resp[idx] == 1 and resp[idx+1] == 4 and resp[idx+2] == 4:
                        if idx + 9 <= len(resp):
                            raw_t = int.from_bytes(resp[idx+3:idx+5], "big", signed=True)
                            raw_h = int.from_bytes(resp[idx+5:idx+7], "big", signed=False)
                            t_val = raw_t / 10.0
                            h_val = raw_h / 10.0
                            if (0.0 <= t_val <= 80.0) and (0.0 <= h_val <= 100.0):
                                temp = t_val
                                hum = h_val
                                break
                    elif resp[idx] == 4 and resp[idx+1] == 4 and idx + 8 <= len(resp):
                        raw_t = int.from_bytes(resp[idx+2:idx+4], "big", signed=True)
                        raw_h = int.from_bytes(resp[idx+4:idx+6], "big", signed=False)
                        t_val = raw_t / 10.0
                        h_val = raw_h / 10.0
                        if (0.0 <= t_val <= 80.0) and (0.0 <= h_val <= 100.0):
                            temp = t_val
                            hum = h_val
                            break

                if temp is not None and hum is not None:
                    self.last_temp = temp
                    self.last_hum = hum
                    self.last_success_time = time.time()
                    self.last_error = None
                    self.consecutive_fails = 0
                    return temp, hum, True
                
                if attempt == 0:
                    time.sleep(0.05)

            except Exception as e:
                self.last_error = f"Exception saat read (attempt {attempt+1}): {e}"
                if attempt == 0:
                    time.sleep(0.05)

        self.consecutive_fails += 1
        return None, None, False

    def close(self):
        if self.ser and self.ser.is_open:
            try: self.ser.close()
            except: pass

sht20_sensor = SHT20RS485()
"""

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(NEW_SHT20_SENSOR.encode()), '/home/tetasco1/Penetas-Telur/backend/sensors/sht20_sensor.py')
sftp.close()

print("Restarting backend app on Raspi...")
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
chan = rp.get_transport().open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1)
chan.close()
rp.close()
print("Done! SHT20 algo updated and backend restarted.")
