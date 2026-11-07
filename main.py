import argparse
import ctypes
import sys
import time

from pynput import keyboard

from config import Config
from capture import Capture
from vision import detect
from human_input import Keys, release_all
from brain import Brain

try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--debug", action="store_true", help="show detection overlay")
    ap.add_argument("--fps", type=int, default=45)
    ap.add_argument("--dry", action="store_true", help="detect only, no input")
    args = ap.parse_args()

    cfg = Config()
    cfg.target_fps = args.fps

    cap = Capture(cfg.region, cfg.max_width)
    keys = Keys()
    brain = Brain(cfg, sys.modules["vision"], keys, cap)
    brain.debug = args.debug

    running = {"on": True, "paused": False}

    def on_press(k):
        name = getattr(k, "name", None) or str(k).lower()
        if name == cfg.panic_key:
            running["on"] = False
        elif name == cfg.pause_key:
            running["paused"] = not running["paused"]
            if running["paused"]:
                release_all(keys)

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    print(f"running — F7 pause, {cfg.panic_key.upper()} stop")
    print("alt-tab into Fortnite now (5s)")
    time.sleep(5)

    frame_budget = 1.0 / cfg.target_fps
    try:
        while running["on"]:
            t0 = time.perf_counter()
            if not running["paused"] and not args.dry:
                brain.step()
            elif args.dry:
                brain.step()
            slack = frame_budget - (time.perf_counter() - t0)
            if slack > 0:
                time.sleep(slack)
    except KeyboardInterrupt:
        pass
    finally:
        release_all(keys)
        cap.close()
        print("\nstopped, inputs released")


if __name__ == "__main__":
    main()
