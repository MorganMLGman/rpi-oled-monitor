# OLED Status for Raspberry Pi

A Python system monitor for Raspberry Pi with an SSD1306 OLED display.  
Displays rolling average CPU and RAM usage, formatted uptime, local IP, and Tailscale ping status.

## Features

- **Rolling average** for CPU and RAM usage (last 10 seconds)
- **Smart uptime formatting** (shows seconds, minutes, hours, days as appropriate for display space)
- **Local IP address** display
- **Tailscale ping** status (average latency or DOWN info)
- Designed for quick hardware and network status checks

## Requirements

- Raspberry Pi with I2C-connected SSD1306 OLED display (128x64 recommended)
- Python 3
- Python packages:  
  `psutil`, `Pillow`, `adafruit-circuitpython-ssd1306`

Install dependencies with pip:
```sh
pip install psutil Pillow adafruit-circuitpython-ssd1306
```

## Usage

1. Connect your SSD1306 OLED display to your Raspberry Pi (I2C: SDA, SCL).
2. Clone this repository.
3. Install required dependencies.
4. Run the script:
   ```sh
   python3 oled_status.py
   ```
5. The display will show:
   - Line 1: Local IP address
   - Line 2: CPU and RAM usage (as a rolling average)
   - Line 3: Tailscale ping (average, or DOWN if unreachable)
   - Line 4: Uptime (with optimal formatting for the display)

## Customization

- You can adjust the display refresh rate or font in the script if needed.
- To use a custom font, place the `.ttf` file in the script directory and update the filename in the code.
