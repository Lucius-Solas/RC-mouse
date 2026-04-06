#!/usr/bin/env python3
import argparse
import sys
from dataclasses import dataclass

import pygame
import pyautogui


@dataclass
class CursorState:
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0


def apply_deadzone(value: float, deadzone: float) -> float:
    if abs(value) < deadzone:
        return 0.0
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Control mouse cursor from gamepad/joystick with simple physics."
    )
    parser.add_argument("--hz", type=int, default=120, help="Update rate.")
    parser.add_argument("--deadzone", type=float, default=0.1, help="Stick deadzone.")
    parser.add_argument(
        "--left-x-axis", type=int, default=0, help="Axis index for left stick X."
    )
    parser.add_argument(
        "--left-y-axis", type=int, default=1, help="Axis index for left stick Y."
    )
    parser.add_argument(
        "--right-x-axis", type=int, default=2, help="Axis index for right stick X."
    )
    parser.add_argument(
        "--gravity",
        type=float,
        default=0.8,
        help="Base downward gravity when no left Y input.",
    )
    parser.add_argument(
        "--left-y-accel", type=float, default=2.8, help="Left stick Y acceleration."
    )
    parser.add_argument(
        "--left-x-accel", type=float, default=1.4, help="Left stick X acceleration."
    )
    parser.add_argument(
        "--right-x-speed", type=float, default=22.0, help="Right stick X direct speed."
    )
    parser.add_argument(
        "--damping",
        type=float,
        default=0.92,
        help="Velocity damping per frame (0-1).",
    )
    return parser.parse_args()


def get_axis_safe(joystick: pygame.joystick.Joystick, axis_index: int) -> float:
    if axis_index < 0 or axis_index >= joystick.get_numaxes():
        return 0.0
    return float(joystick.get_axis(axis_index))


def main() -> int:
    args = parse_args()

    if args.hz <= 0:
        print("Error: --hz must be positive.", file=sys.stderr)
        return 1
    if not (0.0 < args.damping <= 1.0):
        print("Error: --damping must be in (0, 1].", file=sys.stderr)
        return 1
    if not (0.0 <= args.deadzone < 1.0):
        print("Error: --deadzone must be in [0, 1).", file=sys.stderr)
        return 1

    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No joystick/controller detected.", file=sys.stderr)
        pygame.quit()
        return 1

    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    pyautogui.FAILSAFE = False
    screen_w, screen_h = pyautogui.size()
    start_x, start_y = pyautogui.position()
    state = CursorState(float(start_x), float(start_y))
    clock = pygame.time.Clock()

    print(f"Using controller: {joystick.get_name()}")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            pygame.event.pump()

            lx = apply_deadzone(get_axis_safe(joystick, args.left_x_axis), args.deadzone)
            ly = apply_deadzone(get_axis_safe(joystick, args.left_y_axis), args.deadzone)
            rx = apply_deadzone(
                get_axis_safe(joystick, args.right_x_axis), args.deadzone
            )

            ay = args.gravity + (ly * args.left_y_accel)
            ax = lx * args.left_x_accel

            state.vy += ay
            state.vx += ax
            state.vx += rx * args.right_x_speed

            state.vx *= args.damping
            state.vy *= args.damping

            state.x = (state.x + state.vx) % screen_w
            state.y = (state.y + state.vy) % screen_h

            pyautogui.moveTo(int(state.x), int(state.y), _pause=False)
            clock.tick(args.hz)
    except KeyboardInterrupt:
        pass
    finally:
        joystick.quit()
        pygame.quit()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
