"""
All Pygame rendering for Treasure Hunter.
"""

import pygame
from constants import (
    GRID_SIZE, CELL_PX, PANEL_W, SCREEN_W, SCREEN_H, MAX_TURNS,
    EMPTY, TREASURE, WEAPON, WALL, BOMB, HMM_ITEM,
    C,
)

# ── Visual maps ──────────────────────────────────────────────────────────────

CELL_COL_VIS = {
    EMPTY:    C["empty"],
    WALL:     C["wall"],
    TREASURE: C["treasure"],
    BOMB:     C["empty"],       # hidden
    WEAPON:   C["weapon"],
    HMM_ITEM: C["hmm_item"],
}
CELL_LBL_VIS = {
    TREASURE: "GEM",
    WEAPON:   "SWD",
    WALL:     "|||",
    HMM_ITEM: "HMM",
}

# ── Low-level helpers ────────────────────────────────────────────────────────

def rr(surf, col, rect, rad=10, border=None, bw=1):
    """Draw a rounded rectangle, optionally with a border."""
    pygame.draw.rect(surf, col, rect, border_radius=rad)
    if border:
        pygame.draw.rect(surf, border, rect, bw, border_radius=rad)


def lerp_col(a, b, t):
    return tuple(max(0, min(255, int(a[i] + (b[i] - a[i]) * t))) for i in range(3))


# ── Font loader ──────────────────────────────────────────────────────────────

def load_fonts():
    try:
        return {
            "big":   pygame.font.SysFont("consolas", 22, bold=True),
            "med":   pygame.font.SysFont("consolas", 16, bold=True),
            "sm":    pygame.font.SysFont("consolas", 13),
            "cell":  pygame.font.SysFont("consolas", 11, bold=True),
            "title": pygame.font.SysFont("georgia",  26, bold=True),
            "pct":   pygame.font.SysFont("consolas", 10, bold=True),
        }
    except Exception:
        fallback = pygame.font.Font(None, 18)
        return {k: fallback for k in ("big", "med", "sm", "cell", "title", "pct")}


# ── Main draw functions ──────────────────────────────────────────────────────

def draw_grid(screen, state, fonts, hmm_display):
    """Render the game grid, entities, HMM overlays, and respawn flash."""

    def crect(r, c):
        return pygame.Rect(c * CELL_PX + 4, r * CELL_PX + 4, CELL_PX - 8, CELL_PX - 8)

    pygame.draw.rect(screen, C["grid_bg"],
                     (0, 0, GRID_SIZE * CELL_PX, GRID_SIZE * CELL_PX))

    for i in range(GRID_SIZE + 1):
        pygame.draw.line(screen, C["grid_line"], (i * CELL_PX, 0), (i * CELL_PX, SCREEN_H))
        pygame.draw.line(screen, C["grid_line"], (0, i * CELL_PX), (GRID_SIZE * CELL_PX, i * CELL_PX))

    # Refresh HMM display from latest scan results
    for r2, c2, pct in state.hmm_scan_results:
        hmm_display[(r2, c2)] = pct

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            rect = crect(r, c)
            ct       = state.grid[r][c]
            revealed_bomb = (r, c) in state.revealed_bombs and ct == BOMB
            # Gem is visible if: on the grid unrevealed=hidden, OR just collected (in flash)
            gem_visible = (r, c) in state.revealed_gems

            if revealed_bomb:
                col = C["bomb"]
            elif ct == TREASURE and not gem_visible:
                col = C["empty"]   # hidden until discovered
            elif ct == EMPTY and gem_visible:
                col = C["treasure"]  # just collected — show during flash
            else:
                col = CELL_COL_VIS.get(ct, C["empty"])

            fk = (r, c)
            if fk in state.flash:
                col = lerp_col(col, (180, 255, 180), state.flash[fk] / 14.0)

            rr(screen, col, rect, rad=8, border=C["grid_line"])

            if revealed_bomb:
                lbl = "💣"
            elif ct == TREASURE and not gem_visible:
                lbl = ""           # invisible
            elif ct == EMPTY and gem_visible:
                lbl = "GEM"        # show briefly after collection
            else:
                lbl = CELL_LBL_VIS.get(ct, "")
            if lbl:
                ts = fonts["cell"].render(lbl, True, C["bg"])
                screen.blit(ts, ts.get_rect(center=rect.center))

            # HMM probability overlay
            if (r, c) in hmm_display and ct not in (WALL, TREASURE, WEAPON, HMM_ITEM):
                pct = hmm_display[(r, c)]
                danger_t = pct / 100.0
                pcol = lerp_col((60, 200, 80), (220, 40, 40), danger_t)
                bg_s = pygame.Surface((CELL_PX - 8, 16), pygame.SRCALPHA)
                bg_s.fill((0, 0, 0, 140))
                screen.blit(bg_s, (rect.x, rect.bottom - 17))
                pt = fonts["pct"].render(f"{pct}%", True, pcol)
                screen.blit(pt, pt.get_rect(centerx=rect.centerx, bottom=rect.bottom - 2))

    # Entities
    for entity, label, ecol in [
        (state.player, "YOU", C["player_fg"]),
        (state.ai,     "BOT", C["ai_fg"]),
    ]:
        r, c = entity.pos
        rect = crect(r, c)
        rr(screen, ecol, rect, rad=10, border=C["white"], bw=2)
        t = fonts["med"].render(label, True, C["bg"])
        screen.blit(t, t.get_rect(center=rect.center))
        if entity.weapon:
            wt = fonts["cell"].render("SWD", True, C["bg"])
            screen.blit(wt, wt.get_rect(bottomright=rect.bottomright))

    # Red respawn flash
    if state.respawn_flash > 0:
        alpha = int(180 * state.respawn_flash / 60)
        fs = pygame.Surface((GRID_SIZE * CELL_PX, SCREEN_H), pygame.SRCALPHA)
        fs.fill((255, 30, 30, alpha))
        screen.blit(fs, (0, 0))


def draw_panel(screen, state, fonts):
    """Render the right-side HUD panel."""
    px = GRID_SIZE * CELL_PX
    pygame.draw.rect(screen, C["panel_bg"], (px, 0, PANEL_W, SCREEN_H))
    pygame.draw.line(screen, C["grid_line"], (px, 0), (px, SCREEN_H), 2)
    cx = px + PANEL_W // 2
    y  = 12

    t = fonts["title"].render("TREASURE", True, C["gold"])
    screen.blit(t, t.get_rect(centerx=cx, top=y)); y += 30
    t = fonts["med"].render("HUNTER", True, C["dim"])
    screen.blit(t, t.get_rect(centerx=cx, top=y)); y += 22
    t = fonts["sm"].render("[ MINIMAX + A* + HMM ]", True, C["weapon"])
    screen.blit(t, t.get_rect(centerx=cx, top=y)); y += 26

    # Turn progress bar
    left = MAX_TURNS - state.turn
    bw   = PANEL_W - 24
    br   = pygame.Rect(px + 12, y, bw, 14)
    pygame.draw.rect(screen, C["dim"], br, border_radius=6)
    fill = int(bw * left / MAX_TURNS)
    fc   = C["hud_green"] if left > 20 else (255, 200, 0) if left > 10 else C["hud_red"]
    if fill > 0:
        pygame.draw.rect(screen, fc, (px + 12, y, fill, 14), border_radius=6)
    lbl_surf = fonts["cell"].render(f"TURNS LEFT: {left}/{MAX_TURNS}", True, C["text"])
    screen.blit(lbl_surf, lbl_surf.get_rect(center=br.center))
    y += 26

    # Turn indicator
    if state.phase == "player_turn":
        ti_col, ti_txt = C["player_fg"], "YOUR TURN  ▶"
    elif state.phase == "ai_thinking":
        ti_col, ti_txt = C["lock_tint"],  "AI MOVING... ⏳"
    else:
        ti_col, ti_txt = C["dim"],         "GAME OVER"
    ti_surf = fonts["sm"].render(ti_txt, True, ti_col)
    screen.blit(ti_surf, ti_surf.get_rect(centerx=cx, top=y))
    y += 22

    # Score cards
    for label, entity, ecol in [
        ("PLAYER", state.player, C["player_fg"]),
        ("AI BOT", state.ai,     C["ai_fg"]),
    ]:
        card = pygame.Rect(px + 10, y, PANEL_W - 20, 64)
        rr(screen, C["grid_bg"], card, rad=10, border=ecol, bw=2)
        screen.blit(fonts["sm"].render(label, True, ecol), (card.x + 10, card.y + 6))
        score_col = C["hud_red"] if entity.score < 0 else C["white"]
        screen.blit(fonts["big"].render(f"{entity.score} pts", True, score_col),
                    (card.x + 10, card.y + 26))
        if entity.weapon:
            screen.blit(fonts["sm"].render("⚔ Armed", True, C["weapon"]),
                        (card.x + 10, card.y + 46))
        y += 74

    # Bomb hit counter
    bh     = state.player_bomb_hits
    bh_col = C["warn_bomb"] if bh > 0 else C["dim"]
    bh_txt = f"💣 Bomb hits: {bh}/2  — BOOM next!" if bh > 0 else "💣 Bomb hits: 0/2"
    bh_surf = fonts["sm"].render(bh_txt, True, bh_col)
    screen.blit(bh_surf, bh_surf.get_rect(centerx=cx, top=y))
    y += 20

    # HMM status
    hmm_col = C["hmm_item"] if state.player_has_hmm else C["dim"]
    hmm_txt = (f"🔍 HMM: {state.hmm_turns_left} turn(s) left"
               if state.player_has_hmm else "🔍 HMM: none (find HMM item)")
    hmm_surf = fonts["sm"].render(hmm_txt, True, hmm_col)
    screen.blit(hmm_surf, hmm_surf.get_rect(centerx=cx, top=y))
    y += 20
    if state.player_has_hmm:
        sub = fonts["cell"].render("scanning each step → % shown", True, C["dim"])
        screen.blit(sub, sub.get_rect(centerx=cx, top=y))
    y += 20

    # Legend
    y += 4
    for lbl, col, desc in [
        ("GEM", C["treasure"],  "+10  Treasure"),
        ("SWD", C["weapon"],    "+ 2  Weapon ⚔"),
        ("HMM", C["hmm_item"],  "+ 3  HMM Detector (5 turns)"),
        ("💣",  C["bomb"],      "     Bomb hit 2/2 → respawn"),
    ]:
        pygame.draw.rect(screen, col, (px + 10, y, 28, 18), border_radius=4)
        s = fonts["cell"].render(lbl, True, C["bg"])
        screen.blit(s, s.get_rect(center=(px + 24, y + 9)))
        screen.blit(fonts["sm"].render(desc, True, C["dim"]), (px + 44, y + 2))
        y += 22

    # Event log
    y += 6
    s = fonts["sm"].render("── Event Log ──", True, C["dim"])
    screen.blit(s, s.get_rect(centerx=cx, top=y)); y += 16
    for msg, ck in state.log[:9]:
        screen.blit(fonts["cell"].render(msg, True, C[ck]), (px + 10, y))
        y += 15
        if y > SCREEN_H - 38:
            break

    screen.blit(fonts["cell"].render("Arrow/WASD  R=restart  ESC=quit",
                                     True, C["dim"]), (px + 10, SCREEN_H - 18))


def draw_gameover(screen, state, fonts):
    """Render the game-over overlay modal."""
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 175))
    screen.blit(ov, (0, 0))

    cx, cy = SCREEN_W // 2, SCREEN_H // 2
    box = pygame.Rect(cx - 185, cy - 145, 370, 290)
    rr(screen, C["panel_bg"], box, rad=18, border=C["gold"], bw=3)

    ps, ais = state.player.score, state.ai.score
    if   ps > ais:  w, wc = "PLAYER WINS!", C["player_fg"]
    elif ais > ps:  w, wc = "AI WINS!",     C["ai_fg"]
    else:            w, wc = "DRAW!",         C["gold"]

    def tc(txt, fnt, col, yo):
        s = fnt.render(txt, True, col)
        screen.blit(s, s.get_rect(centerx=cx, top=cy - 130 + yo))

    tc("GAME OVER",                fonts["title"], C["gold"],    0)
    tc(w,                          fonts["big"],   wc,          44)
    tc(state.gameover_reason,      fonts["sm"],    C["text"],   84)
    tc(f"Player : {ps} pts",       fonts["med"],   C["text"],  110)
    tc(f"AI Bot  : {ais} pts",     fonts["med"],   C["text"],  135)
    tc("R = restart   ESC = quit", fonts["sm"],    C["dim"],   185)
