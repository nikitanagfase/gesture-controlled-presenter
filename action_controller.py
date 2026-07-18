"""
action_controller.py
----------------------
Takes a classified gesture and actually DOES something with it:
presses a keyboard shortcut, or (in pointer mode) moves the mouse.

Also owns the cooldown timer, so a gesture held for 5 seconds fires
once every `cooldown_seconds`, not once per frame.
"""

import time
import platform

import pyautogui

try:
    import pyautogui
    pyautogui.FAILSAFE = True  # move mouse to a screen corner to abort, as a safety net
    PYAUTOGUI_AVAILABLE = True
except Exception:
    PYAUTOGUI_AVAILABLE = False



class ActionController:
    def __init__(self, config: dict):
        self.gestures_cfg = config.get("gestures", {})
        self.key_mappings = config.get("key_mappings", {})
        self.cooldown = config.get("cooldown_seconds", 1.0)

        self._last_trigger_time = 0.0
        self._last_gesture = None

        detected = "mac" if platform.system() == "Darwin" else (
            "windows" if platform.system() == "Windows" else "linux"
        )
        self.platform = config.get("platform_override") or detected

    def _keys_for(self, action_name: str):
        return self.key_mappings.get(self.platform, {}).get(action_name)

    def trigger(self, gesture_name: str):
        """
        Executes the keyboard action mapped to `gesture_name`, respecting
        the cooldown. Returns the action name that fired, or None if
        nothing happened (unknown gesture, or still cooling down).
        """
        if gesture_name in ("none", "unknown", "index_only"):
            return None
        if gesture_name not in self.gestures_cfg:
            return None

        now = time.time()
        repeated_gesture = gesture_name == self._last_gesture
        still_cooling_down = (now - self._last_trigger_time) < self.cooldown

        if repeated_gesture and still_cooling_down:
            return None

        action_name = self.gestures_cfg[gesture_name]["action"]
        keys = self._keys_for(action_name)
        if not keys:
            return None

        if len(keys) == 1:
            pyautogui.press(keys[0])
        else:
            pyautogui.hotkey(*keys)

        self._last_trigger_time = now
        self._last_gesture = gesture_name
        return action_name

    @staticmethod
    def move_pointer(x_norm: float, y_norm: float):
        """
        Laser Pointer Mode: moves the REAL system mouse cursor to a
        normalized (0-1, 0-1) position on screen, based on fingertip
        location. Used when the user shows only their index finger.
        """
        screen_w, screen_h = pyautogui.size()
        x = int(max(0, min(x_norm, 1)) * screen_w)
        y = int(max(0, min(y_norm, 1)) * screen_h)
        pyautogui.moveTo(x, y, duration=0.05)
