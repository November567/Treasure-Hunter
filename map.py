"""
Grid generation for Treasure Hunter.
"""

import random
from constants import GRID_SIZE, EMPTY, WALL, BOMB, TREASURE, WEAPON, HMM_ITEM


def generate_grid():
    grid = [[EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)]

    def place(ct, n):
        done = 0
        for _ in range(4000):
            r = random.randint(0, GRID_SIZE - 1)
            c = random.randint(0, GRID_SIZE - 1)
            if grid[r][c] != EMPTY:
                continue
            if r <= 1 and c <= 1:
                continue
            if r >= GRID_SIZE - 2 and c >= GRID_SIZE - 2:
                continue
            grid[r][c] = ct
            done += 1
            if done == n:
                break

    place(WALL,     8)
    place(BOMB,     3)   # hidden bombs (2-hit)
    place(TREASURE, 7)
    place(WEAPON,   2)
    place(HMM_ITEM, 2)   # HMM detector pickups
    return grid
