"""Mouse/keyboard injection that never travels in a straight line."""
import ctypes
import math
import random
import time
from ctypes import wintypes

from pynput.keyboard import Controller as KB, Key

MOUSEEVENTF_MOVE = 0x0001
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class _INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


def _raw_move(dx: int, dy: int):
    inp = _INPUT(type=INPUT_MOUSE,
                 u=_INPUT._U(mi=MOUSEINPUT(dx, dy, 0, MOUSEEVENTF_MOVE, 0, None)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def human_move(dx: int, dy: int, cfg):
    """Curved, eased, sub-stepped, with optional overshoot."""
    if dx == 0 and dy == 0:
        return

    dist = math.hypot(dx, dy)
    steps = max(3, min(int(dist / 6), 18))

    # perpendicular control point -> arc instead of a ruler line
    ang = math.atan2(dy, dx) + math.pi / 2
    bow = random.uniform(0.06, 0.20) * dist * random.choice((-1, 1))
    cxp, cyp = dx / 2 + math.cos(ang) * bow, dy / 2 + math.sin(ang) * bow

    ox = oy = 0.0
    for i in range(1, steps + 1):
        t = i / steps
        e = t * t * (3 - 2 * t)                      # smoothstep easing
        px = 2 * (1 - e) * e * cxp + e * e * dx
        py = 2 * (1 - e) * e * cyp + e * e * dy
        sx, sy = round(px - ox), round(py - oy)
        if sx or sy:
            _raw_move(sx, sy)
            ox += sx
            oy += sy
        time.sleep(random.uniform(0.006, 0.016))

    # small human overshoot + settle-back
    if random.random() < cfg.overshoot_chance and dist > 40:
        jx = round(random.gauss(0, 2.2))
        jy = round(random.gauss(0, 2.2))
        _raw_move(jx, jy)
        time.sleep(random.uniform(0.030, 0.070))
        _raw_move(-jx, -jy)


class Keys:
    def __init__(self):
        self.kb = KB()

    def down(self, k):
        self.kb.press(k)

    def up(self, k):
        self.kb.release(k)

    def hold(self, k, lo, hi):
        self.kb.press(k)
        time.sleep(random.uniform(lo, hi))
        self.kb.release(k)

    def tap(self, k):
        self.kb.press(k)
        time.sleep(random.uniform(0.028, 0.062))
        self.kb.release(k)


def release_all(keys: Keys):
    for k in ("w", "a", "s", "d", "e", "shift"):
        try:
            keys.up(k)
        except Exception:
            pass
