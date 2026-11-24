# Raycasting AI 2.0

A rewritten 2.5D first-person shooter prototype inspired by the original `Dungjax/Raycasting` project. This version keeps the Python + Pygame direction but replaces the old physics-library-driven wall query with a compact DDA raycaster and grid-based gameplay systems.

## Features

- **DDA wall renderer** with perpendicular-distance correction, distance fog and procedural wall patterns.
- **Depth-tested billboard enemies** so walls correctly occlude enemies behind them.
- **A* enemy navigation** on a tile grid, with line-of-sight checks and melee attacks.
- **Delta-time movement**, diagonal speed normalization, sprinting and wall sliding.
- **Hitscan weapon**, magazine, fire cooldown and reload timer.
- **HUD and minimap**, generated without external art or audio assets.
- **Unit tests** for DDA edge cases, collision, visibility and path finding.

## Requirements

- Python 3.10+
- Pygame 2.5+

## Run

```bash
python -m pip install -r requirements.txt
python main.py
```

## Controls

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
raycasting-ai-v2/
├── main.py
├── raycasting_ai/
│   ├── config.py      # Tunable constants
│   ├── world.py       # Tile map, DDA ray cast, collision, A*
│   ├── entities.py    # Player and enemy simulation
│   ├── renderer.py    # Software renderer and HUD
│   └── game.py        # Pygame loop and controls
└── tests/
    └── test_world.py
```

## Design notes

The world is a 2D tile grid. Each screen column casts one ray; DDA advances from grid boundary to grid boundary until it enters a solid tile. The renderer applies a cosine correction to the hit distance to reduce fisheye distortion. The same grid is used for collision and A* path finding, keeping the simulation deterministic and easy to test.

The prototype intentionally uses procedural visuals so it runs from a clean checkout without copying the original project's sprite folders or sound files. It is a foundation for bringing back custom textures, animated character sheets, touch controls and richer weapons in later iterations.
