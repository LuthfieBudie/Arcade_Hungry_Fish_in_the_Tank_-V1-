import math
import arcade
import os
import random
 
class EatAnimation:
    """Representasi ikan yang sedang dianimasikan masuk ke mulut player."""
    def __init__(self, fish, player):
        self.x = fish.x
        self.y = fish.y
        self.color = _get_fish_color(fish)


        self.w = _get_fish_w(fish)
        self.h = _get_fish_h(fish)
        self.player = player


        self.progress = 0.0


        self.speed = 0.08
        self.done = False


        self.start_x = fish.x
        self.start_y = fish.y
        self.start_w = self.w
        self.start_h = self.h

    def update(self):
        self.progress += self.speed
        if self.progress >= 1.0:
            self.progress = 1.0
            self.done = True

        t = self.progress
        self.x = self.start_x + (self.player.x - self.start_x) * t
        self.y = self.start_y + (self.player.y - self.start_y) * t
        self.w = self.start_w * (1 - t)
        self.h = self.start_h * (1 - t)



    def draw(self):
        if self.w > 1 and self.h > 1:
            import arcade
            rect = arcade.rect.XYWH(self.x, self.y, self.w, self.h)
            arcade.draw_rect_filled(rect, self.color)


def _get_fish_color(fish):
    import arcade
    name = fish.__class__.__name__
    if name == "hugefish":
        return arcade.color.RED
    elif name == "mediumfish":
        return arcade.color.ORANGE
    elif name == "speedmediumfish":
        return (210, 30, 140)   # magenta — versi cepat mediumfish
    elif name == "jumpingsmallfish":
        return (0, 200, 180)    # cyan — versi lompat smallfish
    elif name == "Bug":
        return (60, 40, 10)   # coklat gelap — warna bug
    else:
        return arcade.color.YELLOW

def _get_fish_w(fish):
    name = fish.__class__.__name__
    if name == "hugefish": return 150
    elif name in ("mediumfish", "speedmediumfish"): return 90
    elif name == "Bug": return 14
    else: return 50

def _get_fish_h(fish):
    name = fish.__class__.__name__
    if name == "hugefish": return 75
    elif name in ("mediumfish", "speedmediumfish"): return 45
    elif name == "Bug": return 10
    else: return 25


class PlayerEatenAnimation:
    """Animasi saat main_fish (player) DIMAKAN oleh ikan lain.

    Kebalikan dari EatAnimation: yang mengecil dan bergerak adalah player,
    menuju posisi predator (ikan yang memakannya) — dibuat sedikit lebih
    lambat dari animasi makan biasa supaya terlihat jelas oleh pemain.
    """
    def __init__(self, player, predator_x, predator_y):
        self.start_x = player.x
        self.start_y = player.y
        self.target_x = predator_x
        self.target_y = predator_y

        self.x = player.x
        self.y = player.y
        self.start_w = player.width
        self.start_h = player.height
        self.w = self.start_w
        self.h = self.start_h

        # Warna sama seperti player (lihat mainfish.draw)
        self.color = arcade.color.PURPLE

        self.progress = 0.0
        self.speed = 0.05
        self.done = False

    def update(self):
        self.progress += self.speed
        if self.progress >= 1.0:
            self.progress = 1.0
            self.done = True

        t = self.progress
        self.x = self.start_x + (self.target_x - self.start_x) * t
        self.y = self.start_y + (self.target_y - self.start_y) * t
        self.w = self.start_w * (1 - t)
        self.h = self.start_h * (1 - t)

    def draw(self):
        if self.w > 1 and self.h > 1:
            rect = arcade.rect.XYWH(self.x, self.y, self.w, self.h)
            arcade.draw_rect_filled(rect, self.color)





def check_collision_and_respawn(player, enemy_list, width, height, window, eat_animations, jarak_minimum=80, chomp_active=False):
    to_remove = []


    if player.is_spawning or player.kebal_timer > 0:
        return

    for fish in enemy_list:


        if hasattr(fish, 'kebal_timer') and fish.kebal_timer > 0:
            continue

        nama_kelas = fish.__class__.__name__

        if nama_kelas == "hugefish":
            ukuran_musuh = 70
        elif nama_kelas in ("mediumfish", "speedmediumfish"):
            ukuran_musuh = 45
        else:
            ukuran_musuh = 25


        player_left   = player.x - (player.width / 2)
        player_right  = player.x + (player.width / 2)
        player_top    = player.y + (player.height / 2)
        player_bottom = player.y - (player.height / 2)

        fish_left   = fish.x - (ukuran_musuh / 2)
        fish_right  = fish.x + (ukuran_musuh / 2)
        fish_top    = fish.y + (ukuran_musuh / 2)
        fish_bottom = fish.y - (ukuran_musuh / 2)

        is_colliding = (
            player_right  >= fish_left  and
            player_left   <= fish_right and
            player_top    >= fish_bottom and
            player_bottom <= fish_top
        )

        if not is_colliding:
            continue








        if nama_kelas == "hugefish":
            if player.status != "HUGE" and not chomp_active:
                # Player dimakan → animasi respawn dari atas
                player.score = max(0, player.score - 9999)
                spawn_x = width // 2
                spawn_y = height // 2
                player.trigger_respawn(spawn_x, spawn_y, height, eaten_by=(fish.x, fish.y))
                window.set_mouse_position(400, 280)
                return
            else:
                random_point = random.randint(10, 15)
                fixed_points = 10   # POINTS HUD: huge fish = 10






        elif nama_kelas in ("mediumfish", "speedmediumfish"):
            if player.status == "SMALL" and not chomp_active:
                player.score = max(0, player.score - 9999)
                spawn_x = width // 2
                spawn_y = height // 2
                player.trigger_respawn(spawn_x, spawn_y, height, eaten_by=(fish.x, fish.y))
                window.set_mouse_position(400, 280)
                return
            else:
                random_point = random.randint(5, 7)
                fixed_points = 5    # POINTS HUD: medium fish = 5




        else:
            random_point = random.randint(1, 3)
            fixed_points = 1        # POINTS HUD: small fish = 1


        # Tambah skor & cek evolusi
        player.score += random_point
        # POINTS HUD — akumulasi permanen, tidak pernah direset walau dimakan
        player.total_points = getattr(player, 'total_points', 0) + fixed_points
        player.check_evolution()






        anim = EatAnimation(fish, player)
        eat_animations.append(anim)
        eat_sfx = ["eat1.mp3", "eat2.mp3", "eat3.mp3", "eat4.mp3", "eat5.mp3"]
        sfx_choice = random.choice(eat_sfx)
        try:
            _base = os.path.dirname(os.path.abspath(__file__))
            sfx_path = os.path.join(_base, "assets", "sfx", "eat_sfx", sfx_choice)
            random_eat_sfx = arcade.load_sound(sfx_path)
            try:
                from setting import load_settings as _ls
                _svol = _ls().get("sfx_volume", 0.6)
            except Exception:
                _svol = 0.6
            arcade.play_sound(random_eat_sfx, volume=_svol)
        except Exception as e:
            print(f"Gagal memutar SFX makan: {e}")






        if hasattr(fish, 'is_panik'):
            to_remove.append(fish)
            continue





        valid_position = False
        attempts = 0
        while not valid_position and attempts < 100:
            kandidat_x = random.randint(50, width - 50)
            kandidat_y = random.randint(50, height - 50)
            too_close = False
            for other in enemy_list:
                if other is fish:
                    continue
                d = math.sqrt((kandidat_x - other.x)**2 + (kandidat_y - other.y)**2)
                if d < jarak_minimum:
                    too_close = True
                    break
            if not too_close:
                fish.x = kandidat_x
                fish.y = kandidat_y
                fish.target_x = random.randint(50, width - 50)
                fish.target_y = random.randint(50, height - 50)
                valid_position = True
            attempts += 1




    for fish in to_remove:
        if fish in enemy_list:
            enemy_list.remove(fish)