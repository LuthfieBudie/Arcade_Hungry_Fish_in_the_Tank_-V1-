# outside.py

import arcade
import math
import random





SURFACE_MARGIN_FROM_TOP = 600   



JUMP_SPEED_Y = 5.0



GRAVITY = 0.1


AIR_DRAG_X = 0.94



AIR_MAX_SPEED_X = 6.0



AIR_ACCEL_X = 0.010




AIR_MAX_FRAMES = 180





PLAYER_REF_HEIGHT = 30  



DASH_JUMP_ZONE = 20

SPLASH_COUNT = 6


# ─── Percikan ─────────────────────────────────────────────────────────────────

class _Splash:
    def __init__(self, x, y): 
        self.x    = x
        self.y    = y
        self.vx   = random.uniform(-3, 3)
        self.vy   = random.uniform(1, 4)
        self.life = random.randint(15, 30)
        self.max_life = self.life
        self.size = random.randint(4, 8)

    def update(self):
        self.x  += self.vx
        self.vy -= 0.12
        self.y  += self.vy
        self.life -= 1

    def draw(self):
        if self.life <= 0:
            return
        alpha = int(180 * (self.life / self.max_life))
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.x, self.y, self.size, self.size // 2 + 2),
            (100, 180, 255, alpha)
        )

    @property
    def done(self):
        return self.life <= 0


# ─── WaterBoundary ────────────────────────────────────────────────────────────

class WaterBoundary:
    def __init__(self, map_width, map_height, screen_w=800, screen_h=560):
        self.map_width  = map_width
        self.map_height = map_height
        self.screen_w   = screen_w
        self.screen_h   = screen_h

        # surface_y = batas permukaan air di world space
        # Area di ATAS surface_y = udara
        # Area di BAWAH surface_y = air (gameplay utama)
        self.surface_y = map_height - SURFACE_MARGIN_FROM_TOP

        self.in_air      = False
        self._air_frames = 0
        self._splashes   = []

    # ──────────────────────────────────────────────────────────────────────────

    def update(self, player, mouse_world_x=None):
        if getattr(player, 'is_spawning', False):
            self.in_air      = False
            self._air_frames = 0
            return

        if not self.in_air:
            self._update_in_water(player)
        else:
            self._update_in_air(player, mouse_world_x)

        for s in self._splashes:
            s.update()
        self._splashes = [s for s in self._splashes if not s.done]

    def _update_in_water(self, player):
        """Blokir player di bawah permukaan.
        Lompat hanya saat DASH dan posisi dekat/menyentuh surface.
        Gunakan PLAYER_REF_HEIGHT (ukuran SMALL) bukan player.height
        agar medium/huge tidak otomatis menyentuh surface lebih cepat.
        """
        is_dashing = getattr(player, 'is_dashing', False)

        # Pakai ref height agar ikan besar tidak lebih mudah menyentuh surface
        player_top = player.y + PLAYER_REF_HEIGHT / 2

        at_surface = player_top >= self.surface_y - DASH_JUMP_ZONE

        if at_surface and is_dashing:
            self.in_air      = True
            self._air_frames = 0
            player.y         = self.surface_y + PLAYER_REF_HEIGHT / 2 + 2
            player.speed_y   = JUMP_SPEED_Y
            self._spawn_splash(player.x, self.surface_y)
            return

        # Blokir menggunakan ref height agar konsisten
        if player_top >= self.surface_y:
            player.y = self.surface_y - PLAYER_REF_HEIGHT / 2 - 1
            if player.speed_y > 0:
                player.speed_y = 0

    def _update_in_air(self, player, mouse_world_x):
        """Fisika di udara — sepenuhnya independen dari ukuran ikan.

        Gravitasi, durasi, dan kecepatan sama persis untuk SMALL, MEDIUM, HUGE.
        Menggunakan PLAYER_REF_HEIGHT bukan player.height untuk semua batas posisi.
        """
        self._air_frames += 1

        # Gravitasi tetap — tidak berubah berdasarkan status/ukuran ikan
        player.speed_y -= GRAVITY

        # Setelah AIR_MAX_FRAMES (1 detik), gravitasi tambahan paksa turun
        if self._air_frames > AIR_MAX_FRAMES:
            player.speed_y -= GRAVITY * 2.0

        # Kontrol KIRI/KANAN saja
        if mouse_world_x is not None:
            dx = mouse_world_x - player.x
            if abs(dx) > 20:
                direction = 1 if dx > 0 else -1
                player.speed_x += direction * AIR_ACCEL_X * min(abs(dx), 400)

        if abs(player.speed_x) > AIR_MAX_SPEED_X:
            player.speed_x = math.copysign(AIR_MAX_SPEED_X, player.speed_x)
        player.speed_x *= AIR_DRAG_X

        player.x += player.speed_x
        player.y += player.speed_y

        # Batas atas MAP — pakai ref height agar konsisten
        max_y = self.map_height - PLAYER_REF_HEIGHT / 2
        if player.y > max_y:
            player.y       = max_y
            player.speed_y = -abs(player.speed_y) * 0.3

        # Batas kiri/kanan
        half_w = player.width / 2
        if player.x < half_w:
            player.x       = half_w
            player.speed_x = 0
        if player.x > self.map_width - half_w:
            player.x       = self.map_width - half_w
            player.speed_x = 0

        # Kembali ke air — pakai ref height
        if player.y - PLAYER_REF_HEIGHT / 2 <= self.surface_y:
            self.in_air      = False
            self._air_frames = 0
            player.y         = self.surface_y - PLAYER_REF_HEIGHT / 2 + 1
            player.speed_y   = 0
            self._spawn_splash(player.x, self.surface_y)

    def _spawn_splash(self, x, y):
        for _ in range(SPLASH_COUNT):
            self._splashes.append(_Splash(x, y))

    # ──────────────────────────────────────────────────────────────────────────
    # DRAW
    # ──────────────────────────────────────────────────────────────────────────

    def draw_world(self):
        """Gambar area udara, garis permukaan air, dan percikan."""
        sky_h  = self.map_height - self.surface_y
        sky_cx = self.map_width / 2
        sky_cy = self.surface_y + sky_h / 2

        if sky_h > 0:
            # Langit biru terang di area udara
            arcade.draw_rect_filled(
                arcade.rect.XYWH(sky_cx, sky_cy, self.map_width, sky_h),
                (135, 206, 235, 120)
            )

        # Garis permukaan air
        arcade.draw_line(0, self.surface_y, self.map_width, self.surface_y,
                         (60, 140, 220), line_width=4)
        arcade.draw_line(0, self.surface_y - 6, self.map_width, self.surface_y - 6,
                         (40, 100, 180, 120), line_width=2)

        for s in self._splashes:
            s.draw()

    def draw_player_in_air(self, player):
        """Kotak polos saat di udara — siap diganti image.

        Ukuran kotak menggunakan player.width/height asli agar secara visual
        tetap sesuai status ikan, tapi fisika tetap pakai PLAYER_REF_HEIGHT.
        """
        if not self.in_air:
            return
        if player.kebal_timer > 0 and not player.blink_visible:
            return
        arcade.draw_rect_filled(
            arcade.rect.XYWH(player.x, player.y, player.width, player.height),
            arcade.color.PURPLE
        )

    def draw_gui(self):
        pass