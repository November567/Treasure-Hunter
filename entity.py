"""
Entity model for Treasure Hunter (player and AI bot).
"""


class Entity:
    def __init__(self, pos, spawn):
        self.pos    = list(pos)
        self.spawn  = list(spawn)
        self.score  = 0
        self.weapon = False
