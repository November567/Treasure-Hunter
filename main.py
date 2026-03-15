"""
Treasure Hunter: Player vs AI
==============================
AI Strategy : Minimax (target selection) + A* (pathfinding)
Features:
  - BOMB (💣)   : hidden, must step on TWICE to explode
  - HMM DETECTOR: scan adjacent cells with probability estimates (HMM)
  - Score < 0   = GAME OVER instantly
  - Player locked while AI is thinking

Requirements: pip install pygame
Controls : Arrow / WASD  move  |  R restart  |  ESC quit
"""

import os
import random
import sys

import pygame

from constants import SCREEN_W, SCREEN_H, FPS, C
from game import GameState
from renderer import load_fonts, draw_grid, draw_panel, draw_gameover


def load_sounds():
    sounds = {}
    pygame.mixer.init()
    snd_dir = os.path.join(os.path.dirname(__file__), "sound")
    files = {
        "bomb":  "freesound_community-moderate-bomb-explosion-41803.mp3",
        "coin":  "ribhavagrawal-coin-recieved-230517.mp3",
        "sword": "u_fe12rqkbth-sword-clash-241729.mp3",
    }
    volumes = {"bomb": 0.3, "coin": 0.5, "sword": 0.5}
    for name, filename in files.items():
        try:
            snd = pygame.mixer.Sound(os.path.join(snd_dir, filename))
            snd.set_volume(volumes[name])
            sounds[name] = snd
        except Exception as e:
            print(f"[sound] Could not load {name} sound: {e}")
    return sounds


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Treasure Hunter — HMM + Bombs + Minimax/A*")
    clock  = pygame.time.Clock()

    fonts  = load_fonts()
    sounds = load_sounds()
    state  = GameState()
    state.sounds = sounds

    stars = [(random.randint(0, SCREEN_W), random.randint(0, SCREEN_H),
              random.random()) for _ in range(80)]

    hmm_display = {}   # (r,c) → pct; persists between frames

    running = True
    while running:
        dt_ms = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                if event.key == pygame.K_r:
                    state = GameState()
                    state.sounds = sounds
                    hmm_display.clear()
                if state.phase == "player_turn":
                    km = {
                        pygame.K_UP:    (-1,  0), pygame.K_w: (-1,  0),
                        pygame.K_DOWN:  ( 1,  0), pygame.K_s: ( 1,  0),
                        pygame.K_LEFT:  ( 0, -1), pygame.K_a: ( 0, -1),
                        pygame.K_RIGHT: ( 0,  1), pygame.K_d: ( 0,  1),
                    }
                    if event.key in km:
                        state.player_move(*km[event.key])

        state.update(dt_ms)

        screen.fill(C["bg"])
        for x, y, b in stars:
            v = int(40 + b * 120)
            pygame.draw.circle(screen, (v, v, v + 20), (x, y), 1)

        draw_grid(screen, state, fonts, hmm_display)
        draw_panel(screen, state, fonts)
        if state.phase == "gameover":
            draw_gameover(screen, state, fonts)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
