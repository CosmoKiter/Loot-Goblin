import random
import time

import cv2

from config import rng, rng_int
from vision import Tracker
from human_input import human_move, release_all


class Brain:
    def __init__(self, cfg, vision, keys, cap):
        self.cfg = cfg
        self.vision = vision
        self.keys = keys
        self.cap = cap
        self.tracker = Tracker(cfg)
        self.target = None
        self.target_lost = 0
        self.locked_id = -1
        self.debug = False

    # ---------- helpers ----------
    def _steer(self, tx, ty, cx, cy):
        ex, ey = tx - cx, ty - cy
        if abs(ex) < self.cfg.aim_deadzone_px and abs(ey) < self.cfg.aim_deadzone_px:
            return ex, ey
        dx = max(-self.cfg.max_mouse_step,
                 min(self.cfg.max_mouse_step, ex * self.cfg.aim_gain))
        dy = max(-self.cfg.max_mouse_step,
                 min(self.cfg.max_mouse_step, ey * self.cfg.aim_gain))
        dx += random.gauss(0, self.cfg.aim_jitter_px)
        dy += random.gauss(0, self.cfg.aim_jitter_px)
        human_move(int(dx), int(dy), self.cfg)
        return ex, ey

    def _scan(self):
        """Sweep the camera in arcs, pausing like a bored human."""
        self.keys.up("w")
        direction = random.choice((-1, 1))
        travel = rng_int(self.cfg.scan_pan) * direction
        human_move(travel, rng_int((0, 14)), self.cfg)
        # idle wiggle
        for _ in range(rng_int((1, 3))):
            human_move(round(random.gauss(0, self.cfg.wiggle_amplitude * 2)),
                       round(random.gauss(0, self.cfg.wiggle_amplitude)), self.cfg)
            time.sleep(rng((0.05, 0.14)))
        time.sleep(rng(self.cfg.scan_pause))

    def _approach(self, det, fw, fh):
        cx, cy = fw / 2, fh / 2
        ex, ey = self._steer(det.cx, det.cy, cx, cy)

        centered = abs(ex) < self.cfg.aim_deadzone_px * 1.6
        self.keys.down("w")
        if random.random() < self.cfg.approach_strafe_chance:
            self.keys.hold(random.choice(("a", "d")), 0.09, 0.24)
        time.sleep(rng(self.cfg.steer_interval))
        return centered

    def _interact(self):
        self.keys.up("w")
        time.sleep(rng(self.cfg.reaction_delay))
        # sometimes a player fumbles and taps twice
        self.keys.hold("e", *self.cfg.interact_hold)
        if random.random() < 0.14:
            time.sleep(rng((0.12, 0.30)))
            self.keys.hold("e", *self.cfg.interact_hold)

    def _loot_sweep(self):
        """Look down and shuffle over the drops, tapping pickup."""
        human_move(rng_int((-8, 8)), rng_int((90, 165)), self.cfg)
        self.keys.down("w")
        for _ in range(rng_int(self.cfg.loot_taps)):
            self.keys.tap("e")
            human_move(rng_int((-26, 26)), rng_int((6, 26)), self.cfg)
            time.sleep(rng((0.10, 0.22)))
        self.keys.up("w")
        human_move(0, rng_int((-40, -70)), self.cfg)

    # ---------- main step ----------
    def step(self):
        frame = self.cap.grab()
        if frame is None:
            return
        fh, fw = frame.shape[:2]

        dets = self.vision.detect(frame, self.cfg)
        tracks = self.tracker.update(dets)

        # sticky target lock
        if self.locked_id != -1:
            held = next((t for t in tracks if t.id == self.locked_id
                         and t.hits >= self.cfg.persistence_frames), None)
            self.target = held
            self.target_lost = 0 if held else self.target_lost + 1
        else:
            self.target = self.tracker.best()

        if self.debug:
            for t in tracks:
                col = (0, 255, 0) if t is self.target else (90, 90, 90)
                cv2.rectangle(frame, (t.x, t.y), (t.x + t.w, t.y + t.h), col, 2)
            cv2.imshow("venice-chestbot", frame)
            cv2.waitKey(1)

        if self.target is None or self.target_lost > self.cfg.tracker_max_age:
            self.locked_id = -1
            self._scan()
            return

        self.locked_id = self.target.id

        # random distraction
        if random.random() < self.cfg.distract_chance:
            release_all(self.keys)
            time.sleep(rng(self.cfg.distract_duration))
            return

        if self.target.h >= self.cfg.close_bbox_h:
            centered = self._approach(self.target, fw, fh)
            if centered:
                self._interact()
                self._loot_sweep()
                time.sleep(rng(self.cfg.scan_pause))
                self.locked_id = -1
        else:
            self._approach(self.target, fw, fh)
