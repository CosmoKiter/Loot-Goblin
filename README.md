# Loot-Goblin
External chest-farming bot for Fortnite. Screen-capture + OpenCV detection, humanized mouse paths, no memory reading and no aimbot. Runs on Python, needs no injection.


## Setup
1. `pip install -r requirements.txt`
2. Fortnite: windowed or borderless, 1080p or lower, 100% render scale, no motion blur.
   Turn OFF "Post Processing" — it shifts the gold hue of chest glow.
3. Bind interact to E, sprint to Shift. Default WASD.
4. `python main.py --debug` first, watch the boxes lock onto chests.
5. `python main.py` for real runs.

## Calibration
Run `--debug` and adjust in config.py until boxes sit on chests only:
- Boxes on random gold loot/floor: raise `min_blob_area`, `min_solidity`.
- Chests missed: lower `min_blob_area`, widen `GOLD_LO`/`GOLD_HI` in vision.py.
- Stops too far away: lower `close_bbox_h`.

## Why it doesn't look like a bot
- Mouse always travels a curved bezier, never a straight line to target
- 180-340ms reaction before every E, sometimes a fumbled double-tap
- Gaussian jitter on every camera correction
- Random strafe while walking, random 0.7-2.4s distractions
- Scan pans are random-length arcs with idle wiggle, not a metronome
- No head-lock, no snap: chest center is the target and it drifts around it

## Risk
External + screen-only + simulated input is the lowest-footprint class of
cheat. Not undetectable — EAC can flag it — but it has no signature to
scan for beyond "inhuman uptime". Cap sessions at 1-2 hours.
