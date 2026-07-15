# power_up.py
#
# Fitur "Power-Up Box": kotak persegi sempurna (ukuran mirip medium fish)
# yang muncul dengan siklus hidup:
#
#   1) FALLING   -> jatuh dari atas map (seperti respawn player), mendarat
#                   dengan efek memantul (ease-out-bounce) tepat di garis
#                   batas air/udara (surface_y).
#   2) FLOATING  -> mengapung/naik-turun pelan (bobbing) di perbatasan
#                   air-udara selama ± 2 detik.
#   3) SINKING   -> setelah itu turun pelan-pelan masuk ke dalam air menuju
#                   kedalaman acak.
#   4) DESPAWNING-> pada waktu acak SELAMA proses turun (beberapa detik),
#                   kotak bisa mulai despawn: opacity berkedip hidup-mati,
#                   lalu hilang.
#
# Setelah hilang (baik karena despawn maupun dimakan), power-up akan
# respawn lagi di posisi acak setelah ± 20 detik.
#
# EFEK SAAT DIMAKAN:
#   - main_fish (player)                -> +15 poin (score & total_points)
#   - smallfish / jumpingsmallfish      -> berevolusi jadi mediumfish
#   - mediumfish / speedmediumfish      -> berevolusi jadi hugefish
#   - hugefish                          -> berevolusi jadi dangerousfish
#
# CARA PAKAI DI game.py (contoh):
#
#   from power_up import PowerUpManager
#   self.power_up_manager = PowerUpManager(self.MAP_WIDTH, self.MAP_HEIGHT,
#                                           self.water_boundary.surface_y)
#
#   # di on_update():
#   self.power_up_manager.update()
#   self.power_up_manager.check_and_handle_collisions(
#       self.player_fish, self.enemy_list,
#       dangerous_manager=self.dangerous_manager,
#       eat_animations=self.eat_animations,
#   )
#
#   # di on_draw() (sebelum gui_camera.use(), masih pakai world camera):
#   self.power_up_manager.draw()

import math
import random

import arcade

from small_fish import smallfish
from medium_fish import mediumfish
from huge_fish import hugefish
from dangerous_fish import dangerousfish


# ─── Konstanta ────────────────────────────────────────────────────────────────

BOX_SIZE = 70   # kotak persegi sempurna, kira-kira sebesar medium fish

# Warna power-up (emas terang supaya beda dari ikan lain)
BOX_COLOR    = (139, 69, 19)

SPAWN_ABOVE_MAP = 220     # tinggi jatuh di atas map, mirip respawn.py
FALL_SPEED      = 0.024   # kecepatan animasi jatuh (± 0.7 detik)

FLOAT_DURATION = 120      # ± 2 detik @ 60fps mengapung di batas air/udara
FLOAT_BOB_AMPLITUDE = 6   # naik-turun halus saat mengapung
FLOAT_BOB_SPEED = 0.06

SINK_SPEED = 0.35         # kecepatan turun pelan ke dalam air
SINK_MIN_DEPTH = 120      # minimal kedalaman dari surface_y
SINK_MAX_DEPTH = 420      # maksimal kedalaman dari surface_y

# Despawn terjadi acak SELAMA fase sinking (dalam frame @ 60fps)
DESPAWN_DELAY_MIN = 10 * 60    # paling cepat 2 detik setelah mulai turun
DESPAWN_DELAY_MAX = 25 * 60    # paling lambat 9 detik setelah mulai turun
DESPAWN_BLINK_DURATION = 80   # ± 1.3 detik proses berkedip sebelum benar hilang
DESPAWN_BLINK_INTERVAL = 5    # kedip tiap 5 frame (opacity hidup-mati)

# Respawn ± 20 detik setelah hilang (dimakan / despawn)
RESPAWN_MIN = 18 * 60
RESPAWN_MAX = 22 * 60

SPAWN_MARGIN_X = 120          # margin kiri-kanan saat memilih posisi jatuh acak

# Poin untuk main_fish
PLAYER_POINT_REWARD = 15


# ─── Kotak Power-Up ───────────────────────────────────────────────────────────

def _ease_out_bounce(t: float) -> float:
    """Efek memantul saat mendarat (sama gayanya dengan respawn.py)."""
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1: 
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


class PowerUpBox:
    """Satu instance kotak power-up dengan siklus hidup:
    falling -> floating -> sinking -> (opsional) despawning -> gone.
    """

    def __init__(self, map_width, map_height, surface_y):
        self.map_width  = map_width
        self.map_height = map_height
        self.surface_y  = surface_y

        self.size = BOX_SIZE

        # Posisi X acak, Y mulai jauh di atas map (jatuh dari langit)
        self.x = random.uniform(SPAWN_MARGIN_X, map_width - SPAWN_MARGIN_X)
        self.start_y = map_height + SPAWN_ABOVE_MAP
        self.float_y = surface_y   # titik "mengapung" tepat di batas air/udara
        self.y = self.start_y

        self.state = "falling"
        self.fall_progress = 0.0

        self.float_timer = FLOAT_DURATION
        self._bob_time = random.uniform(0, 100)  # fase bobbing acak biar variatif

        self.sink_target_y = None
        self.despawn_timer = None
        self.despawning = False
        self.blink_visible = True
        self.blink_timer = 0
        self._despawn_blink_left = DESPAWN_BLINK_DURATION

        self.alive  = True   # False kalau sudah waktunya dihapus manager
        self.eaten  = False  # True kalau habis dimakan (bukan despawn alami)

    # ──────────────────────────────────────────────────────────────────────
    def update(self):
        if not self.alive:
            return

        if self.state == "falling":
            self._update_falling()
        elif self.state == "floating":
            self._update_floating()
        elif self.state == "sinking":
            self._update_sinking()

    def _update_falling(self):
        self.fall_progress += FALL_SPEED
        if self.fall_progress >= 1.0:
            self.fall_progress = 1.0

        ease = _ease_out_bounce(self.fall_progress)
        self.y = self.start_y + (self.float_y - self.start_y) * ease

        if self.fall_progress >= 1.0:
            self.y = self.float_y
            self.state = "floating"
            self.float_timer = FLOAT_DURATION

    def _update_floating(self):
        self._bob_time += FLOAT_BOB_SPEED
        self.y = self.float_y + math.sin(self._bob_time) * FLOAT_BOB_AMPLITUDE

        self.float_timer -= 1
        if self.float_timer <= 0:
            # Mulai turun pelan-pelan ke kedalaman acak
            depth = random.uniform(SINK_MIN_DEPTH, SINK_MAX_DEPTH)
            self.sink_target_y = max(60, self.surface_y - depth)
            self.state = "sinking"
            # Tentukan kapan (secara acak) despawn mulai terjadi selama turun
            self.despawn_timer = random.randint(DESPAWN_DELAY_MIN, DESPAWN_DELAY_MAX)

    def _update_sinking(self):
        # Turun pelan-pelan menuju target kedalaman
        if self.y > self.sink_target_y:
            self.y -= SINK_SPEED
            if self.y < self.sink_target_y:
                self.y = self.sink_target_y

        if not self.despawning:
            self.despawn_timer -= 1
            if self.despawn_timer <= 0:
                self.despawning = True
                self._despawn_blink_left = DESPAWN_BLINK_DURATION
        else:
            # Opacity hidup-mati (blink) sebelum benar-benar hilang
            self.blink_timer += 1
            if self.blink_timer >= DESPAWN_BLINK_INTERVAL:
                self.blink_timer = 0
                self.blink_visible = not self.blink_visible

            self._despawn_blink_left -= 1
            if self._despawn_blink_left <= 0:
                self.alive = False   # habis, akan dihapus manager (despawn alami)

    # ──────────────────────────────────────────────────────────────────────
    def draw(self):
        if not self.alive:
            return
        # Saat despawn & sedang fase "mati" dari blink, jangan digambar
        if self.despawning and not self.blink_visible:
            return

        rect = arcade.rect.XYWH(self.x, self.y, self.size, self.size)
        arcade.draw_rect_filled(rect, BOX_COLOR)
    # ──────────────────────────────────────────────────────────────────────
    def get_bounds(self):
        half = self.size / 2
        return (self.x - half, self.x + half, self.y - half, self.y + half)


# ─── Manager ──────────────────────────────────────────────────────────────────

class PowerUpManager:
    """Mengelola satu kotak power-up aktif dalam satu waktu, termasuk
    siklus jatuh/mengapung/tenggelam/despawn dan jeda respawn ± 20 detik.
    """

    def __init__(self, map_width, map_height, surface_y):
        self.map_width  = map_width
        self.map_height = map_height
        self.surface_y  = surface_y

        self.current = None
        # Jeda pertama sebelum power-up pertama muncul
        self.respawn_timer = random.randint(RESPAWN_MIN // 2, RESPAWN_MAX // 2)

    # ──────────────────────────────────────────────────────────────────────
    def update(self):
        if self.current is None:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self._spawn_new()
            return

        self.current.update()
        if not self.current.alive:
            self.current = None
            self.respawn_timer = random.randint(RESPAWN_MIN, RESPAWN_MAX)

    def _spawn_new(self):
        self.current = PowerUpBox(self.map_width, self.map_height, self.surface_y)

    def draw(self):
        if self.current is not None:
            self.current.draw()

    # ──────────────────────────────────────────────────────────────────────
    def check_and_handle_collisions(self, player, enemy_list,
                                     dangerous_manager=None, eat_animations=None,
                                     on_player_pickup=None):
        """Panggil tiap frame dari on_update(). Mengecek tabrakan kotak
        power-up dengan main_fish dan dengan NPC ikan (untuk evolusi).

        on_player_pickup: callback opsional tanpa argumen, dipanggil saat
        main_fish menabrak kotak. Harus mengembalikan True kalau kotak
        boleh dikonsumsi (mis. slot power-up sedang kosong), atau False
        kalau kotak TIDAK boleh dikonsumsi dulu (mis. main_fish masih
        menyimpan/mengundi power-up lain). Kalau on_player_pickup tidak
        diisi, perilaku lama (langsung dapat poin) tetap dipakai.
        """
        box = self.current
        if box is None or box.eaten or not box.alive:
            return

        b_left, b_right, b_bottom, b_top = box.get_bounds()

        # ── Cek tabrakan dengan player ──
        p_left   = player.x - player.width / 2
        p_right  = player.x + player.width / 2
        p_bottom = player.y - player.height / 2
        p_top    = player.y + player.height / 2

        if (p_right >= b_left and p_left <= b_right and
                p_top >= b_bottom and p_bottom <= b_top):
            if on_player_pickup is not None:
                if on_player_pickup():
                    self._consume(box)
                return

            self._consume(box)
            player.score = getattr(player, 'score', 0) + PLAYER_POINT_REWARD
            player.total_points = getattr(player, 'total_points', 0) + PLAYER_POINT_REWARD
            if hasattr(player, 'check_evolution'):
                player.check_evolution()
            return

        # ── Cek tabrakan dengan NPC ikan (untuk evolusi) ──
        for fish in list(enemy_list):
            nama = fish.__class__.__name__

            if nama in ("smallfish", "jumpingsmallfish"):
                ukuran = 50
            elif nama in ("mediumfish", "speedmediumfish"):
                ukuran = 90
            elif nama == "hugefish":
                ukuran = 150
            else:
                continue

            half = ukuran / 2
            f_left, f_right = fish.x - half, fish.x + half
            f_bottom, f_top = fish.y - half, fish.y + half

            is_colliding = (
                f_right >= b_left and f_left <= b_right and
                f_top >= b_bottom and f_bottom <= b_top
            )
            if not is_colliding:
                continue

            self._consume(box)
            self._evolve_fish(fish, enemy_list, dangerous_manager)
            return

    def _consume(self, box):
        box.eaten = True
        box.alive = False
        self.current = None
        self.respawn_timer = random.randint(RESPAWN_MIN, RESPAWN_MAX)

    def _evolve_fish(self, fish, enemy_list, dangerous_manager):
        """Naikkan tahap evolusi NPC yang memakan power-up:
        small -> medium -> huge -> dangerous.
        """
        nama = fish.__class__.__name__
        x, y = fish.x, fish.y

        if nama in ("smallfish", "jumpingsmallfish"):
            new_fish = mediumfish(self.map_width, self.map_height, x, y)
            self._replace(fish, new_fish, enemy_list)

        elif nama in ("mediumfish", "speedmediumfish"):
            new_fish = hugefish(self.map_width, self.map_height, x, y)
            self._replace(fish, new_fish, enemy_list)

        elif nama == "hugefish":
            if dangerous_manager is None:
                return   # tidak ada manager dangerous fish, evolusi dibatalkan
            new_fish = dangerousfish(x, y, [(x, y)],
                                      speed=random.uniform(3.0, 4.5),
                                      patrol=True)
            new_fish._pick_random_patrol_waypoint(self.map_width, self.map_height)
            dangerous_manager.ambient_fish_list.append(new_fish)
            if fish in enemy_list:
                enemy_list.remove(fish)

    def _replace(self, old_fish, new_fish, enemy_list):
        if old_fish in enemy_list:
            idx = enemy_list.index(old_fish)
            enemy_list[idx] = new_fish
        else:
            enemy_list.append(new_fish)