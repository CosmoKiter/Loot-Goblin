"""Golden-glow chest detection with persistence gating and centroid tracking."""
import cv2
import numpy as np
from dataclasses import dataclass, field

GOLD_LO = np.array([13, 110, 130], np.uint8)
GOLD_HI = np.array([40, 255, 255], np.uint8)
SPEC_LO = np.array([0, 0, 235], np.uint8)
SPEC_HI = np.array([45, 90, 255], np.uint8)

K_CLOSE = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
K_OPEN = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))


@dataclass
class Detection:
    x: int
    y: int
    w: int
    h: int
    score: float
    hits: int = 0
    id: int = -1

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    @property
    def area(self) -> int:
        return self.w * self.h


def _mask_hud(frame, cfg):
    h, w = frame.shape[:2]
    out = frame.copy()
    for (x0, y0, x1, y1) in (cfg.mask_top_left, cfg.mask_bottom_right, cfg.mask_bottom_left):
        out[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = 0
    return out


def detect(frame, cfg) -> list[Detection]:
    frame = _mask_hud(frame, cfg)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    gold = cv2.inRange(hsv, GOLD_LO, GOLD_HI)
    spec = cv2.inRange(hsv, SPEC_LO, SPEC_HI)
    mask = cv2.bitwise_or(gold, cv2.bitwise_and(spec, gold if gold.any() else spec))

    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, K_CLOSE, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, K_OPEN, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in contours:
        area = cv2.contourArea(c)
        if not (cfg.min_blob_area <= area <= cfg.max_blob_area):
            continue
        x, y, w, h = cv2.boundingRect(c)
        if h == 0:
            continue
        aspect = w / h
        if not (cfg.min_aspect <= aspect <= cfg.max_aspect):
            continue
        solidity = area / float(w * h)
        if solidity < cfg.min_solidity:
            continue

        # chests are roughly square-ish and sit in a glow halo
        score = solidity * (1.0 if 0.7 <= aspect <= 1.6 else 0.6) * min(area / 4000, 1.6)
        out.append(Detection(x, y, w, h, score))

    return _nms(out, 0.35)


def _nms(dets, thresh):
    if not dets:
        return []
    dets = sorted(dets, key=lambda d: d.score, reverse=True)
    keep = []
    for d in dets:
        if all(_iou(d, k) < thresh for k in keep):
            keep.append(d)
    return keep


def _iou(a, b):
    ax2, ay2 = a.x + a.w, a.y + a.h
    bx2, by2 = b.x + b.w, b.y + b.h
    ix = max(0, min(ax2, bx2) - max(a.x, b.x))
    iy = max(0, min(ay2, by2) - max(a.y, b.y))
    inter = ix * iy
    if inter == 0:
        return 0.0
    return inter / float(a.w * a.h + b.w * b.h - inter)


class Tracker:
    """Confirms blobs over N frames so sparkles never trigger a false approach."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.tracks: list[Detection] = []
        self._next_id = 0

    def update(self, dets: list[Detection]) -> list[Detection]:
        for t in self.tracks:
            t.hits -= 1

        for d in dets:
            best, best_d = None, self.cfg.tracker_gate_px
            for t in self.tracks:
                dist = ((t.cx - d.cx) ** 2 + (t.cy - d.cy) ** 2) ** 0.5
                if dist < best_d:
                    best, best_d = t, dist
            if best is not None:
                best.x, best.y, best.w, best.h = d.x, d.y, d.w, d.h
                best.score = d.score
                best.hits = min(best.hits + 2, 12)
            else:
                d.id = self._next_id
                self._next_id += 1
                d.hits = 1
                self.tracks.append(d)

        self.tracks = [t for t in self.tracks if t.hits > -self.cfg.tracker_max_age]
        return self.tracks

    def best(self) -> Detection | None:
        live = [t for t in self.tracks if t.hits >= self.cfg.persistence_frames]
        if not live:
            return None
        return max(live, key=lambda t: t.score * (t.area ** 0.35))
