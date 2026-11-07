"""All tunables in one place. Every timing is a RANGE, never a constant."""
from dataclasses import dataclass
import random


def rng(r: tuple) -> float:
    return random.uniform(*r)


def rng_int(r: tuple) -> int:
    return random.randint(*r)


@dataclass
class Config:
    # ---------- capture ----------
    region: tuple | None = None      # (l, t, r, b) or None for full primary monitor
    target_fps: int = 45
    max_width: int = 1600            # downscale for detection speed

    # ---------- HUD masks (fractions of frame, zeroed out) ----------
    mask_top_left: tuple = (0.0, 0.0, 0.20, 0.20)
    mask_bottom_right: tuple = (0.72, 0.72, 1.0, 1.0)
    mask_bottom_left: tuple = (0.0, 0.80, 0.30, 1.0)

    # ---------- vision ----------
    min_blob_area: int = 200
    max_blob_area: int = 90_000
    min_solidity: float = 0.42
    min_aspect: float = 0.45
    max_aspect: float = 3.2
    persistence_frames: int = 3
    tracker_max_age: int = 10
    tracker_gate_px: int = 240

    # ---------- steering ----------
    aim_deadzone_px: int = 26
    aim_gain: float = 0.40
    max_mouse_step: int = 58
    aim_jitter_px: float = 2.4
    steer_interval: tuple = (0.028, 0.052)

    # ---------- interaction ----------
    close_bbox_h: int = 150
    reaction_delay: tuple = (0.18, 0.34)
    interact_hold: tuple = (0.05, 0.11)
    loot_taps: tuple = (3, 6)

    # ---------- humanization ----------
    scan_pan: tuple = (45, 190)
    scan_pause: tuple = (0.35, 1.7)
    wiggle_amplitude: float = 2.1
    approach_strafe_chance: float = 0.35
    distract_chance: float = 0.06
    distract_duration: tuple = (0.7, 2.4)
    overshoot_chance: float = 0.22

    # ---------- safety ----------
    panic_key: str = "f8"
    pause_key: str = "f7"
