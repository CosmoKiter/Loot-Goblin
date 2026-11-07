"""Fast screen grab. Uses DXGI (dxcam) when present, falls back to mss."""
import numpy as np

try:
    import dxcam
    _HAS_DXCAM = True
except Exception:
    _HAS_DXCAM = False

import mss


class Capture:
    def __init__(self, region=None, max_width=1600):
        self.region = region
        self.max_width = max_width
        self._cam = None
        self._sct = None

        if _HAS_DXCAM:
            self._cam = dxcam.create(output_color="BGR")
        else:
            self._sct = mss.mss()

    def grab(self) -> np.ndarray | None:
        if self._cam is not None:
            frame = self._cam.grab(region=self.region)
        else:
            mon = self.region and {
                "left": self.region[0], "top": self.region[1],
                "width": self.region[2] - self.region[0],
                "height": self.region[3] - self.region[1],
            } or self._sct.monitors[1]
            frame = np.array(self._sct.grab(mon))[:, :, :3]

        if frame is None:
            return None

        h, w = frame.shape[:2]
        if w > self.max_width:
            s = self.max_width / w
            import cv2
            frame = cv2.resize(frame, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
        return frame

    def close(self):
        if self._cam is not None:
            try:
                self._cam.release()
            except Exception:
                pass
