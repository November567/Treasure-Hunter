# Treasure Hunter

A turn-based Player vs AI game built with Pygame. Collect gems, pick up weapons, avoid hidden bombs, and outscore the AI bot before time runs out.

## Gameplay

| Item | Effect |
|------|--------|
| 💎 GEM | +10 pts |
| ⚔ SWD (Sword) | +2 pts, enables attacks |
| 🔍 HMM | +3 pts, reveals nearby bomb probabilities for 5 turns |
| 💣 BOMB | Hidden. 1st step = warning. 2nd step = −16 pts + respawn |

**Win conditions**
- All gems collected → highest score wins
- 60 turns elapsed → highest score wins
- Either player's score drops below 0 → opponent wins immediately

**Combat** — when adjacent to the opponent with a sword:
- Only attacker armed → attacker wins, opponent −8 pts + respawn
- Both armed → 50/50 duel, loser −8 pts + respawn, both lose swords

**Controls**

| Key | Action |
|-----|--------|
| Arrow keys / WASD | Move |
| R | Restart |
| ESC / Q | Quit |

## AI

The bot uses a combination of three algorithms:

- **Minimax + alpha-beta pruning** (depth 3) — evaluates future moves considering both scores
- **A\* pathfinding** — navigates toward targets, avoiding known bombs
- **Hidden Markov Model (HMM)** — probabilistic bomb detection via noisy sensor scans

The heuristic is score-aware: when losing the AI collects items more aggressively; when its score is dangerously low it flees combat; when the player is near death and the AI is armed it prioritises the kill.

## Requirements

```
pip install pygame
```

Python 3.8+

## Run

```
python main.py
```

## Project Structure

```
main.py          — game loop and entry point
game.py          — GameState (rules, turns, combat, bombs)
ai_agent.py      — A*, minimax, heuristic, AI decision logic
renderer.py      — all Pygame drawing
hmm_detector.py  — Bayesian HMM sensor model
map.py           — procedural grid generation
entity.py        — Entity class (player / AI)
constants.py     — shared constants and colour palette
sound/           — audio assets
```
