# bugs.py
import arcade
import math
import random

TOTAL_BUGS   = 7
BUG_W        = 14
BUG_H        = 10
BUG_COLOR    = (60, 40, 10)

BUG_SPEED_MIN = 0.8
BUG_SPEED_MAX = 2.0

# Bugs terbang di zona rendah dekat permukaan air agar mudah dimakan
BUG_MIN_ABOVE_SURFACE = 20    # minimal 20px di atas surface
BUG_MAX_ABOVE_SURFACE = 220   # maksimal 220px di atas surface — zona terjangkau player

EAT_RADIUS   = 35
WANDER_MIN   = 60
WANDER_MAX   = 180
MIN_SPAWN_DIST = 80


class Bug:
    def __init__(self, x, y, map_width, surface_y, map_height):
        self.x          = x
        self.y          = y
        self.map_width  = map_width
        self.surface_y  = surface_y
        self.map_height = map_height

        # Zona terbang bug: surface_y s/d surface_y + BUG_MAX_ABOVE_SURFACE
        self._min_y = surface_y + BUG_MIN_ABOVE_SURFACE
        self._max_y = surface_y + BUG_MAX_ABOVE_SURFACE

        self.speed        = random.uniform(BUG_SPEED_MIN, BUG_SPEED_MAX)
        self.target_x     = x
        self.target_y     = y
        self.wander_timer = random.randint(WANDER_MIN, WANDER_MAX)
        self._pick_target()
        self.eaten = False

    def _pick_target(self):
        margin = 60
        self.target_x = random.uniform(margin, self.map_width - margin)
        # Target hanya di zona rendah — dekat permukaan air
        self.target_y = random.uniform(self._min_y + BUG_H, self._max_y)

    def update(self):
        if self.eaten:
            return

        self.wander_timer -= 1
        if self.wander_timer <= 0:
            self._pick_target()
            self.wander_timer = random.randint(WANDER_MIN, WANDER_MAX)

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist < 10:
            self._pick_target()
        else:
            zigzag = math.sin(self.wander_timer * 0.3) * 0.8
            self.x += (dx / dist) * self.speed + zigzag
            self.y += (dy / dist) * self.speed

        # Klem ke zona terbang
        self.y = max(self._min_y, min(self.y, self._max_y))
        self.x = max(BUG_W, min(self.x, self.map_width - BUG_W))

    def draw(self):
        if self.eaten:
            return
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.x, self.y, BUG_W, BUG_H),
            BUG_COLOR
        )


class BugManager:
    def __init__(self, map_width, map_height, surface_y):
        self.map_width  = map_width
        self.map_height = map_height
        self.surface_y  = surface_y
        self._min_y     = surface_y + BUG_MIN_ABOVE_SURFACE
        self._max_y     = surface_y + BUG_MAX_ABOVE_SURFACE

        self.bugs           = []
        self._pending_score  = 0
        self._pending_points = 0   # untuk POINTS HUD permanen (bug = 1 poin)
        self._replenish()

    def _spawn_one(self):
        margin = 80
        for _ in range(50):
            x = random.uniform(margin, self.map_width - margin)
            y = random.uniform(self._min_y + BUG_H * 2, self._max_y)
            too_close = any(
                math.sqrt((x - b.x)**2 + (y - b.y)**2) < MIN_SPAWN_DIST
                for b in self.bugs if not b.eaten
            )
            if not too_close:
                return Bug(x, y, self.map_width, self.surface_y, self.map_height)
        x = random.uniform(margin, self.map_width - margin)
        y = random.uniform(self._min_y + BUG_H * 2, self._max_y)
        return Bug(x, y, self.map_width, self.surface_y, self.map_height)

    def _replenish(self):
        alive = [b for b in self.bugs if not b.eaten]
        for _ in range(TOTAL_BUGS - len(alive)):
            alive.append(self._spawn_one())
        self.bugs = alive

    def update(self, player, player_in_air: bool, eat_animations=None):
        for bug in self.bugs:
            bug.update()

        if player_in_air and not getattr(player, 'is_spawning', False):
            px, py = player.x, player.y
            pw, ph = player.width / 2, player.height / 2
            for bug in self.bugs:
                if bug.eaten:
                    continue
                if (abs(px - bug.x) < pw + EAT_RADIUS and
                        abs(py - bug.y) < ph + EAT_RADIUS):
                    bug.eaten = True
                    self._pending_score += random.randint(1, 3)
                    self._pending_points += 1   # POINTS HUD: bug = 1 poin tetap

                    # ── Animasi makan bug (sama seperti ikan) ──
                    if eat_animations is not None:
                        from eat_fish import EatAnimation
                        eat_animations.append(EatAnimation(bug, player))

                    # ── SFX makan ──
                    import os
                    _eat_sfx = ["eat1.mp3","eat2.mp3","eat3.mp3","eat4.mp3","eat5.mp3"]
                    try:
                        _sfx_path = os.path.join("assets", "sfx", "eat_sfx",
                                                  random.choice(_eat_sfx))
                        arcade.play_sound(arcade.load_sound(_sfx_path), volume=0.6)
                    except Exception:
                        pass

        self.bugs = [b for b in self.bugs if not b.eaten]
        self._replenish()

    def consume_score(self):
        s = self._pending_score
        self._pending_score = 0
        return s

    def consume_points(self):
        p = self._pending_points
        self._pending_points = 0
        return p

    def draw(self):
        for bug in self.bugs:
            bug.draw()