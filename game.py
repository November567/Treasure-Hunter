"""
GameState — central state manager for Treasure Hunter.
"""

import random
from constants import (
    GRID_SIZE, MAX_TURNS, AI_DELAY_MS, TRAP_PENALTY, HMM_TURNS_MAX,
    EMPTY, TREASURE, WEAPON, WALL, BOMB, HMM_ITEM,
)
from entity import Entity
from map import generate_grid
from hmm_detector import HMMDetector
from ai_agent import ai_decide


class GameState:
    def __init__(self):
        self.grid            = generate_grid()
        self.player          = Entity([0, 0], [0, 0])
        self.ai              = Entity([GRID_SIZE - 1, GRID_SIZE - 1],
                                      [GRID_SIZE - 1, GRID_SIZE - 1])
        self.turn            = 0
        self.phase           = "player_turn"   # player_turn | ai_thinking | gameover
        self.gameover_reason = ""
        self.ai_timer        = 0
        self.log             = []
        self.flash           = {}      # (r,c): frames remaining
        self.ai_path         = []
        self.respawn_flash   = 0       # red-screen flash frames

        # Bomb state
        self.player_bomb_hits = 0
        self.ai_bomb_hits     = 0
        self.ai_known_bombs   = set()   # bombs AI has triggered and memorised
        self.revealed_bombs   = set()   # bomb cells revealed after being stepped on
        self.ai_has_hmm       = False
        self.ai_hmm_turns     = 0
        self.ai_hmm_belief    = {}      # (r,c) → P(bomb) from AI's scans

        self.revealed_gems   = set()   # gem cells made visible after first collision
        self.sounds          = {}      # populated by main.py after pygame.mixer init
        self.ai_visited      = set()   # cells visited during random-walk exploration

        # Player HMM
        self.hmm              = HMMDetector(self.grid)
        self.player_has_hmm   = False
        self.hmm_turns_left   = 0
        self.hmm_scan_results = []     # [(r,c,pct)] displayed this turn

    # ── Sound ────────────────────────────────────────────────────────────────

    def _play(self, name):
        snd = self.sounds.get(name)
        if snd:
            snd.play()

    # ── Logging ──────────────────────────────────────────────────────────────

    def add_log(self, msg, ck="log_info"):
        self.log.insert(0, (msg, ck))
        self.log = self.log[:14]

    # ── Game-over helper ─────────────────────────────────────────────────────

    def _end_game(self, reason):
        self.phase           = "gameover"
        self.gameover_reason = reason
        self.add_log(reason, "log_bomb")

    # ── Cell landing (player) ────────────────────────────────────────────────

    def _apply_cell_player(self):
        r, c = self.player.pos
        ct   = self.grid[r][c]

        if ct == TREASURE:
            self._play("coin")
            self.revealed_gems.add((r, c))
            self.player.score += 10
            self.grid[r][c] = EMPTY
            self.hmm.mark_safe(r, c)
            self.add_log("Player: +10 💎 Treasure!", "log_treas")
            self.flash[(r, c)] = 14
            self._check_treasures()
            if self.phase == "gameover":
                return

        elif ct == WEAPON:
            self.player.score += 2
            self.player.weapon = True
            self.grid[r][c] = EMPTY
            self.hmm.mark_safe(r, c)
            self.add_log("Player: +2 ⚔  Weapon!", "log_weap")
            self.flash[(r, c)] = 14

        elif ct == HMM_ITEM:
            self.player.score   += 3
            self.player_has_hmm  = True
            self.hmm_turns_left  = HMM_TURNS_MAX
            self.grid[r][c] = EMPTY
            self.hmm.mark_safe(r, c)
            self.add_log(f"Player: HMM Detector active! ({HMM_TURNS_MAX} turns)", "log_hmm")
            self.flash[(r, c)] = 14
            self._hmm_scan()

        elif ct == BOMB:
            self._play("bomb")
            self.revealed_bombs.add((r, c))
            self.player_bomb_hits += 1
            self.hmm.mark_danger(r, c)
            if self.player_bomb_hits % 2 == 0:
                # Even hit → explosion
                self.player.score    -= TRAP_PENALTY * 2
                self.player.pos       = self.player.spawn[:]
                self.player.weapon    = False
                self.player_bomb_hits = 0
                self.respawn_flash    = 60
                self.add_log(f"💣 BOOM! -{TRAP_PENALTY * 2} pts → respawn", "log_bomb")
                if self.player.score < 0:
                    self._end_game("Score below 0 — GAME OVER!")
            else:
                # Odd hit → warning
                self.respawn_flash = 20
                self.add_log(f"⚠ Bomb! ({self.player_bomb_hits}/2) — next bomb = BOOM!", "log_bomb")
                self.flash[(r, c)] = 20
            return

        else:
            self.hmm.mark_safe(r, c)
            self.flash[(r, c)] = 10

        if self.player_has_hmm and self.hmm_turns_left > 0:
            self._hmm_scan()
            self.hmm_turns_left -= 1
            if self.hmm_turns_left <= 0:
                self.player_has_hmm   = False
                self.hmm_scan_results = []
                self.add_log("🔍 HMM Detector expired!", "log_hmm")

    # ── HMM scan (player) ────────────────────────────────────────────────────

    def _hmm_scan(self):
        self.hmm_scan_results = self.hmm.scan_adjacent(self.player.pos, self.grid)

    # ── HMM scan (AI) ────────────────────────────────────────────────────────

    def _ai_hmm_scan(self):
        r0, c0 = self.ai.pos
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r0 + dr, c0 + dc
                if not (0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE):
                    continue
                if self.grid[nr][nc] == WALL:
                    continue
                is_bomb = self.grid[nr][nc] == BOMB
                obs = random.random() < (0.85 if is_bomb else 0.15)
                p = self.ai_hmm_belief.get((nr, nc), 0.15)
                if obs:
                    p = (0.85 * p) / (0.85 * p + 0.15 * (1 - p) + 1e-9)
                else:
                    p = (0.15 * p) / (0.15 * p + 0.85 * (1 - p) + 1e-9)
                self.ai_hmm_belief[(nr, nc)] = max(0.0, min(1.0, p))
                if p >= 0.7:
                    self.ai_known_bombs.add((nr, nc))
                elif p < 0.3:
                    self.ai_known_bombs.discard((nr, nc))

    # ── Check all treasures collected ────────────────────────────────────────

    def _check_ai_score(self):
        if self.ai.score < 0:
            ps = self.player.score
            self._end_game(f"AI score below 0 — Player wins! ({ps} vs {self.ai.score})")

    def _check_treasures(self):
        remaining = sum(1 for row in self.grid for c in row if c == TREASURE)
        if remaining == 0:
            ps, ais = self.player.score, self.ai.score
            if   ps > ais:  reason = f"All gems found! Player wins! ({ps} vs {ais})"
            elif ais > ps:  reason = f"All gems found! AI wins! ({ais} vs {ps})"
            else:            reason = f"All gems found! Draw! (both {ps} pts)"
            self._end_game(reason)

    # ── Cell landing (AI) ────────────────────────────────────────────────────

    def _apply_cell_ai(self):
        r, c = self.ai.pos
        ct   = self.grid[r][c]

        if ct == TREASURE:
            self._play("coin")
            self.revealed_gems.add((r, c))
            self.ai.score += 10; self.grid[r][c] = EMPTY
            self.add_log("AI: +10 💎 Treasure!", "log_treas")
            self.flash[(r, c)] = 14
            self._check_treasures()
        elif ct == WEAPON:
            self.ai.score += 2; self.ai.weapon = True; self.grid[r][c] = EMPTY
            self.add_log("AI: +2 ⚔  Weapon!", "log_weap")
            self.flash[(r, c)] = 14
        elif ct == HMM_ITEM:
            self.ai.score   += 3
            self.ai_has_hmm  = True
            self.ai_hmm_turns = HMM_TURNS_MAX
            self.grid[r][c] = EMPTY
            self.add_log(f"AI: +3 🔍 HMM active! ({HMM_TURNS_MAX} turns)", "log_hmm")
            self.flash[(r, c)] = 14
            self._ai_hmm_scan()
        elif ct == BOMB:
            self._play("bomb")
            self.revealed_bombs.add((r, c))
            self.ai_bomb_hits += 1
            if self.ai_bomb_hits % 2 == 0:
                self.ai.score    -= TRAP_PENALTY * 2
                self.ai.pos       = self.ai.spawn[:]
                self.ai.weapon    = False
                self.ai_bomb_hits = 0
                self.ai_known_bombs.add((r, c))
                self.add_log(f"AI: 💣 BOOM! -{TRAP_PENALTY * 2} → respawn (memorised)", "log_bomb")
                self.flash[(r, c)] = 20
                self._check_ai_score()
            else:
                self.add_log("AI: ⚠ Bomb step 1/2! Learning...", "log_bomb")
                self.flash[(r, c)] = 20
        else:
            self.flash[(r, c)] = 10

    # ── Attack ───────────────────────────────────────────────────────────────

    def _try_attack(self, attacker, target, aname, dname):
        if not attacker.weapon:
            return
        dist = abs(attacker.pos[0] - target.pos[0]) + abs(attacker.pos[1] - target.pos[1])
        if dist > 1:
            return

        self._play("sword")
        # Both armed → 50/50 duel; loser takes damage
        if target.weapon:
            if random.random() < 0.5:
                winner, loser, wname, lname = attacker, target, aname, dname
            else:
                winner, loser, wname, lname = target, attacker, dname, aname
            self.add_log(f"⚔ DUEL! {wname} wins vs {lname}! -8, respawn", "log_atk")
            loser.score   -= 8
            loser.pos      = loser.spawn[:]
            loser.weapon   = False
            winner.weapon  = False
            if loser is self.player and loser.score < 0:
                self._end_game("Score below 0 — GAME OVER!")
            elif loser is self.ai:
                self._check_ai_score()
        else:
            self.add_log(f"{aname} ⚔ attacks {dname}! -8, respawn", "log_atk")
            target.score    -= 8
            target.pos       = target.spawn[:]
            target.weapon    = False
            attacker.weapon  = False
            if target is self.player and target.score < 0:
                self._end_game("Score below 0 — GAME OVER!")
            elif target is self.ai:
                self._check_ai_score()

    # ── Player move ──────────────────────────────────────────────────────────

    def player_move(self, dr, dc):
        if self.phase != "player_turn":
            return False
        nr, nc = self.player.pos[0] + dr, self.player.pos[1] + dc
        if not (0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE):
            return False
        if self.grid[nr][nc] == WALL:
            return False

        self.player.pos = [nr, nc]
        self._apply_cell_player()

        if self.phase == "gameover":
            return True

        self._try_attack(self.player, self.ai, "Player", "AI")

        if self.phase == "gameover":
            return True

        if self.player.score < 0:
            self._end_game("Score below 0 — GAME OVER!")
            return True

        self.turn += 1
        if self.turn >= MAX_TURNS:
            self.phase           = "gameover"
            self.gameover_reason = "Time up!"
            return True

        self.phase    = "ai_thinking"
        self.ai_timer = AI_DELAY_MS
        return True

    # ── AI move ──────────────────────────────────────────────────────────────

    def ai_move(self):
        # Mask unrevealed gems so AI has no knowledge of them
        masked = [row[:] for row in self.grid]
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if masked[r][c] == TREASURE and (r, c) not in self.revealed_gems:
                    masked[r][c] = EMPTY

        self.ai_visited.add(tuple(self.ai.pos))

        next_pos, path = ai_decide(
            masked,
            self.player.pos, self.player.score, self.player.weapon,
            self.ai.pos,     self.ai.score,     self.ai.weapon,
            self.ai_known_bombs | self.revealed_bombs,
            self.ai_visited,
        )
        self.ai_path = path
        if next_pos:
            nr, nc = next_pos
            if self.grid[nr][nc] != WALL:
                self.ai.pos = [nr, nc]
                self._apply_cell_ai()
                self._try_attack(self.ai, self.player, "AI", "Player")

        if self.ai_has_hmm and self.ai_hmm_turns > 0:
            self._ai_hmm_scan()
            self.ai_hmm_turns -= 1
            if self.ai_hmm_turns <= 0:
                self.ai_has_hmm = False
                self.add_log("AI: HMM expired", "log_hmm")

        if self.phase != "gameover":
            self.phase = "player_turn"

    # ── Per-frame update ─────────────────────────────────────────────────────

    def update(self, dt_ms):
        if self.phase == "ai_thinking":
            self.ai_timer -= dt_ms
            if self.ai_timer <= 0:
                self.ai_move()
        for k in list(self.flash):
            self.flash[k] -= 1
            if self.flash[k] <= 0:
                del self.flash[k]
        if self.respawn_flash > 0:
            self.respawn_flash -= 1
