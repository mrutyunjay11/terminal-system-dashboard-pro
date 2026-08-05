# Terminal System Dashboard Pro

#### Video Demo: <URL HERE>

#### Description:

Terminal System Dashboard Pro is a real-time system monitoring tool that runs entirely inside the terminal. It collects information about the CPU, memory, disk, network, battery, and running processes, then displays everything in a live-updating dashboard built with the Rich library.

I built this project because I wanted something more hands-on than a simple command-line script. System monitoring felt like a good fit — it involves real data, multiple subsystems, and a visual component that makes the result feel tangible. The project gave me a reason to work with dataclasses, modular architecture, threading, non-blocking input, and a real terminal UI framework.

## How It Works

When you run `python project.py`, the application initializes a set of collectors — one for each subsystem (CPU, memory, disk, network, battery, processes). These collectors use `psutil` and `py-cpuinfo` to read hardware data from the operating system. A central monitor module calls each collector and bundles their results into a single `SystemState` dataclass. The dashboard module then takes that state and renders it into a Rich `Layout` with panels, tables, and progress bars. This cycle repeats every second by default.

The dashboard runs inside a `Live` context from Rich, which handles screen clearing and re-rendering. Keyboard input is handled without blocking — on macOS/Linux, the terminal is put into cbreak mode using `termios`, and `select` is used to poll `stdin`. On Windows, `msvcrt.kbhit()` is used instead.

## Features

- **CPU monitoring**: Shows the processor model, architecture, physical/logical core counts (with a breakdown of Performance and Efficiency cores on Apple Silicon), GPU and Neural Engine core counts, current/max frequencies, overall load percentage, per-core usage with P/E labels, thermal throttling state, and real-time CPU/GPU package power draw in Watts.
- **Memory monitoring**: Displays total, used, and available RAM along with swap usage. All sizes are formatted in human-readable units.
- **Disk monitoring**: Lists mounted partitions with their filesystem type, total/used/free space, and usage percentage. Also calculates live read and write speeds by comparing I/O counters between refreshes.
- **Network monitoring**: Shows hostname, local IP address, internet connectivity status (checked via socket), current upload and download speeds, and total bytes transferred. Supports running an internet speedtest in the background using `speedtest-cli`.
- **Battery monitoring**: Displays battery percentage, charging state, remaining runtime, temperature, virtual temperature, cycle counts, current health (based on nominal vs. design capacity), wear levels, active voltage, and current (charging/discharging amperage in mA).
- **Process monitoring**: Lists the top CPU-consuming and top memory-consuming processes with their PID, name, and resource usage.
- **Themes**: Five color schemes — dark, light, cyberpunk, matrix, and ocean. You can cycle through them at runtime by pressing `T`. The selected theme is saved to `config.json`.
- **Export**: Press `E` to export a snapshot of the current system state (including detailed CPU and battery diagnostics). Exports are saved to an `exports/` folder with timestamped filenames. Supported formats are JSON, CSV, and TXT.
- **Configuration**: Settings like refresh interval, theme, units (binary or metric), export format, and auto-export are stored in `config.json`. The application reads this file on startup and falls back to defaults if it is missing or malformed.
- **Logging**: Errors, warnings, startup events, theme changes, and exports are logged to `logs/dashboard.log`.

## Project Structure

```
project.py        - Entry point. Parses CLI arguments and starts the dashboard.
                    Contains main(), load_config(), save_report(), validate_theme().
dashboard.py      - Builds the Rich layout and handles the live render loop
                    and non-blocking keyboard input.
monitor.py        - Coordinates all collectors and produces a unified SystemState.
cpu.py            - Collects CPU model, cores, frequency, usage, and temperature.
memory.py         - Collects RAM and swap usage.
disk.py           - Collects partition info and calculates read/write speed.
network.py        - Collects network stats, connectivity, and runs speedtests.
battery.py        - Collects battery percentage, charging status, and time remaining.
processes.py      - Finds the top 10 CPU and top 10 memory consuming processes.
config.py         - Manages loading and saving settings from config.json.
                    Defines the AppConfig dataclass and sets up logging.
utils.py          - Pure helper functions: format_bytes(), uptime(),
                    check_internet_connection(), get_local_ip(), safe_execute().
themes.py         - Defines ThemeColors dataclass and five theme palettes.
export.py         - Exports SystemState snapshots to JSON, CSV, or TXT files.
test_project.py   - Pytest test suite covering the core functions.
config.json       - Default configuration file.
requirements.txt  - Python package dependencies.
```

## Libraries Used

| Library | Purpose |
|---|---|
| `rich` | Terminal UI — layout, panels, tables, progress bars, live rendering |
| `psutil` | Reading CPU, memory, disk, network, battery, and process data from the OS |
| `py-cpuinfo` | Getting the CPU brand name and architecture |
| `speedtest-cli` | Running internet speed tests |
| `humanize` | Listed as a dependency (formatting support) |
| `colorama` | Terminal color initialization across platforms |
| `gputil` | Optional GPU information (listed as a dependency) |
| `platformdirs` | Listed as a dependency for platform-appropriate directory resolution |
| `pytest` | Running the automated test suite |

## Installation

```bash
# Clone or download the project
cd CS50P_Final_Project

# Create a virtual environment
python3 -m venv venv

# Activate it
# macOS / Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

**Start the live dashboard:**
```bash
python project.py
```

**Start with a specific theme:**
```bash
python project.py --theme cyberpunk
```

**Change the refresh interval (in seconds):**
```bash
python project.py --refresh 2
```

**Print a one-time snapshot to stdout and exit:**
```bash
python project.py --once
```

**Export a report and exit immediately:**
```bash
python project.py --export json
python project.py --export csv
python project.py --export txt
```

Supported themes for `--theme`: `dark`, `light`, `cyberpunk`, `matrix`, `ocean`.

## Keyboard Shortcuts

These work while the live dashboard is running:

| Key | Action |
|---|---|
| `Q` | Quit the dashboard |
| `R` | Force an immediate refresh |
| `T` | Cycle to the next theme |
| `E` | Export a snapshot report |
| `S` | Run a background internet speedtest |

## Design Decisions

**Modular collector pattern.** Each subsystem (CPU, memory, disk, etc.) has its own module with a collector class. The collector exposes a single `collect()` method that returns a dataclass. This keeps each file focused on one thing, makes the code easier to test, and means adding a new subsystem is just adding a new file and wiring it into the monitor.

**Dataclasses everywhere.** I used `@dataclass` for `CPUData`, `MemoryData`, `DiskData`, `NetworkData`, `BatteryData`, `ProcessInfo`, `SystemState`, `OSData`, `AppConfig`, and `ThemeColors`. They reduce boilerplate and make the data flow between modules explicit.

**Caching static values.** The CPU model name and architecture are fetched once during initialization, not on every refresh. `py-cpuinfo` is slow (it can take hundreds of milliseconds), so caching avoids lag in the render loop.

**Non-blocking keyboard input.** Using `input()` would freeze the dashboard. Instead, the terminal is switched to cbreak mode on Unix using `termios`/`tty`, and `select` is used to check if a key was pressed without waiting. On Windows, `msvcrt` handles the same thing. This is wrapped in a context manager that restores terminal settings on exit.

**Background speedtest.** The speedtest takes 10-20 seconds. Running it on the main thread would freeze the UI. Instead, it runs on a daemon thread. The dashboard checks the thread's state each refresh and shows either "Running..." or the results.

**Configuration validation.** Every field in `config.json` is validated when loaded. Invalid themes fall back to "dark". Invalid refresh intervals fall back to 1.0. Malformed JSON falls back to all defaults. The application never crashes because of a bad config file.

**Error handling and hardware fallbacks.** Missing battery sensors, unavailable temperature readings, permission-denied partitions, and network failures are all caught and handled with fallbacks instead of crashes. On systems where low-level sensor access is restricted (like Apple Silicon without sudo), the application falls back safely to reporting general metrics.

**Apple Silicon optimizations.** On Apple Silicon macOS systems, standard library monitoring calls (like `psutil`) do not report P-core vs. E-core counts or package power draw. To support this natively, the app runs queries against `sysctl` and `system_profiler` to cache core topologies, and prompts for `sudo` credentials at startup to spawn a background daemon thread that reads package-level power consumption via Apple's built-in `powermetrics` utility. Additionally, detailed battery health diagnostics (cycle counts, virtual temperature, actual current, design/nominal capacities, and wear percentage) are fetched via parsing `ioreg` output.


## Testing

The test suite is in `test_project.py` and runs with pytest:

```bash
pytest test_project.py
```

The following functions are tested:

- **`validate_theme()`** — Tests with valid theme names, invalid names, whitespace/capitalization variations, and non-string inputs (int, None, list). Checks that ValueError and TypeError are raised appropriately.
- **`format_bytes()`** — Tests binary (base 1024) and metric (base 1000) formatting, zero bytes, boundary values (exactly 1 KiB, 1 MiB, etc.), negative input (expects ValueError), and large values up to exabytes.
- **`uptime()`** — Tests with mocked `time.time()` for various durations (seconds, minutes, hours, days). Also tests edge cases where boot time equals or exceeds current time.
- **`load_config()`** — Tests with a missing file (expects defaults), a valid JSON file, a malformed JSON file (expects defaults), and a file with out-of-bounds values (expects safe fallbacks).
- **`save_report()`** — Tests successful file creation (including automatic parent directory creation), empty filepath, and non-string content inputs.

There are 15 test cases total, covering valid input, invalid input, and edge cases.

## Future Improvements

- Add GPU monitoring using GPUtil for machines with NVIDIA GPUs.
- Add a help screen overlay that can be toggled with `H`.
- Support custom keybindings defined in config.json.
- Add historical tracking so metrics can be graphed over time.
- Allow filtering processes by name in the process panel.

## License

This project is licensed under the **GNU General Public License v3.0** (GPLv3). See the [LICENSE](file:///Users/mrutyunjayjoshi/Desktop/CS50P_Final_Project/LICENSE) file for details.

