# Terminal System Dashboard Pro — Windows & Linux Version

> 🔙 [← Back to main README](../README.md)

#### Video Demo: `<URL HERE>`

#### Description:

Terminal System Dashboard Pro is a real-time system monitoring tool that runs entirely inside the terminal. It collects information about the CPU, memory, disk, network, battery, and running processes, then displays everything in a live-updating dashboard built with the Rich library.

This is the **Windows & Linux version**, supporting Windows 10/11 (via `msvcrt` for keyboard input) and all major Linux distributions (Ubuntu, Debian, Arch, Fedora, etc.).

---

## 🪟🐧 Platform-Specific Notes

### Windows
- Keyboard input uses `msvcrt.kbhit()` instead of `termios` (macOS/Linux).
- UTF-8 output is configured automatically on startup (`sys.stdout.reconfigure`).
- Use **Windows Terminal** (not the old `cmd.exe`) for full Unicode and color support.
- Run as **Administrator** if some disk I/O stats or process details are restricted.

### Linux
- Keyboard input uses `termios` + `select` (same as macOS).
- If battery or temperature sensors show `N/A`, install `lm-sensors`:
  ```bash
  sudo apt install lm-sensors        # Ubuntu / Debian
  sudo pacman -S lm_sensors          # Arch
  sudo dnf install lm_sensors        # Fedora
  ```
- Run with `sudo` if some network or disk stats are restricted.

---

## ✨ All Features

- **CPU** — Model, architecture, core counts, per-core usage bars, frequency, thermal pressure state
- **Memory** — RAM and Swap with human-readable units
- **Disk** — All partitions with live read/write I/O speeds
- **Network** — IP, connectivity, upload/download speeds, total transfer, background speedtest
- **Battery** — Charge %, charging state, time remaining (on laptops)
- **Processes** — Top 10 by CPU and top 10 by Memory (PID, name, resource usage)
- **5 Themes** — `dark`, `light`, `cyberpunk`, `matrix`, `ocean`
- **Export** — JSON, CSV, or TXT snapshot

---

## 🚀 Installation

### 🪟 Windows

#### Requirements
- Python 3.10 or higher — download from [python.org](https://www.python.org/downloads/)
- **Windows Terminal** — download from [Microsoft Store](https://aka.ms/terminal) (recommended)

#### Steps

```bash
# 1. Clone the repository
git clone https://github.com/mrutyunjay11/CS50P_Final_Project.git
cd CS50P_Final_Project/windows_linux_version

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
venv\Scripts\activate

# 4. Install all dependencies
pip install -r requirements.txt

# 5. Run the dashboard
python project.py
```

---

### 🐧 Linux

#### Requirements
- Python 3.10 or higher (`python3 --version`)
- `pip` and `venv` (`sudo apt install python3-pip python3-venv` on Ubuntu)

#### Steps

```bash
# 1. Clone the repository
git clone https://github.com/mrutyunjay11/CS50P_Final_Project.git
cd CS50P_Final_Project/windows_linux_version

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate it
source venv/bin/activate

# 4. Install all dependencies
pip install -r requirements.txt

# 5. Run the dashboard
python project.py
```

---

## ▶️ Usage

```bash
# Live dashboard (default)
python project.py

# Choose a theme at startup
python project.py --theme cyberpunk

# Change refresh rate (seconds)
python project.py --refresh 2

# Print one snapshot to terminal and exit
python project.py --once

# Export a report and exit
python project.py --export json
python project.py --export csv
python project.py --export txt
```

**Available themes:** `dark` · `light` · `cyberpunk` · `matrix` · `ocean`

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|---|---|
| `Q` | Quit |
| `R` | Force immediate refresh |
| `T` | Cycle theme |
| `E` | Export snapshot |
| `S` | Run background speedtest |

---

## 📁 File Structure

```
windows_linux_version/
├── project.py          ← Entry point: main(), load_config(), save_report(), validate_theme()
├── test_project.py     ← 15 pytest tests
├── dashboard.py        ← Rich TUI layout, live loop, msvcrt (Win) / termios (Linux) keyboard
├── monitor.py          ← Orchestrates all collectors into SystemState
├── cpu.py              ← CPU metrics via psutil
├── battery.py          ← Battery status & health
├── memory.py           ← RAM & Swap
├── disk.py             ← Partitions & I/O speed
├── network.py          ← Network stats & speedtest thread
├── processes.py        ← Top process scanner (heapq optimised)
├── export.py           ← JSON / CSV / TXT exporter
├── themes.py           ← 5 color palettes
├── config.py           ← AppConfig dataclass & logging setup
├── utils.py            ← format_bytes(), uptime(), safe_execute(), etc.
├── config.json         ← Default settings
├── requirements.txt    ← pip dependencies
└── video_script.txt    ← Demo video script
```

---

## 🧪 Testing

```bash
pytest test_project.py
```

15 tests covering `validate_theme()`, `format_bytes()`, `uptime()`, `load_config()`, and `save_report()` — all pass.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| Colors not showing on Windows | Use **Windows Terminal**, not `cmd.exe` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside your venv |
| Battery shows `N/A` on Linux | Install `lm-sensors` — see notes above |
| Process details missing | Run as Administrator (Windows) or `sudo` (Linux) |
| Speedtest slow or fails | Check internet connection; speedtest runs in background |

---

## 📄 License

GNU General Public License v3.0 — see [LICENSE](../LICENSE)
