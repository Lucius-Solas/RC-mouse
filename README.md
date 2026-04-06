# RC-Mouse

Control the system mouse cursor with a joystick/controller (for example a RadioMaster Pocket) using simple physics-based movement.

## Features

- Left stick Y: vertical acceleration (gravity-like)
- Left stick X: horizontal acceleration
- Right stick X: direct horizontal movement
- Velocity damping/friction
- Full screen wrapping (teleport at edges)

## Setup

1. Install Python 3.8+.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python rc_mouse.py
```

Optional tuning arguments:

```bash
python rc_mouse.py --hz 120 --deadzone 0.1 --gravity 0.8 --damping 0.92
```

Axis mapping defaults:

- `--left-x-axis 0`
- `--left-y-axis 1`
- `--right-x-axis 2`

If your controller reports different axis indices, override with CLI flags.
