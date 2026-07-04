# seaweed.py
import arcade
import math
import random

class PanikFish:
    def __init__(self, x, y, screen_width, screen_height):
        self.x = x
        self.y = y
        self.width = 25
        self.height = 15
        self.is_panik = True

        # Delay sebelum bisa dimakan: 60 frame = 1 detik
        self.kebal_timer = 60

        self.screen_width = screen_width
        self.screen_height = screen_height

        # Target awal: berpencar menjauhi titik spawn (seaweed)
        # Arah acak ke segala penjuru agar terasa berpencar
        angle = random.uniform(0, 2 * math.pi)
        scatter_dist = random.uniform(80, 200)
        self.target_x = max(50, min(x + math.cos(angle) * scatter_dist, screen_width - 50))
        self.target_y = max(50, min(y + math.sin(angle) * scatter_dist, screen_height - 50))

        # Kecepatan lebih cepat saat panik
        self.speed = random.uniform(2.5, 4.0)

        # Setelah 1 detik, ganti ke mode wander biasa
        self.scatter_done = False

    def draw(self):
        fish_rect = arcade.rect.XYWH(self.x, self.y, self.width, self.height)
        arcade.draw_rect_filled(fish_rect, arcade.color.YELLOW)

    def update(self):
        if self.kebal_timer > 0:
            self.kebal_timer -= 1

        # Fase 1: Berpencar (selama 1 detik / 60 frame pertama)
        # Fase 2: Wander biasa setelah selesai berpencar
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        jarak = math.sqrt(dx**2 + dy**2)

        if jarak > 5:
            self.x += (dx / jarak) * self.speed
            self.y += (dy / jarak) * self.speed
        else:
            # Selesai berpencar → mulai wander biasa
            self.scatter_done = True
            self.speed = random.uniform(1.2, 2.0)  # Lebih pelan saat wander
            self.target_x = random.randint(50, self.screen_width - 50)
            self.target_y = random.randint(50, self.screen_height - 50)

        self.x = max(15, min(self.x, self.screen_width - 15))
        self.y = max(15, min(self.y, self.screen_height - 15))


class seaweed:
    def __init__(self, x, y, width=20, height=80, color=arcade.color.AMAZON):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.cooldown_timer = 0

    def draw(self):
        kotak_placeholder = arcade.rect.XYWH(self.x, self.y, self.width, self.height)
        arcade.draw_rect_filled(kotak_placeholder, self.color)

    def check_dash_collision(self, player, enemy_list, screen_width, screen_height):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1
            return False

        if player.is_dashing:
            jarak_ke_player = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
            batas_jarak = (player.width / 2) + (self.width / 2) + 10

            if jarak_ke_player < batas_jarak:
                self.cooldown_timer = 180

                for _ in range(5):
                    # Spawn tepat di seaweed dengan sedikit variasi posisi
                    spawn_x = self.x + random.randint(-15, 15)
                    spawn_y = self.y + random.randint(-10, 20)
                    panik_fish = PanikFish(spawn_x, spawn_y, screen_width, screen_height)
                    enemy_list.append(panik_fish)

                return True
        return False