# Loot-Goblin
External chest-farming bot for Fortnite. Screen-capture + OpenCV detection, humanized mouse paths, no memory reading and no aimbot. Runs on Python, needs no injection.


## Setup

Follow this in order. Steps 1-4 are one-time; steps 5-8 are per-machine
calibration and must be redone if you change resolution, monitor, or HUD scale.

### 1. Requirements

| Item | Value |
|---|---|
| OS | Windows 10 21H2+ or Windows 11 |
| Python | 3.10, 3.11, or 3.12 (3.13 breaks `dxcam` wheels) |
| Displays | exactly one monitor connected |
| GPU | anything DX11-capable |
| Access | local admin |

Multi-monitor works but requires setting `region` manually (see step 7).

### 2. Install

Open PowerShell in the repo folder:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If `dxcam` fails to build, the bot silently falls back to `mss` — it still
runs, just at lower capture rate. Do not try to fix it unless the debug
overlay is visibly laggy.

### 3. Fortnite video settings

Settings > Video. Use these exact values:

| Setting | Value | Why |
|---|---|---|
| Window Mode | **Windowed Fullscreen** | DXGI capture fails on exclusive fullscreen |
| Resolution | 1920x1080 or lower | 1440p+ overflows the blob area filter |
| Frame Rate Limit | **60** | consistent capture timing, GPU not pegged |
| Rendering Mode | **DirectX 11** | DX12 and Performance Mode change chest glow hue |
| 3D Resolution | 100% | below 100 softens gold edges |
| View Distance | Far | chests must render before they can be detected |
| Shadows | Off | less clutter under chests |
| Anti-Aliasing | Off or FXAA | TAA smears the gold contour |
| Motion Blur | Off | |
| Post Processing | Off | shifts gold saturation out of `GOLD_LO`/`GOLD_HI` |
| Show FPS | Off | overlay digits pollute detection |

### 4. Input settings

Settings > Keyboard & Mouse:

- Interact = **E**
- Sprint = **Left Shift**
- Movement = default WASD
- **Mouse acceleration / "Enhance pointer precision" = OFF** (Windows > Mouse settings > Additional options > Pointer Options)
- Set in-game sensitivity to **0.60 or lower**. Higher values make
  `aim_gain` overshoot; retune it if you change this.

In the Epic Games Launcher: Settings > uncheck **Enable Overlay**.

### 5. Elevation

If Fortnite runs elevated, the bot must too, or `SendInput` is ignored by the
game window. Check with Task Manager > Details > look for the "Elevated"
column. Either run both elevated, or neither.

Launch the bot from an **admin** PowerShell:

```powershell
.venv\Scripts\activate
python main.py --dry
```

### 6. Dry run

`--dry` detects but sends no input. Drop into **Creative**, stand in a room
with chests, and confirm the console prints detections. If it prints nothing,
your video settings or `GOLD_LO`/`GOLD_HI` are off — fix that before moving on.

### 7. Set the capture region

Only needed for multi-monitor or a non-primary display. Determine the game
window's screen coordinates, then in `config.py`:

```python
region = (0, 0, 1920, 1080)   # (left, top, right, bottom)
```

Leave `region = None` for a single-monitor fullscreen game.

### 8. Calibrate the detector

Run `python main.py --debug` and watch the boxes. Boxes must sit on chests and
nothing else. Adjust **one** dial at a time, in this order:

| Symptom | Dial | Direction |
|---|---|---|
| Boxes on floor loot, gold trim, sunset sky | `min_solidity` | up, 0.42 -> 0.60 |
| Boxes on distant sparkle particles | `persistence_frames` | up, 3 -> 6 |
| Chests missed at mid range | `min_blob_area` | down, 200 -> 120 |
| Chests missed entirely, nothing detects | widen `GOLD_LO`/`GOLD_HI` in `vision.py` | lower `GOLD_LO[1]` to 90 |
| Walks past chests without stopping | `close_bbox_h` | down, 150 -> 110 |
| Stops too far from the chest | `close_bbox_h` | up, 150 -> 190 |
| Camera jitters instead of settling | `aim_deadzone_px` | up, 26 -> 40 |
| Camera swings past the chest | `aim_gain` | down, 0.40 -> 0.28 |
| Never presses E | `aim_deadzone_px` | up — the deadzone is too tight to satisfy |

Test on **Creative islands with a chest spawn**, not in a live match, until the
boxes are clean.

### 9. Live run

```powershell
python main.py
```

Alt-tab into Fortnite within 5 seconds. F7 pauses, F8 stops. Cap sessions at
1-2 hours.

### Troubleshooting

| Problem | Cause |
|---|---|
| Camera doesn't move at all | bot not elevated while game is; or wrong window focused |
| Moves but E never fires | `aim_deadzone_px` too tight,
