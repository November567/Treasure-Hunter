"""
Shared constants, colours, and cell-type definitions for Treasure Hunter.
"""

# ── Grid / display ──────────────────────────────────────────────────────────
GRID_SIZE     = 8
CELL_PX       = 72
PANEL_W       = 290
FPS           = 60
MAX_TURNS     = 60
MINIMAX_DEPTH = 3
AI_DELAY_MS   = 500
TRAP_PENALTY  = 8
HMM_TURNS_MAX = 5   # HMM detector active for N turns

SCREEN_W = GRID_SIZE * CELL_PX + PANEL_W
SCREEN_H = GRID_SIZE * CELL_PX

# ── Cell types ───────────────────────────────────────────────────────────────
EMPTY    = 0
TREASURE = 1
WEAPON   = 3
WALL     = 4
BOMB     = 5   # hidden; 2 hits = explosion
HMM_ITEM = 6   # collect → HMM scan ability

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

# ── Colour palette ───────────────────────────────────────────────────────────
C = {
    "bg":        ( 10,  14,  30),
    "grid_bg":   ( 18,  28,  55),
    "grid_line": ( 35,  55, 100),
    "wall":      ( 42,  42,  65),
    "treasure":  (255, 210,  30),
    "weapon":    (  0, 210, 240),
    "empty":     ( 22,  36,  70),
    "bomb":      (255,  80,   0),
    "hmm_item":  (180,   0, 255),
    "player_fg": (  0, 230, 118),
    "ai_fg":     (255,  82,  82),
    "panel_bg":  ( 12,  18,  40),
    "text":      (200, 210, 240),
    "dim":       ( 80,  90, 120),
    "gold":      (255, 200,   0),
    "white":     (255, 255, 255),
    "log_treas": (255, 230,  80),
    "log_weap":  ( 80, 220, 255),
    "log_atk":   (255, 150,  50),
    "log_bomb":  (255,  80,   0),
    "log_hmm":   (200,  80, 255),
    "log_info":  (170, 185, 220),
    "hud_green": (  0, 230, 118),
    "hud_red":   (255,  82,  82),
    "lock_tint": (255, 180,   0),
    "respawn":   (255,  60,  60),
    "warn_bomb": (255, 140,   0),
}
