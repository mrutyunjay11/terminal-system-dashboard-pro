<div align="center">

```
████████╗ ███████╗██████╗ ██████╗
╚══██╔══╝██╔════╝██╔══██╗██╔══██╗
   ██║   ███████╗██║  ██║██████╔╝
   ██║   ╚════██║██║  ██║██╔═══╝
██║   ███████║██████╔╝██║
╚═╝   ╚══════╝╚═════╝ ╚═╝
```

# Terminal System Dashboard Pro

**A real-time system monitoring dashboard that lives in your terminal.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)]()
[![CS50P](https://img.shields.io/badge/CS50P-Final%20Project-red)](https://cs50.harvard.edu/python/)

#### Video Demo: `<URL HERE>`

</div>

---

## 📖 About

Terminal System Dashboard Pro is a fully cross-platform, real-time system monitoring tool built entirely for the terminal. It displays live CPU, memory, disk, network, battery, and process data in a rich, colorful dashboard — updating every second.

Built as the **CS50P Final Project** by [Mrutyunjay Joshi](https://github.com/mrutyunjay11).

---

## 🖥️ Platform Versions

This repository contains two separate versions optimised for each platform:

| Version | Folder | Platforms |
|---|---|---|
| 🍎 **macOS Version** | [`mac_version/`](mac_version/) | macOS (Apple Silicon M1/M2/M3/M4 & Intel) |
| 🪟🐧 **Windows & Linux Version** | [`windows_linux_version/`](windows_linux_version/) | Windows 10/11 · Ubuntu · Debian · Arch · Fedora |

> Each folder contains its own complete source code, `requirements.txt`, and `README.md` with platform-specific setup instructions.

---

## ✨ Features at a Glance

```
┌─────────────────────────── TERMINAL SYSTEM DASHBOARD PRO ───────────────────────────┐
│  CPU │ Apple M2 · 4P+4E Cores · 8 GPU · 16 NPU · 5.3% Load · CPU Power: 0.67W      │
│  MEM │ 7.30 GiB / 16.00 GiB (65%)                                                   │
│ DISK │ / apfs  11.71 GiB / 228.27 GiB ·  Read: 0 B/s  Write: 4.05 KiB/s            │
│  NET │ Online · UP: 0 B/s · DN: 0 B/s · TX: 3.18 GiB / RX: 2.61 GiB               │
│  BAT │ 45% (5h 44m) · Temp: 30.5°C · Cycles: 185 · Health: 100%                    │
│ PROC │ Top 10 by CPU & Memory                                                        │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

- **CPU** — Model, architecture, P/E core split (Apple Silicon), GPU & NPU core counts, per-core bars, frequency, thermal state, real-time power draw in Watts
- **Memory** — RAM and Swap usage with human-readable formatting
- **Disk** — All partitions with usage bars and live I/O read/write speeds
- **Network** — IP, connectivity, upload/download speeds, total transfer, background speedtest
- **Battery** — Charge %, time remaining, temperature, cycle count, health %, wear level, voltage, current (mA)
- **Processes** — Top 10 by CPU and by Memory (PID, name, resource usage)
- **5 Themes** — `dark`, `light`, `cyberpunk`, `matrix`, `ocean` — switch live with `T`
- **Export** — Snapshot to `JSON`, `CSV`, or `TXT` with `E`
- **CLI flags** — `--theme`, `--refresh`, `--once`, `--export`

---

## 🖥️ Platform Compatibility

| Feature | 🍎 macOS (Apple Silicon) | 🍎 macOS (Intel) | 🪟 Windows | 🐧 Linux |
|---|:---:|:---:|:---:|:---:|
| CPU usage & per-core load | ✅ | ✅ | ✅ | ✅ |
| CPU Temperature | ✅ (powermetrics) | ✅ (psutil) | ✅ (WMI) | ✅ (psutil sensors) |
| RAM & Swap monitoring | ✅ | ✅ | ✅ | ✅ |
| Disk usage & I/O speed | ✅ | ✅ | ✅ | ✅ |
| Network speed & speedtest | ✅ | ✅ | ✅ | ✅ |
| Process list (CPU & RAM) | ✅ | ✅ | ✅ | ✅ |
| Battery status & health | ✅ | ✅ | ✅ | ✅ |
| Battery diagnostics (cycles/wear/V/mA) | ✅ (ioreg) | ✅ (ioreg) | ❌ | ✅ (/sys) |
| Dedicated GPU monitoring | ✅ (Apple GPU) | ❌ | ✅ (NVIDIA GPUtil) | ✅ (NVIDIA GPUtil) |
| Real-time Power Draw (Watts) | ✅ (powermetrics) | ❌ | ❌ | ✅ (Intel RAPL) |
| All 5 themes | ✅ | ✅ | ✅ | ✅ |
| Export (JSON / CSV / TXT) | ✅ | ✅ | ✅ | ✅ |
| P/E core split display | ✅ | ❌ | ❌ | ❌ |

---

## 🚀 Quick Start

### 🍎 macOS

```bash
# Clone & go to mac version
git clone https://github.com/mrutyunjay11/terminal-system-dashboard-pro.git
cd CS50P_Final_Project/mac_version

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Install & run
pip install -r requirements.txt
python project.py
```

📖 Full macOS guide → [`mac_version/README.md`](mac_version/README.md)

---

### 🪟 Windows

```bash
# Clone & go to Windows/Linux version
git clone https://github.com/mrutyunjay11/terminal-system-dashboard-pro.git
cd CS50P_Final_Project/windows_linux_version

# Set up virtual environment
python -m venv venv
venv\Scripts\activate

# Install & run
pip install -r requirements.txt
python project.py
```

> Use **Windows Terminal** (not the old `cmd.exe`) for full Unicode and color support.

📖 Full Windows guide → [`windows_linux_version/README.md`](windows_linux_version/README.md)

---

### 🐧 Linux

```bash
# Clone & go to Windows/Linux version
git clone https://github.com/mrutyunjay11/terminal-system-dashboard-pro.git
cd CS50P_Final_Project/windows_linux_version

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Install & run
pip install -r requirements.txt
python project.py
```

📖 Full Linux guide → [`windows_linux_version/README.md`](windows_linux_version/README.md)

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|---|---|
| `Q` | Quit the dashboard |
| `R` | Force an immediate refresh |
| `T` | Cycle to the next theme |
| `E` | Export a snapshot report |
| `S` | Run a background internet speedtest |

---

## 📁 Repository Structure

```
CS50P_Final_Project/
│
├── 📄 README.md                    ← You are here (GitHub landing page)
├── 📄 LICENSE                      ← GNU General Public License v3.0
├── 📄 .gitignore
│
├── 🍎 mac_version/                 ← macOS optimized build
│   ├── project.py                  ← Entry point (main, load_config, save_report, validate_theme)
│   ├── test_project.py             ← 15 pytest tests
│   ├── dashboard.py                ← Rich TUI layout & keyboard input
│   ├── monitor.py                  ← System state orchestrator
│   ├── cpu.py                      ← CPU + Apple Silicon power/thermal
│   ├── battery.py                  ← Battery + ioreg diagnostics
│   ├── memory.py                   ← RAM & Swap
│   ├── disk.py                     ← Partitions & I/O speed
│   ├── network.py                  ← Network stats & speedtest
│   ├── processes.py                ← Top process scanner
│   ├── export.py                   ← JSON / CSV / TXT exporter
│   ├── themes.py                   ← 5 color palettes
│   ├── config.py                   ← AppConfig dataclass & logging
│   ├── utils.py                    ← Helper functions
│   ├── config.json                 ← Default settings
│   ├── requirements.txt            ← Dependencies
│   ├── video_script.txt            ← Demo video script
│   └── README.md                   ← macOS-specific install guide
│
└── 🪟🐧 windows_linux_version/     ← Windows & Linux build
    ├── project.py                  ← Entry point (with Windows UTF-8 fix)
    ├── test_project.py             ← 15 pytest tests
    ├── dashboard.py                ← Rich TUI (msvcrt keyboard on Windows)
    ├── monitor.py
    ├── cpu.py
    ├── battery.py
    ├── memory.py
    ├── disk.py
    ├── network.py
    ├── processes.py
    ├── export.py
    ├── themes.py
    ├── config.py
    ├── utils.py
    ├── config.json
    ├── requirements.txt
    ├── video_script.txt
    └── README.md                   ← Windows & Linux install guide
```

---

## 🧪 Testing

Both versions include a full test suite:

```bash
pytest test_project.py
```

**15 tests across 5 functions — all pass:**

| Function | What Is Tested |
|---|---|
| `validate_theme()` | Valid names, invalid names, non-string types (TypeError) |
| `format_bytes()` | Binary (1024) & metric (1000) units, negatives (ValueError), exabyte scale |
| `uptime()` | Mocked boot times for seconds/minutes/hours/days, edge cases |
| `load_config()` | Missing file, valid JSON, malformed JSON, out-of-bounds values |
| `save_report()` | Successful write with auto-mkdir, empty path, non-string content |

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `rich` | ≥ 13.7.0 | Terminal UI framework |
| `psutil` | ≥ 5.9.8 | System hardware data |
| `py-cpuinfo` | ≥ 9.0.0 | CPU model & architecture |
| `speedtest-cli` | ≥ 2.1.3 | Internet speed testing |
| `humanize` | ≥ 4.9.0 | Human-readable sizes |
| `colorama` | ≥ 0.4.6 | Windows terminal color support |
| `gputil` | ≥ 1.4.0 | NVIDIA GPU monitoring (optional) |
| `platformdirs` | ≥ 4.2.0 | Platform directory resolution |
| `pytest` | ≥ 8.0.0 | Test runner |

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**.
See [LICENSE](LICENSE) for full details.

```
Copyright (C) 2026  Mrutyunjay Joshi

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
```

---

<div align="center">

Built with ❤️ as a CS50P Final Project · [Harvard CS50P](https://cs50.harvard.edu/python/)

</div>
