import board
import busio
from adafruit_ssd1306 import SSD1306_I2C
from PIL import Image, ImageDraw, ImageFont
import psutil
import socket
import fcntl
import struct
import time
import subprocess
import os
import datetime
import re
import asyncio
from collections import deque

# Global shared variables
cpu_usage = 0.0
ram_usage = 0.0
tailscale_ping = None
ip_addr = "Brak IP"
uptime_seconds = 0

# Rolling buffers for averages
cpu_buffer = deque(maxlen=10)
ram_buffer = deque(maxlen=10)

def get_ip_sync(ifname='eth0'):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname.encode('utf-8')[:15])
        )[20:24])
    except Exception:
        return "Brak IP"

async def cpu_task():
    global cpu_usage
    while True:
        cpu = psutil.cpu_percent(interval=1)
        cpu_buffer.append(cpu)
        cpu_usage = sum(cpu_buffer) / len(cpu_buffer)
        await asyncio.sleep(0)  # yield control

async def ram_task():
    global ram_usage
    while True:
        ram = psutil.virtual_memory().percent
        ram_buffer.append(ram)
        ram_usage = sum(ram_buffer) / len(ram_buffer)
        await asyncio.sleep(1)

async def ip_task():
    global ip_addr
    while True:
        ip_addr = get_ip_sync()
        await asyncio.sleep(10)

async def tailscale_task():
    global tailscale_ping
    while True:
        try:
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", "4", "-W", "1", "100.100.100.100",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            if proc.returncode != 0:
                tailscale_ping = None
            else:
                times = []
                for line in stdout.decode().splitlines():
                    match = re.search(r'time=([\d\.]+)\s*ms', line)
                    if match:
                        times.append(float(match.group(1)))
                if times:
                    tailscale_ping = sum(times) / len(times)
                else:
                    tailscale_ping = None
        except Exception:
            tailscale_ping = None
        await asyncio.sleep(10)

async def uptime_task():
    global uptime_seconds
    while True:
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = int(float(f.readline().split()[0]))
        except Exception:
            uptime_seconds = 0
        await asyncio.sleep(5)

def format_uptime(screen_chars=14):
    """
    Zwraca sformatowany uptime mieszczący się w podanej liczbie znaków.
    """
    total = uptime_seconds
    s = total % 60
    m = (total // 60) % 60
    h = (total // 3600) % 24
    d = total // (3600 * 24)

    if total < 60:
        # Do 59s
        return f"Uptime: {s}s"
    elif total < 3600:
        # Do 59m 59s
        result = f"Uptime: {m}m {s}s"
        if len(result) <= screen_chars:
            return result
        return f"Uptime: {m}m"
    elif total < 86400:
        result = f"Uptime: {h}h {m}m {s}s"
        if len(result) <= screen_chars:
            return result
        elif len(f"Uptime: {h}h {m}m") <= screen_chars:
            return f"Uptime: {h}h {m}m"
        else:
            return f"Uptime: {h}h"
    else:
        result = f"Uptime: {d}d {h}h {m}m"
        if len(result) <= screen_chars:
            return result
        elif len(f"Uptime: {d}d {h}h") <= screen_chars:
            return f"Uptime: {d}d {h}h"
        else:
            return f"Uptime: {d}d"

async def display_task():
    i2c = busio.I2C(board.SCL, board.SDA)
    oled = SSD1306_I2C(128, 64, i2c)
    try:
        font = ImageFont.truetype("PixelOperator.ttf", 16)
    except:
        font = ImageFont.load_default()
    line_height = oled.height // 4

    while True:
        image = Image.new("1", (oled.width, oled.height))
        draw = ImageDraw.Draw(image)

        # Line 1: IP address
        draw.text((2, 0), f"IP: {ip_addr}", font=font, fill=255)
        # Line 2: CPU/RAM (rolling avg)
        draw.text((2, line_height), f"CPU: {cpu_usage:.0f}% RAM: {ram_usage:.0f}%", font=font, fill=255)
        # Line 3: Tailscale ping
        if tailscale_ping is not None:
            tailscale_line = f"Tailscale: {tailscale_ping:.2f} ms"
        else:
            tailscale_line = "Tailscale: DOWN"
        draw.text((2, line_height * 2), tailscale_line, font=font, fill=255)
        # Line 4: Uptime (auto-format)
        draw.text((2, line_height * 3), format_uptime(screen_chars=14), font=font, fill=255)

        oled.fill(0)
        oled.image(image)
        oled.show()

        await asyncio.sleep(5)

async def main():
    await asyncio.gather(
        cpu_task(),
        ram_task(),
        ip_task(),
        tailscale_task(),
        uptime_task(),
        display_task(),
    )

if __name__ == "__main__":
    asyncio.run(main())
