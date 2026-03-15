# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Game

```bash
pip install pygame
python main.py
```

Controls: Arrow keys / WASD to move | R to restart | ESC to quit

## Architecture

The game is currently monolithic — all working logic lives in `main.py` (~946 lines). The files `game.py`, `map.py`, and `ai_agent.py` are empty placeholders for a future refactor.

### Key Constants (top of `main.py`)

| Constant | Value | Purpose |
|---|---|---|
| `GRID_SIZE` | 8 | 8×8 board |
| `CELL_PX` | 72 | Pixels per cell |
| `MAX_TURNS` | 60 | Turn limit |
| `MINIMAX_DEPTH` | 3 | AI lookahead depth |
| `AI_DELAY_MS` | 500 | Delay before AI moves |

Cell types: `EMPTY=0`, `TREASURE=1`, `WEAPON=3`, `WALL=4`, `BOMB=5`, `HMM_ITEM=6`

### Core Algorithms

- **HMMDetector** (lines 84–162): Bayesian inference for probabilistic trap/bomb detection. Updates `P(danger|obs)` using Bayes rule with hardcoded sensor accuracy (0.85 true positive, 0.15 false positive).
- **A\* pathfinding** (lines 190–222): AI navigation; known bombs add cost 6, unknown cells cost 1.
- **Minimax + alpha-beta pruning** (lines 271–302, depth 3): AI strategic decision-making. Evaluation weighs score delta, item proximity, weapon status.
- **AI decision engine** (lines 307–357): Selects targets (treasure/weapon/hunt player), then uses A* to path there.

### Game State

`GameState` (lines 372–640) owns: the grid, both `Entity` objects (player + AI), turn counter, bomb hit tracking, HMM belief map, and flash animations.

**Bomb mechanic:** Two-hit system — first step triggers a warning; second step causes respawn + penalty. AI learns bomb locations gradually via HMM scanning.

**Win conditions:** All treasures collected, 60 turns elapsed, or any entity's score drops below 0 (instant game over).

### Rendering

`draw_*` functions (lines 643–940) handle: grid cells, entity sprites, HMM probability overlays (green=safe → red=danger), and the right-side panel (scores, turn count, event log).
