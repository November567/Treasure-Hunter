"""
AI decision-making for Treasure Hunter.

Contains:
  - astar_ai      : A* pathfinding (avoids known bombs)
  - minimax       : alpha-beta minimax tree search
  - ai_decide     : target selection + path planning
"""

import heapq
import random
from constants import GRID_SIZE, EMPTY, WALL, TREASURE, WEAPON, HMM_ITEM, DIRS, MINIMAX_DEPTH


# ── A* pathfinding ───────────────────────────────────────────────────────────

def astar_ai(grid, start, goal, known_bombs=None):
    """
    AI pathfinding:
    - Avoids WALL cells always.
    - Treats cells in known_bombs with high cost (avoids them).
    - Treats unseen BOMB cells as empty (AI doesn't know yet).
    """
    if known_bombs is None:
        known_bombs = set()
    sr, sc = start
    gr, gc = goal
    h = lambda r, c: abs(r - gr) + abs(c - gc)
    heap = [(h(sr, sc), 0, sr, sc, [(sr, sc)])]
    visited = {}
    while heap:
        f, g, r, c, path = heapq.heappop(heap)
        if (r, c) in visited and visited[(r, c)] <= g:
            continue
        visited[(r, c)] = g
        if r == gr and c == gc:
            return path
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE):
                continue
            if grid[nr][nc] == WALL:
                continue
            step = 6 if (nr, nc) in known_bombs else 1
            ng = g + step
            if (nr, nc) in visited and visited[(nr, nc)] <= ng:
                continue
            heapq.heappush(heap, (ng + h(nr, nc), ng, nr, nc, path + [(nr, nc)]))
    return []


# ── Minimax helpers ──────────────────────────────────────────────────────────

def _land_sim(grid, pos, score, weapon):
    """Simulate landing on a cell inside the minimax tree."""
    r, c = pos
    ct = grid[r][c]
    if ct == TREASURE:
        score += 10; grid[r][c] = EMPTY
    elif ct == WEAPON:
        score += 2;  weapon = True; grid[r][c] = EMPTY
    elif ct == HMM_ITEM:
        score += 3;  grid[r][c] = EMPTY
    # BOMB treated as empty in simulation (uncertainty)
    return score, weapon, pos[:]


def _valid_moves(grid, pos):
    out = []
    for dr, dc in DIRS:
        nr, nc = pos[0] + dr, pos[1] + dc
        if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and grid[nr][nc] != WALL:
            out.append((dr, dc))
    return out


def _heuristic(grid, p_pos, p_score, p_weapon, a_pos, a_score, a_weapon):
    # ── Score context ────────────────────────────────────────────────────────
    score_diff   = a_score - p_score
    ai_losing    = a_score < p_score
    ai_danger    = a_score < 10          # risk of dropping below 0
    player_dying = p_score < 10          # player close to game over

    # Score difference weighted heavily — it's the primary objective
    score_weight = 2.0 if ai_losing else 1.5

    # ── Item proximity ───────────────────────────────────────────────────────
    # Collect items more urgently when losing; back off when already ahead
    item_urgency = 1.8 if ai_losing else 1.0
    ai_bonus = p_penalty = 0
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if grid[r][c] in (TREASURE, WEAPON, HMM_ITEM):
                dv = 10 if grid[r][c] == TREASURE else 6 if grid[r][c] == WEAPON else 3
                ai_bonus  += dv * item_urgency / (abs(r - a_pos[0]) + abs(c - a_pos[1]) + 1)
                p_penalty += dv / (abs(r - p_pos[0]) + abs(c - p_pos[1]) + 1) * 0.6

    # ── Weapon advantage ─────────────────────────────────────────────────────
    wb = (4 if a_weapon else 0) - (4 if p_weapon else 0)

    # ── Positioning / combat ─────────────────────────────────────────────────
    dist_to_player = abs(a_pos[0] - p_pos[0]) + abs(a_pos[1] - p_pos[1])
    positioning = 0
    if a_weapon and not p_weapon:
        # Prioritise finishing the player if they're near death
        chase = 20.0 if player_dying else 8.0
        positioning = chase / (dist_to_player + 0.5)
    elif p_weapon and not a_weapon:
        # Flee harder when AI score is dangerously low
        flee = 18.0 if ai_danger else 10.0
        positioning = -flee / (dist_to_player + 0.5)
    elif p_weapon and a_weapon:
        positioning = 3.0 / (dist_to_player + 0.5)

    # ── Danger penalty ───────────────────────────────────────────────────────
    # Discourage aggressive play when AI could go below 0
    danger_penalty = -20 if ai_danger else 0

    return score_weight * score_diff + ai_bonus - p_penalty + wb + positioning + danger_penalty


def minimax(grid, p_pos, p_score, p_weapon,
            a_pos, a_score, a_weapon,
            depth, is_max, alpha=-10000, beta=10000):
    if depth == 0:
        return _heuristic(grid, p_pos, p_score, p_weapon, a_pos, a_score, a_weapon)
    moves = _valid_moves(grid, a_pos if is_max else p_pos)
    if not moves:
        return _heuristic(grid, p_pos, p_score, p_weapon, a_pos, a_score, a_weapon)

    if is_max:
        best = -10000
        for dr, dc in moves:
            ng = [row[:] for row in grid]
            nr, nc = a_pos[0] + dr, a_pos[1] + dc
            ns, nw, nap = _land_sim(ng, [nr, nc], a_score, a_weapon)
            val = minimax(ng, p_pos, p_score, p_weapon,
                          nap, ns, nw, depth - 1, False, alpha, beta)
            best = max(best, val); alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = 10000
        for dr, dc in moves:
            ng = [row[:] for row in grid]
            nr, nc = p_pos[0] + dr, p_pos[1] + dc
            ns, nw, npp = _land_sim(ng, [nr, nc], p_score, p_weapon)
            val = minimax(ng, npp, ns, nw,
                          a_pos, a_score, a_weapon, depth - 1, True, alpha, beta)
            best = min(best, val); beta = min(beta, best)
            if beta <= alpha:
                break
        return best


# ── AI decision entry point ──────────────────────────────────────────────────

def _explore_move(grid, a_pos, ai_visited):
    """Pick a random unvisited neighbour; if all visited, clear history and pick any."""
    moves = _valid_moves(grid, a_pos)
    if not moves:
        return None, []
    unvisited = [(dr, dc) for dr, dc in moves
                 if (a_pos[0] + dr, a_pos[1] + dc) not in ai_visited]
    if not unvisited:
        ai_visited.clear()
        unvisited = moves
    dr, dc = random.choice(unvisited)
    return (a_pos[0] + dr, a_pos[1] + dc), []


def ai_decide(grid, p_pos, p_score, p_weapon,
              a_pos, a_score, a_weapon, known_bombs=None, ai_visited=None):
    """
    Choose the best next position for the AI.
    Returns (next_pos, full_path).
    """
    if ai_visited is None:
        ai_visited = set()

    candidates = [(r, c) for r in range(GRID_SIZE)
                          for c in range(GRID_SIZE)
                          if grid[r][c] in (TREASURE, WEAPON, HMM_ITEM)]

    hunt_target = tuple(p_pos) if a_weapon else None

    if not candidates and not hunt_target:
        return _explore_move(grid, a_pos, ai_visited)

    best_val, best_target = -10000, None

    for tr, tc in candidates:
        ng = [row[:] for row in grid]
        ns, nw, _ = _land_sim(ng, [tr, tc], a_score, a_weapon)
        val = minimax(ng, p_pos, p_score, p_weapon,
                      [tr, tc], ns, nw, MINIMAX_DEPTH - 1, False)
        if val > best_val:
            best_val, best_target = val, (tr, tc)

    if hunt_target:
        pr, pc = hunt_target
        ng = [row[:] for row in grid]
        val = minimax(ng, p_pos, p_score, p_weapon,
                      [pr, pc], a_score, a_weapon, MINIMAX_DEPTH - 1, False)
        val += 12   # bonus for hunting
        if val > best_val:
            best_val, best_target = val, hunt_target

    if best_target is None:
        return _explore_move(grid, a_pos, ai_visited)

    path = astar_ai(grid, tuple(a_pos), best_target, known_bombs)
    if len(path) >= 2:
        return path[1], path
    if len(path) == 1:
        return path[0], path
    moves = _valid_moves(grid, a_pos)
    if not moves:
        return None, []
    dr, dc = moves[0]
    return (a_pos[0] + dr, a_pos[1] + dc), []
