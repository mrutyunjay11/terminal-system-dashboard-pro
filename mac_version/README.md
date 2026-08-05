# Terminal System Dashboard Pro — macOS Version

> 🔙 [← Back to main README](../README.md)

#### Video Demo: `<URL HERE>`

#### Description:

Terminal System Dashboard Pro is a real-time system monitoring tool that runs entirely inside the terminal. It collects information about the CPU, memory, disk, network, battery, and running processes, then displays everything in a live-updating dashboard built with the Rich library.

This is the **macOS version**, optimised for both **Apple Silicon** (M1, M2, M3, M4 and Pro/Max/Ultra variants) and **Intel** Macs. It includes exclusive Apple Silicon features such as P/E core display, real-time CPU/GPU package power draw (via `powermetrics`), and deep battery diagnostics (via `ioreg`).

---

## 🍎 macOS-Exclusive Features

| Feature | Apple Silicon | Intel Mac |
|---|:---:|:---:|
| Performance & Efficiency core split | ✅ | ❌ |
| GPU core count (from system_profiler) | ✅ | ❌ |
| Neural Engine (NPU) core count | ✅ | ❌ |
| Real-time CPU power draw (Watts) | ✅ (sudo) | ❌ |
| Real-time GPU power draw (Watts) | ✅ (sudo) | ❌ |
| Battery virtual temp, wear %, voltage, current (mA) | ✅ | ✅ |
| Battery cycle count & health (ioreg) | ✅ | ✅ |

---

## ✨ All Features

- **CPU** — Model, arch, P/E cores, GPU cores, NPU cores, frequency, per-core bars, thermal state, CPU/GPU power draw (W)
- **Memory** — RAM and Swap with human-readable units
- **Disk** — All partitions with live read/write I/O speeds
- **Network** — IP, connectivity, upload/download speeds, total transfer, background speedtest
- **Battery** — Charge %, time remaining, temperature, virtual temp, lifetime max/min temp, cycle count, health %, wear level, voltage, current (mA), design capacity
- **Processes** — Top 10 by CPU and top 10 by Memory
- **5 Themes** — `dark`, `light`, `cyberpunk`, `matrix`, `ocean`
- **Export** — JSON, CSV, or TXT snapshot

---

## 🚀 Installation

### Requirements
- macOS 12 Monterey or later
- Python 3.10 or higher (`python3 --version` to check)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/mrutyunjay11/terminal-system-dashboard-pro.git
cd CS50P_Final_Project/mac_version

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate it
source venv/bin/activate

# 4. Install all dependencies
pip install -r requirements.txt

# 5. Run the dashboard
python project.py
```

> **Apple Silicon**: On first run you will be prompted for your `sudo` password. This is required to enable thermal monitoring (CPU/GPU die temperature and package power draw via `powermetrics`). If you skip it, the dashboard falls back to battery sensor temperature — everything else still works.

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
mac_version/
├── project.py          ← Entry point: main(), load_config(), save_report(), validate_theme()
├── test_project.py     ← 15 pytest tests
├── dashboard.py        ← Rich TUI layout, live loop, termios keyboard input
├── monitor.py          ← Orchestrates all collectors into SystemState
├── cpu.py              ← CPU + Apple Silicon sysctl/powermetrics integration
├── battery.py          ← Battery + ioreg deep diagnostics
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

## 📄 License

GNU General Public License v3.0 — see [LICENSE](../LICENSE)
