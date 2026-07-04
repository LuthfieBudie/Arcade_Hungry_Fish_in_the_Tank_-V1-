# huge_fish.py
import arcade
import random
import math
from outside import SURFACE_MARGIN_FROM_TOP

class hugefish:
    def __init__(self, width, height, x, y):
        self.screen_width = width
        self.screen_height = height
        self.water_max_y = height - SURFACE_MARGIN_FROM_TOP - 50
        self.x = x
        self.y = y
        self.speed = random.uniform(0.7, 1.1)

        self.target_x = random.randint(50, self.screen_width - 50)
        self.target_y = random.randint(50, max(100, int(self.water_max_y)))
        self.wander_timer = random.uniform(120, 250)

        # Huge fish mengejar player jika dekat
        self.chase_radius = 350
        self.is_chasing = False

    def draw(self):
        body = arcade.rect.XYWH(self.x, self.y, 150, 75)
        arcade.draw_rect_filled(body, arcade.color.RED)

    def update(self, player=None):
        if player and player.status != "HUGE":
            d = math.sqrt((self.x - player.x)**2 + (self.y - player.y)**2)
            if d < self.chase_radius:
                # Kejar player!
                self.is_chasing = True
                dx = player.x - self.x
                dy = player.y - self.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    chase_speed = self.speed * 1.5
                    self.x += (dx / dist) * chase_speed
                    self.y += (dy / dist) * chase_speed
            else:
                self.is_chasing = False
                self._wander()
        else:
            self.is_chasing = False
            self._wander()

        self.x = max(50, min(self.x, self.screen_width - 50))
        self.y = max(50, min(self.y, self.water_max_y))

    def _wander(self):
        self.wander_timer -= 1
        if self.wander_timer <= 0:
            self.target_x = random.randint(50, self.screen_width - 50)
            self.target_y = random.randint(50, max(100, int(self.water_max_y)))
            self.wander_timer = random.uniform(150, 300)

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist < 10:
            self.target_x = random.randint(50, self.screen_width - 50)
            self.target_y = random.randint(50, max(100, int(self.water_max_y)))
        else:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

    def generate_fish(quantity, width, height, min_distance):
        fishes = []
        for _ in range(quantity):
            valid_position = False
            attempts = 0
            while not valid_position and attempts < 100:
                kandidat_x = random.randint(25, width - 25)
                kandidat_y = random.randint(25, height - 25)
                too_close = any(
                    math.sqrt((kandidat_x - f.x)**2 + (kandidat_y - f.y)**2) < min_distance
                    for f in fishes
                )
                if not too_close:
                    fishes.append(hugefish(width, height, kandidat_x, kandidat_y))
                    valid_position = True
                attempts += 1
        return fishes