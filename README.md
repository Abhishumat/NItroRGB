# NitroRGB Control Center

A modern, full-featured GUI frontend for managing Acer Nitro keyboard backlighting on Linux.

Built with PyQt, NitroRGB serves as a lightweight alternative to native Windows control software. It interfaces directly with the `facer-rgb` kernel module to provide real-time control over static lighting zones, hardware animations, global brightness, and custom preset management.

## Features

* **Advanced Zone Control:** Individually toggle power and assign custom hex colors to all 4 keyboard zones.
* **Hardware Animations:** Full support for built-in effects (Wave, Breath, Neon, Shifting, Zoom) with adjustable speed, direction, and base colors.
* **Dynamic Wallpaper Sync:** Extracts a 4-color gradient from your active wallpaper, applies an LED-specific saturation boost, and maps it across your keyboard zones.
* **Preset Management:** Create, save, and delete your own custom lighting layouts (comes pre-loaded with themes like Pastel Sky and Arctic Ice).
* **Boot Daemon:** Supports a `--silent` flag to run a smooth wipe animation and apply your saved settings automatically on system startup without launching the GUI.
* **Hardware Diagnostics:** Built-in system check to verify if the `/dev/acer-gkbbl-0` device is loaded and has the correct user permissions.

## Requirements

* **Hardware:** Acer Nitro 5 (Tested on AN515-45)
* **OS:** Linux (Arch, CachyOS, Pop!_OS, etc.)
* **Dependencies:**
* The [facer](https://github.com/JafarAkhondali/acer-predator-turbo-and-rgb-keyboard-linux-module) kernel module must be installed and loaded.
* Python 3.8+

### Dependencies

* `colorthief`
* `Pillow`
* `PyQt5` (or `PyQt6`)

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/NitroRGB.git
cd NitroRGB

```

2. Set up a virtual environment and install the required Python packages:
```bash
python -m venv venv
source venv/bin/activate
pip install PyQt5 colorthief Pillow

```


## Usage

### Launching the GUI

Run the main script to open the Control Center:

```bash
python main.py

```

### Applying on Startup (Silent Mode)

To have your keyboard light up with your saved settings (and an optional startup animation) when you boot your computer, add the following command to your desktop environment's autostart applications:

```bash
/path/to/NitroRGB/venv/bin/python /path/to/NitroRGB/main.py --silent

```

## Permissions & Troubleshooting

NitroRGB requires write access to `/dev/acer-gkbbl-0` to communicate with the keyboard. If the app launches but the colors don't change, or the built-in Diagnostic tool reports a permission error, you need to set up a `udev` rule to grant your user access to the hardware file.

1. Create a new udev rule:
```bash
sudo nano /etc/udev/rules.d/99-acer-rgb.rules

```


2. Add the following line:
```text
KERNEL=="acer-gkbbl-0", MODE="0666"

```


3. Reload the rules:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger

```
