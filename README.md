# RC-mouse

Control your mouse cursor with a drone/RC controller (or any USB joystick).

## Requirements

- Python 3.8+
- A drone/RC controller that exposes itself as a USB joystick (most FrSky, Taranis, FlySky, DJI, etc. controllers do this when plugged in via USB in "Joystick" mode)

## Installation

```bash
pip install -r requirements.txt
```

## Quick start

```bash
# List detected controllers
python rc_mouse.py --list

# Start controlling the mouse with controller index 0 (default)
python rc_mouse.py
```

## Controls

| Input | Action |
|---|---|
| Left/right stick X axis | Move cursor left/right |
| Left/right stick Y axis | Move cursor up/down |
| Button 0 | Left click |
| Button 1 | Right click |
| Button 2 | Toggle scroll mode |
| Button 9 | Quit |

> Axes and buttons vary by controller. Use `--list` to see how many axes/buttons your device has, then adjust `config.json` accordingly.

## Configuration (`config.json`)

```json
{
  "controller_index": 0,
  "axes": {
    "x": 0,
    "y": 1,
    "scroll": 3
  },
  "buttons": {
    "left_click": 0,
    "right_click": 1,
    "scroll_mode_toggle": 2,
    "quit": 9
  },
  "sensitivity": 20,
  "dead_zone": 0.05,
  "invert_y": false,
  "invert_x": false,
  "poll_rate_hz": 60
}
```

| Key | Description |
|---|---|
| `controller_index` | Index of the controller to use (see `--list`) |
| `axes.x` / `axes.y` | Joystick axis indices for horizontal/vertical cursor movement |
| `axes.scroll` | Axis index used for scrolling when scroll mode is active |
| `buttons.*` | Button indices for each action (`null` to disable) |
| `sensitivity` | Pixels moved per poll cycle at full deflection |
| `dead_zone` | Fraction of axis range to ignore near centre (0–1) |
| `invert_x` / `invert_y` | Flip cursor movement direction |
| `poll_rate_hz` | How often the controller is polled per second |

## Usage

```
python rc_mouse.py [--list] [--config CONFIG] [--controller INDEX]
```

- `--list` – List all connected joystick devices and exit.
- `--config FILE` – Use a custom config file (default: `config.json`).
- `--controller INDEX` – Override the controller index at runtime.

Press **Ctrl-C** or the configured quit button to exit.
