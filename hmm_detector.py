"""
Hidden Markov Model detector for trap/bomb probability estimation.
"""

import random
from constants import GRID_SIZE, BOMB, WALL


class HMMDetector:
    """
    Simple Hidden Markov Model for trap/bomb detection.

    Hidden state H(r,c) ∈ {danger, safe}
    Prior  P(danger) = ratio of danger cells in grid.

    Observation model (noisy sensor):
      P(obs=1 | danger) = 0.85   (true positive)
      P(obs=1 | safe)   = 0.15   (false positive)

    After scanning, belief is updated via Bayes rule:
      P(danger | obs) ∝ P(obs | danger) * P(danger)

    The displayed number is P(danger | observations) × 100 (%).
    Multiple scans accumulate (sequential Bayesian update).
    """

    P_TRUE_POS  = 0.85   # sensor says danger when cell IS danger
    P_FALSE_POS = 0.15   # sensor says danger when cell is safe

    def __init__(self, grid):
        n_danger = sum(1 for row in grid for c in row if c == BOMB)
        n_total  = GRID_SIZE * GRID_SIZE
        prior    = n_danger / max(n_total, 1)
        # belief[r][c] = P(danger at (r,c))
        self.belief  = [[prior] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.scanned = set()   # cells already revealed as safe/danger

    def scan_adjacent(self, pos, grid):
        """
        Scan the 8 neighbours (and the cell itself) around pos.
        For each neighbour simulate a noisy observation and perform a
        Bayesian belief update.  Returns list of (r, c, pct) for display.
        """
        r0, c0 = pos
        results = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r0 + dr, c0 + dc
                if not (0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE):
                    continue
                if grid[nr][nc] == WALL:
                    continue

                is_danger = grid[nr][nc] == BOMB
                obs = random.random() < (self.P_TRUE_POS if is_danger
                                         else self.P_FALSE_POS)

                p = self.belief[nr][nc]
                if obs:
                    p = (self.P_TRUE_POS * p /
                         (self.P_TRUE_POS * p +
                          self.P_FALSE_POS * (1 - p) + 1e-9))
                else:
                    p_safe = 1 - p
                    p = ((1 - self.P_TRUE_POS) * p /
                         ((1 - self.P_TRUE_POS) * p +
                          (1 - self.P_FALSE_POS) * p_safe + 1e-9))

                self.belief[nr][nc] = max(0.0, min(1.0, p))
                self.scanned.add((nr, nc))
                results.append((nr, nc, int(self.belief[nr][nc] * 100)))
        return results

    def mark_safe(self, r, c):
        self.belief[r][c] = 0.0
        self.scanned.add((r, c))

    def mark_danger(self, r, c):
        self.belief[r][c] = 1.0
        self.scanned.add((r, c))
