# Raycasting AI 2.1

A mobile-friendly 2.5D first-person shooter prototype inspired by the original `Dungjax/Raycasting` project. It keeps the Python + Pygame direction but uses a DDA raycaster and grid-based gameplay systems, with on-screen multitouch controls for Android/Pydroid.

## Features

- **DDA wall renderer** with perpendicular-distance correction, distance fog and procedural wall patterns.
- **Depth-tested billboard enemies** so walls correctly occlude enemies behind them.
- **A* enemy navigation** on a tile grid, with line-of-sight checks and melee attacks.
- **Delta-time movement**, diagonal speed normalization, sprinting and wall sliding.
- **Hitscan weapon**, magazine, fire cooldown and reload timer.
- **Android multitouch controls**: left virtual joystick, right-side drag look, fire, reload and sprint buttons.
- **HUD and minimap**, generated without external art or audio assets.
- **Unit tests** for DDA edge cases, collision, visibility and path finding.

## Run on Android with Pydroid 3

1. Install or update **Pydroid 3**.
2. Open Pydroid's Pip/package installer and install **pygame** (Pygame 2). Pydroid lists Pygame 2 as a supported library.
3. Download this repository as a ZIP from GitHub and extract it.
4. In Pydroid, open the extracted folder and run `main.py`.
5. Rotate the phone to **landscape** before starting the game.

No Pymunk, external images, sprite sheets or sound files are required.

### Touch controls

| Screen area | Action |
| --- | --- |
| Left virtual joystick | Move and strafe |
| Drag on the open right side | Turn / look |
| **FIRE** | Hold to fire |
| **R** | Reload |
| **RUN** | Hold to sprint |

Use two or more fingers at once to move, aim and fire together. Touch input uses Pygame 2 finger events.

## Run on desktop

Requirements: Python 3.10+ and Pygame 2.5+.

```bash
python -m pip install -r requirements.txt
python main.py
```

| Input | Action |
| --- | --- |
| `W` / `S` or `↑` / `↓` | Move forward / backward |
| `A` / `D` | Strafe left / right |
| Mouse | Look around |
| `Q` / `E` | Turn left / right |
| `Left Shift` | Sprint |
| Left mouse button | Fire (hold for automatic fire) |
| `R` | Reload |
| `Tab` | Release / recapture mouse |
| `Esc` | Exit |

## Tests

```bash
python -m unittest discover -s tests -v
```

## Project layout

```text
raycasting-AI/
├── main.py
├── requirements.txt
├── raycasting_ai/
│   ├── config.py      # Tunable constants and mobile render resolution
│   ├── world.py       # Tile map, DDA ray cast, collision, A*
│   ├── entities.py    # Player and enemy simulation
│   ├── renderer.py    # Software renderer, HUD and virtual controls
│   └── game.py        # Pygame loop, desktop and Android controls
└── tests/
    └── test_world.py
```

## Design notes

The world is a 2D tile grid. Each screen column casts one ray; DDA advances from grid boundary to grid boundary until it enters a solid tile. The renderer applies a cosine correction to the hit distance to reduce fisheye distortion. The same grid is used for collision and A* path finding, keeping the simulation deterministic and easy to test.

The internal render target is 480x270 to reduce the number of rays and scale to the device display. The game targets 45 FPS on Android and 60 FPS on desktop. Visuals are procedural so a clean checkout does not need separate asset folders.
