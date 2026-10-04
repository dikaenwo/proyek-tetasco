#!/usr/bin/env python3
"""
display_qr.py — Tampilkan QR Code di Monitor HDMI Raspi Lemari
═══════════════════════════════════════════════════════════════
Flow:
  1. Fetch claim token dari server (tetasco.my.id)
  2. Generate QR dari token
  3. Tampilkan full-screen di HDMI dengan info device
  4. Refresh tiap 60 detik (agar suhu real-time update)

Dependencies (install di Raspi):
  pip3 install qrcode pillow pygame requests

Usage:
  python3 display_qr.py                    # auto-detect lemari ID dari env
  TETASCO_ID=3 python3 display_qr.py       # manual set lemari ID
"""

import os
import sys
import time
import threading
import logging

# ─── Config ─────────────────────────────────────────────────────────────────
TETASCO_ID   = int(os.getenv("TETASCO_ID", "1"))
SERVER_URL   = os.getenv("TETASCO_SERVER", "https://tetasco.my.id")
DEVICE_NAME  = os.getenv("TETASCO_NAME", f"Lemari #{TETASCO_ID}")
REFRESH_SEC  = int(os.getenv("QR_REFRESH_SEC", "30"))   # refresh sensor tiap N detik
DISPLAY_W    = int(os.getenv("DISPLAY_W", "800"))
DISPLAY_H    = int(os.getenv("DISPLAY_H", "480"))
FULLSCREEN   = os.getenv("FULLSCREEN", "1") == "1"

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("display_qr")

# ─── Import dependencies ─────────────────────────────────────────────────────
try:
    import requests
except ImportError:
    print("Install: pip3 install requests"); sys.exit(1)

try:
    import qrcode
    from qrcode.image.pil import PilImage
except ImportError:
    print("Install: pip3 install qrcode[pil]"); sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Install: pip3 install pillow"); sys.exit(1)

try:
    import pygame
except ImportError:
    print("Install: pip3 install pygame"); sys.exit(1)


# ─── State ───────────────────────────────────────────────────────────────────
state = {
    "token":       None,
    "qr_data":     None,
    "temperature": None,
    "humidity":    None,
    "online":      False,
    "ip":          "...",
    "last_fetch":  0,
    "error":       None,
}


# ─── Data Fetching ───────────────────────────────────────────────────────────
def fetch_device_info():
    """Fetch claim token + sensor data dari server."""
    try:
        # 1. Claim token
        r = requests.get(
            f"{SERVER_URL}/api/tetasco/{TETASCO_ID}/claim-token",
            timeout=8
        )
        if r.ok:
            data = r.json()
            state["token"]   = data.get("token")
            state["qr_data"] = data.get("qrData")
            state["error"]   = None
        else:
            state["error"] = f"Token error: HTTP {r.status_code}"

        # 2. Sensor real-time
        s = requests.get(
            f"{SERVER_URL}/api/tetasco/{TETASCO_ID}/sensor",
            timeout=8
        )
        if s.ok:
            sdata = s.json()
            state["temperature"] = sdata.get("temperature")
            state["humidity"]    = sdata.get("humidity")
            state["online"]      = sdata.get("online", False)

        # 3. IP lokal
        import socket
        s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s2.connect(("8.8.8.8", 80))
        state["ip"] = s2.getsockname()[0]
        s2.close()

        state["last_fetch"] = time.time()
        log.info(f"Data refreshed: temp={state['temperature']} token={state['token']}")

    except Exception as e:
        state["error"] = str(e)
        log.warning(f"Fetch error: {e}")


def fetch_loop():
    """Background thread: fetch data tiap REFRESH_SEC."""
    while True:
        fetch_device_info()
        time.sleep(REFRESH_SEC)


# ─── QR Code Generation ──────────────────────────────────────────────────────
def make_qr_image(qr_data: str, size: int) -> Image.Image:
    """Generate QR code sebagai PIL Image."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1A2B1C", back_color="#FFFFFF")
    img = img.convert("RGB")
    img = img.resize((size, size), Image.LANCZOS)
    return img


# ─── Screen Rendering ────────────────────────────────────────────────────────
# Colors (dark greenish theme sesuai app)
BG         = (26,  43, 28)   # #1A2B1C
GREEN      = (47, 107, 63)   # #2F6B3F
GREEN_LIGHT= (61, 138, 82)   # #3D8A52
WHITE      = (255, 255, 255)
GRAY       = (138, 158, 140) # #8A9E8C
YELLOW     = (245, 158, 11)
RED        = (239,  68,  68)

def try_font(size):
    try:
        return pygame.font.SysFont("Ubuntu,DejaVuSans,Arial", size, bold=False)
    except:
        return pygame.font.Font(None, size)

def try_font_bold(size):
    try:
        return pygame.font.SysFont("Ubuntu,DejaVuSans,Arial", size, bold=True)
    except:
        return pygame.font.Font(None, size + 4)


def render(screen: pygame.Surface):
    W, H = screen.get_size()
    screen.fill(BG)

    # ── Header ──────────────────────────────────────────────────
    header_h = 64
    pygame.draw.rect(screen, GREEN, (0, 0, W, header_h))
    f_title = try_font_bold(28)
    f_sub   = try_font(18)

    title_surf = f_title.render("TETASCO CONNECT", True, WHITE)
    screen.blit(title_surf, (24, 10))

    device_surf = f_sub.render(f"{DEVICE_NAME}  •  lemari-{TETASCO_ID}", True, (200, 230, 200))
    screen.blit(device_surf, (24, 40))

    # Online dot
    online_color = (74, 222, 128) if state["online"] else YELLOW
    pygame.draw.circle(screen, online_color, (W - 40, 32), 8)
    pygame.draw.circle(screen, BG, (W - 40, 32), 5 if not state["online"] else 0)

    # ── QR Area (kanan tengah) ───────────────────────────────────
    qr_size = min(H - header_h - 60, W // 2 - 80)
    qr_x = W - qr_size - 48
    qr_y = header_h + (H - header_h - qr_size) // 2

    if state["qr_data"] and state["token"]:
        try:
            qr_img = make_qr_image(state["qr_data"], qr_size)
            # White padding
            pad = 12
            pygame.draw.rect(screen, WHITE, (qr_x - pad, qr_y - pad, qr_size + pad*2, qr_size + pad*2), border_radius=12)
            # QR image
            qr_surf = pygame.image.fromstring(qr_img.tobytes(), qr_img.size, "RGB")
            screen.blit(qr_surf, (qr_x, qr_y))
        except Exception as e:
            log.warning(f"QR render error: {e}")
            f_err = try_font(18)
            screen.blit(f_err.render("Generating QR...", True, GRAY), (qr_x, qr_y + qr_size // 2))
    else:
        f_loading = try_font(20)
        msg = state.get("error", "Menghubungi server...")
        screen.blit(f_loading.render(msg[:40], True, GRAY), (qr_x, qr_y + qr_size // 2))

    # ── Left Panel: Info + Instructions ─────────────────────────
    left_w = W - qr_size - 96
    y = header_h + 24

    # Suhu & Kelembaban
    f_big   = try_font_bold(52)
    f_unit  = try_font(24)
    f_label = try_font(14)
    f_med   = try_font(20)
    f_small = try_font(16)

    # Temperature box
    temp_str = f"{state['temperature']:.1f}" if state["temperature"] is not None else "--.-"
    humid_str = f"{state['humidity']:.1f}" if state["humidity"] is not None else "--.-"

    box_w = (left_w - 32) // 2
    for i, (label, val, unit, color) in enumerate([
        ("SUHU", temp_str, "°C", (239, 68, 68)),
        ("LEMBAB", humid_str, "%", (59, 130, 246)),
    ]):
        bx = 16 + i * (box_w + 16)
        by = y
        # Box background
        pygame.draw.rect(screen, (36, 60, 38), (bx, by, box_w, 100), border_radius=12)
        lbl_s = f_label.render(label, True, (*(c//2+60 for c in color),))
        screen.blit(lbl_s, (bx + 12, by + 8))
        val_s = f_big.render(val, True, color)
        screen.blit(val_s, (bx + 12, by + 26))
        unit_s = f_unit.render(unit, True, color)
        screen.blit(unit_s, (bx + 12 + val_s.get_width(), by + 48))

    y += 120

    # ── Steps: cara scan ────────────────────────────────────────
    f_step_title = try_font_bold(20)
    f_step       = try_font(18)

    screen.blit(f_step_title.render("Cara Menghubungkan HP:", True, WHITE), (16, y))
    y += 32

    steps = [
        "1. Buka app TernakTelur di HP",
        "2. Ketuk  Tambah Inkubator",
        "3. Pilih  Scan QR Code",
        "4. Arahkan ke QR di sebelah kanan →",
        "5. Inkubator langsung terhubung! ✓",
    ]
    for step in steps:
        s = f_step.render(step, True, GRAY)
        screen.blit(s, (16, y))
        y += 26

    y += 12

    # ── Token ────────────────────────────────────────────────────
    if state["token"]:
        screen.blit(f_label.render("KODE KLAIM (jika scan QR gagal):", True, GRAY), (16, y))
        y += 18
        f_token = try_font_bold(32)
        token_s = f_token.render(state["token"], True, (245, 158, 11))
        screen.blit(token_s, (16, y))
        y += 44

    # ── IP & Server ──────────────────────────────────────────────
    screen.blit(f_small.render(f"IP: {state['ip']}   Server: {SERVER_URL}", True, (80, 100, 82)), (16, H - 32))

    # ── Bottom bar: last update ──────────────────────────────────
    if state["last_fetch"]:
        ago = int(time.time() - state["last_fetch"])
        bar_s = f_label.render(f"Update {ago}s lalu  •  Refresh tiap {REFRESH_SEC}s", True, (80, 100, 82))
        screen.blit(bar_s, (W // 2 - bar_s.get_width() // 2, H - 32))

    pygame.display.flip()


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    # Background fetch thread
    t = threading.Thread(target=fetch_loop, daemon=True)
    t.start()

    # Tunggu data pertama kali
    log.info("Menghubungi server, harap tunggu...")
    timeout = 0
    while state["token"] is None and timeout < 15:
        time.sleep(0.5); timeout += 0.5

    # Pygame setup
    os.environ.setdefault("SDL_FBDEV", "/dev/fb0")
    if FULLSCREEN:
        os.environ.setdefault("SDL_VIDEODRIVER", "x11")  # HDMI via X11

    pygame.init()
    pygame.mouse.set_visible(False)

    if FULLSCREEN:
        info = pygame.display.Info()
        screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((DISPLAY_W, DISPLAY_H))

    pygame.display.set_caption(f"Tetasco — {DEVICE_NAME}")
    clock = pygame.time.Clock()

    log.info(f"Display: {screen.get_size()}, fullscreen={FULLSCREEN}")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r:
                    fetch_device_info()  # manual refresh dengan tombol R

        render(screen)
        clock.tick(2)  # 2 FPS cukup untuk info statis

    pygame.quit()
    log.info("Display ditutup.")


if __name__ == "__main__":
    main()
