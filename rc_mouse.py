#!/usr/bin/env python3
"""
rc_mouse.py – Control your mouse cursor with a drone/RC controller.

Usage:
    python rc_mouse.py [--list] [--config CONFIG] [--controller INDEX]

Options:
    --list              List all detected joystick/controller devices and exit.
    --config CONFIG     Path to a JSON config file (default: config.json).
    --controller INDEX  Override the controller index from the config.

Default axis mapping (customisable in config.json):
    Axis 0  →  mouse X
    Axis 1  →  mouse Y
    Axis 3  →  scroll wheel (when scroll-mode is active)

Default button mapping:
    Button 0  →  left click
    Button 1  →  right click
    Button 2  →  toggle scroll mode
    Button 9  →  quit
"""

import argparse
import json
import os
import sys
import time

import pyautogui
import pygame


# ── helpers ───────────────────────────────────────────────────────────────────

def load_config(path: str) -> dict:
    """Load JSON config, falling back to built-in defaults."""
    defaults = {
        "controller_index": 0,
        "axes": {"x": 0, "y": 1, "scroll": 3},
        "buttons": {
            "left_click": 0,
            "right_click": 1,
            "scroll_mode_toggle": 2,
            "quit": 9,
        },
        "sensitivity": 20,
        "dead_zone": 0.05,
        "invert_y": False,
        "invert_x": False,
        "poll_rate_hz": 60,
    }

    if path and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                user = json.load(fh)
            # Deep-merge user values over defaults
            for key, value in user.items():
                if key.startswith("_"):
                    continue
                if isinstance(value, dict) and key in defaults:
                    defaults[key].update(value)
                else:
                    defaults[key] = value
            print(f"[rc_mouse] Loaded config from '{path}'")
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[rc_mouse] Warning: could not read config '{path}': {exc}")
    else:
        print("[rc_mouse] No config file found – using built-in defaults.")

    return defaults


def apply_dead_zone(value: float, dead_zone: float) -> float:
    """Return 0 when |value| is inside the dead zone; rescale otherwise."""
    if abs(value) < dead_zone:
        return 0.0
    sign = 1 if value > 0 else -1
    return sign * (abs(value) - dead_zone) / (1.0 - dead_zone)


def list_controllers() -> None:
    """Print all detected joystick devices and exit."""
    pygame.init()
    pygame.joystick.init()
    count = pygame.joystick.get_count()
    if count == 0:
        print("No joystick/controller devices detected.")
    else:
        print(f"Detected {count} device(s):")
        for i in range(count):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            print(
                f"  [{i}] {joy.get_name()} "
                f"– axes: {joy.get_numaxes()}, "
                f"buttons: {joy.get_numbuttons()}, "
                f"hats: {joy.get_numhats()}"
            )
    pygame.quit()


# ── main loop ─────────────────────────────────────────────────────────────────

def run(config: dict) -> None:
    pygame.init()
    pygame.joystick.init()

    num_joysticks = pygame.joystick.get_count()
    if num_joysticks == 0:
        print("[rc_mouse] ERROR: No joystick/controller detected. Plug in your controller and try again.")
        sys.exit(1)

    idx = int(config["controller_index"])
    if idx >= num_joysticks:
        print(
            f"[rc_mouse] ERROR: Controller index {idx} not found. "
            f"Only {num_joysticks} device(s) detected (indices 0–{num_joysticks - 1})."
        )
        sys.exit(1)

    joystick = pygame.joystick.Joystick(idx)
    joystick.init()
    print(f"[rc_mouse] Using controller [{idx}]: {joystick.get_name()}")
    print(f"           Axes: {joystick.get_numaxes()}, Buttons: {joystick.get_numbuttons()}")

    # Config shortcuts
    ax_cfg = config["axes"]
    btn_cfg = config["buttons"]
    sensitivity = float(config["sensitivity"])
    dead_zone = float(config["dead_zone"])
    invert_y = bool(config["invert_y"])
    invert_x = bool(config["invert_x"])
    poll_interval = 1.0 / max(1, int(config["poll_rate_hz"]))

    ax_x = int(ax_cfg.get("x", 0))
    ax_y = int(ax_cfg.get("y", 1))
    ax_scroll = int(ax_cfg.get("scroll", 3))

    btn_left = btn_cfg.get("left_click", 0)
    btn_right = btn_cfg.get("right_click", 1)
    btn_scroll_toggle = btn_cfg.get("scroll_mode_toggle", 2)
    btn_quit = btn_cfg.get("quit", 9)

    # Convert to int, handling None
    btn_left = int(btn_left) if btn_left is not None else None
    btn_right = int(btn_right) if btn_right is not None else None
    btn_scroll_toggle = int(btn_scroll_toggle) if btn_scroll_toggle is not None else None
    btn_quit = int(btn_quit) if btn_quit is not None else None

    # Keep pyautogui fail-safe enabled: moving the cursor to the top-left
    # corner of the screen will raise an exception and exit the program,
    # providing a reliable emergency stop independent of the controller.
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0

    scroll_mode = False
    btn_states: dict[int, bool] = {}

    print("[rc_mouse] Running. Move the sticks to control the cursor.")
    print("           Press the quit button or Ctrl-C to exit.\n")

    try:
        while True:
            pygame.event.pump()

            # ── read axes ─────────────────────────────────────────────────────
            num_axes = joystick.get_numaxes()

            raw_x = joystick.get_axis(ax_x) if ax_x < num_axes else 0.0
            raw_y = joystick.get_axis(ax_y) if ax_y < num_axes else 0.0
            raw_scroll = joystick.get_axis(ax_scroll) if ax_scroll < num_axes else 0.0

            dx = apply_dead_zone(raw_x, dead_zone) * sensitivity
            dy = apply_dead_zone(raw_y, dead_zone) * sensitivity
            dscroll = apply_dead_zone(raw_scroll, dead_zone)

            if invert_x:
                dx = -dx
            if invert_y:
                dy = -dy

            # ── move or scroll ────────────────────────────────────────────────
            if scroll_mode:
                if dscroll != 0.0:
                    pyautogui.scroll(int(-dscroll * 3))
            else:
                if dx != 0.0 or dy != 0.0:
                    pyautogui.moveRel(int(dx), int(dy), duration=0)

            # ── buttons ───────────────────────────────────────────────────────
            num_btns = joystick.get_numbuttons()

            for btn_idx in [btn_left, btn_right, btn_scroll_toggle, btn_quit]:
                if btn_idx is None or btn_idx >= num_btns:
                    continue

                pressed = bool(joystick.get_button(btn_idx))
                prev = btn_states.get(btn_idx, False)

                if pressed and not prev:  # rising edge only
                    if btn_idx == btn_quit:
                        print("[rc_mouse] Quit button pressed. Exiting.")
                        return
                    elif btn_idx == btn_scroll_toggle:
                        scroll_mode = not scroll_mode
                        print(f"[rc_mouse] Scroll mode {'ON' if scroll_mode else 'OFF'}")
                    elif btn_idx == btn_left:
                        pyautogui.click(button="left")
                    elif btn_idx == btn_right:
                        pyautogui.click(button="right")

                btn_states[btn_idx] = pressed

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\n[rc_mouse] Interrupted by user.")
    finally:
        pygame.quit()


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Control your mouse cursor with a drone/RC controller.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List detected controllers and exit.",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        metavar="FILE",
        help="Path to JSON config file (default: config.json).",
    )
    parser.add_argument(
        "--controller",
        type=int,
        default=None,
        metavar="INDEX",
        help="Override controller index from config.",
    )
    args = parser.parse_args()

    if args.list:
        list_controllers()
        return

    config = load_config(args.config)

    if args.controller is not None:
        config["controller_index"] = args.controller

    run(config)


if __name__ == "__main__":
    main()
