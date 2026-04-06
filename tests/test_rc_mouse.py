"""Tests for rc_mouse.py core logic (no hardware required)."""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Stub out display-dependent packages before importing rc_mouse so that the
# tests can run in a headless environment (no DISPLAY / X server required).
for _mod in ("pygame", "pyautogui", "mouseinfo"):
    sys.modules.setdefault(_mod, MagicMock())

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rc_mouse


class TestApplyDeadZone(unittest.TestCase):
    def test_within_dead_zone_returns_zero(self):
        self.assertEqual(rc_mouse.apply_dead_zone(0.03, 0.05), 0.0)
        self.assertEqual(rc_mouse.apply_dead_zone(-0.04, 0.05), 0.0)
        self.assertEqual(rc_mouse.apply_dead_zone(0.0, 0.05), 0.0)

    def test_exactly_at_dead_zone_boundary_returns_zero(self):
        self.assertEqual(rc_mouse.apply_dead_zone(0.05, 0.05), 0.0)

    def test_outside_dead_zone_positive(self):
        result = rc_mouse.apply_dead_zone(1.0, 0.05)
        self.assertAlmostEqual(result, 1.0)

    def test_outside_dead_zone_negative(self):
        result = rc_mouse.apply_dead_zone(-1.0, 0.05)
        self.assertAlmostEqual(result, -1.0)

    def test_rescales_correctly(self):
        # Midway between dead_zone (0.05) and 1.0 should give 0.5
        result = rc_mouse.apply_dead_zone(0.525, 0.05)
        self.assertAlmostEqual(result, 0.5)

    def test_preserves_sign(self):
        pos = rc_mouse.apply_dead_zone(0.5, 0.05)
        neg = rc_mouse.apply_dead_zone(-0.5, 0.05)
        self.assertGreater(pos, 0)
        self.assertLess(neg, 0)
        self.assertAlmostEqual(pos, -neg)


class TestLoadConfig(unittest.TestCase):
    def test_defaults_when_no_file(self):
        config = rc_mouse.load_config("/nonexistent/path/config.json")
        self.assertIn("sensitivity", config)
        self.assertIn("dead_zone", config)
        self.assertIn("axes", config)
        self.assertIn("buttons", config)

    def test_loads_user_values(self):
        data = {"sensitivity": 42, "dead_zone": 0.1}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as fh:
            json.dump(data, fh)
            path = fh.name
        try:
            config = rc_mouse.load_config(path)
            self.assertEqual(config["sensitivity"], 42)
            self.assertAlmostEqual(config["dead_zone"], 0.1)
            # Defaults not overridden should still be present
            self.assertIn("axes", config)
        finally:
            os.unlink(path)

    def test_deep_merges_axes(self):
        data = {"axes": {"x": 2}}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as fh:
            json.dump(data, fh)
            path = fh.name
        try:
            config = rc_mouse.load_config(path)
            self.assertEqual(config["axes"]["x"], 2)
            # Other axes keys should come from defaults
            self.assertIn("y", config["axes"])
        finally:
            os.unlink(path)

    def test_invalid_json_uses_defaults(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as fh:
            fh.write("{bad json")
            path = fh.name
        try:
            config = rc_mouse.load_config(path)
            self.assertIn("sensitivity", config)
        finally:
            os.unlink(path)

    def test_comments_are_ignored(self):
        data = {"_comment": "should be ignored", "sensitivity": 5}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as fh:
            json.dump(data, fh)
            path = fh.name
        try:
            config = rc_mouse.load_config(path)
            self.assertNotIn("_comment", config)
            self.assertEqual(config["sensitivity"], 5)
        finally:
            os.unlink(path)


class TestListControllers(unittest.TestCase):
    @patch("rc_mouse.pygame")
    def test_no_controllers(self, mock_pygame):
        mock_pygame.joystick.get_count.return_value = 0
        # Should run without raising
        rc_mouse.list_controllers()

    @patch("rc_mouse.pygame")
    def test_one_controller(self, mock_pygame):
        mock_pygame.joystick.get_count.return_value = 1
        joy = MagicMock()
        joy.get_name.return_value = "FrSky Taranis"
        joy.get_numaxes.return_value = 6
        joy.get_numbuttons.return_value = 16
        joy.get_numhats.return_value = 1
        mock_pygame.joystick.Joystick.return_value = joy
        rc_mouse.list_controllers()


class TestRunExitsWhenNoController(unittest.TestCase):
    @patch("rc_mouse.pygame")
    def test_exits_on_no_joystick(self, mock_pygame):
        mock_pygame.joystick.get_count.return_value = 0
        config = rc_mouse.load_config(None)
        with self.assertRaises(SystemExit):
            rc_mouse.run(config)

    @patch("rc_mouse.pygame")
    def test_exits_on_invalid_index(self, mock_pygame):
        mock_pygame.joystick.get_count.return_value = 1
        config = rc_mouse.load_config(None)
        config["controller_index"] = 5
        with self.assertRaises(SystemExit):
            rc_mouse.run(config)


if __name__ == "__main__":
    unittest.main()
