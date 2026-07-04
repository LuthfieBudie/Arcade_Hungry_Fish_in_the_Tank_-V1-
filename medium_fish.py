# medium_fish.py
import arcade
import random
import math
from outside import SURFACE_MARGIN_FROM_TOP

class mediumfish:
    def __init__(self, width, height, x, y):
        self.screen_width = width
        self.screen_height = height
        self.water_max_y = height - SURFACE_MARGIN_FROM_TOP - 50
        self.x = x
        self.y = y
        self.speed = random.uniform(1.0, 1.6)

        self.target_x = random.randint(50, self.screen_width - 50)
        self.target_y = random.randint(50, max(100, int(self.water_max_y)))
        self.wander_timer = random.uniform(80, 180)

        self.flee_radius = 220  # Lari dari huge fish dan HUGE player

    def draw(self):
        body = arcade.rect.XYWH(self.x, self.y, 90, 45)
        arcade.draw_rect_filled(body, arcade.color.ORANGE)

    def update(self, player=None, huge_list=None):
        threat_x, threat_y = None, None
        closest_dist = self.flee_radius

        # Medium fish takut pada huge fish dan player yg sudah HUGE
        threats = []
        if huge_list:
            for h in huge_list:
                threats.append((h.x, h.y))
        if player and player.status == "HUGE":
            threats.append((player.x, player.y))

        for tx, ty in threats:
            d = math.sqrt((self.x - tx)**2 + (self.y - ty)**2)
            if d < closest_dist:
                closest_dist = d
                threat_x, threat_y = tx, ty

        if threat_x is not None:
            # Lari
            flee_dx = self.x - threat_x
            flee_dy = self.y - threat_y
            dist = math.sqrt(flee_dx**2 + flee_dy**2)
            if dist > 0:
                flee_speed = self.speed * 2.0
                self.x += (flee_dx / dist) * flee_speed
                self.y += (flee_dy / dist) * flee_speed
        else:
            # Wander dengan perubahan arah berkala
            self.wander_timer -= 1
            if self.wander_timer <= 0:
                self.target_x = random.randint(50, self.screen_width - 50)
                self.target_y = random.randint(50, max(100, int(self.water_max_y)))
                self.wander_timer = random.uniform(100, 220)

            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist < 10:
                self.target_x = random.randint(50, self.screen_width - 50)
                self.target_y = random.randint(50, max(100, int(self.water_max_y)))
            else:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed

        self.x = max(25, min(self.x, self.screen_width - 25))
        self.y = max(25, min(self.y, self.water_max_y))

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
                    fishes.append(mediumfish(width, height, kandidat_x, kandidat_y))
                    valid_position = True
                attempts += 1
        return fishes