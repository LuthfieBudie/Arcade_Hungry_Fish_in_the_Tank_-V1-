# outside.py

import arcade
import math
import random
import os

import audio_registry





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

# ── SFX bubble: dibuat "sustained" (looping) selama BUBBLE_SUSTAIN_FRAMES
# supaya konsisten kedengaran ~1 detik setiap kali nyebrang permukaan,
# tidak bergantung ke durasi asli file bubble.mp3 (yang bisa saja sangat
# pendek/langsung terpotong kalau cuma dimainkan sekali/one-shot). ──
BUBBLE_SUSTAIN_FRAMES = 60   # ~1 detik @ 60fps

# ── SFX outside (ambient) — mulai diputar SAAT MASIH DI DALAM AIR tapi
# sudah mendekati perbatasan permukaan (bukan dipicu oleh lompat). Makin
# dekat ke permukaan, makin kencang, dan tepat DI permukaan (sebelum
# benar-benar lompat keluar) volume sudah FULL. Selama di udara, volume
# tetap full (karena sudah full sejak di permukaan). ──
OUTSIDE_VOLUME_MIN_FRAC  = 0.25   # volume saat baru masuk jangkauan (paling jauh)
OUTSIDE_VOLUME_MAX_FRAC  = 3.0    # volume saat tepat di permukaan / di udara
OUTSIDE_APPROACH_RANGE   = 300.0  # px di bawah permukaan tempat sfx mulai kedengaran


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

        # ── SFX: di-load SEKALI di sini, dipakai berkali-kali tanpa
        # baca file lagi tiap kali dipicu. ──
        self._jump_sfx    = self._load_sfx("assets", "sfx", "jump_sfx", "jump.mp3")
        self._splash_sfx  = self._load_sfx("assets", "sfx", "jump_sfx", "splash.mp3")
        self._bubble_sfx  = self._load_sfx("assets", "sfx", "outside_sfx", "bubble.mp3")
        self._outside_sfx = self._load_sfx("assets", "sfx", "outside_sfx", "outside.mp3")

        # Referensi player suara "outside" yang SEDANG loop (untuk stop nanti)
        self._outside_player = None

        # ── Bubble sustained: player suara bubble yang sedang loop +
        # sisa frame sebelum otomatis dihentikan (lihat BUBBLE_SUSTAIN_FRAMES) ──
        self._bubble_player = None
        self._bubble_timer  = 0

        # Jeda singkat setelah mendarat (splash masuk air) sebelum ambient
        # 'outside' boleh mulai lagi lewat sistem approach — supaya tidak
        # langsung nyala ulang di frame yang sama persis saat baru mendarat
        # (posisi masih persis di garis permukaan).
        self._outside_restart_cooldown = 0

    def _load_sfx(self, *path_parts):
        """Load satu file sfx, kembalikan None kalau gagal (tidak crash)."""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            return arcade.load_sound(os.path.join(base_dir, *path_parts))
        except Exception as e:
            print(f"[outside.py] GAGAL load sfx '{path_parts[-1]}': {e}")
            return None

    def _sfx_volume(self):
        try:
            from setting import load_settings as _ls
            return _ls().get("sfx_volume", 0.6)
        except Exception:
            return 0.6

    def _play_one_shot(self, sfx):
        """Mainkan sfx SEKALI (jump/splash/bubble — bukan loop)."""
        if sfx is None:
            return
        try:
            arcade.play_sound(sfx, volume=self._sfx_volume())
        except Exception as e:
            print(f"Gagal memutar sfx: {e}")

    def _start_outside_loop(self, start_vol=None):
        """Mulai ambient 'outside'. Dipanggil dari _update_outside_ambient
        begitu player masuk jangkauan OUTSIDE_APPROACH_RANGE dari permukaan
        (baik masih di air maupun sudah di udara)."""
        if self._outside_sfx is None:
            return
        self._stop_outside_loop()   # jaga-jaga, jangan sampai dobel
        if start_vol is None:
            start_vol = self._sfx_volume() * OUTSIDE_VOLUME_MIN_FRAC
        try:
            self._outside_player = arcade.play_sound(
                self._outside_sfx, volume=start_vol, loop=True
            )
            audio_registry.register(self._outside_player)
        except Exception as e:
            print(f"Gagal memutar sfx outside: {e}")

    def _stop_outside_loop(self):
        """Hentikan ambient 'outside' — dipanggil pas player menjauh dari
        perbatasan permukaan (balik nyelam dalam) atau saat respawn."""
        if self._outside_player is None:
            return
        try:
            arcade.stop_sound(self._outside_player)
        except Exception:
            pass
        audio_registry.unregister(self._outside_player)
        self._outside_player = None

    def _update_outside_ambient(self, player):
        """Panggil TIAP FRAME (baik lagi di air maupun di udara).

        Menghitung seberapa dekat player ke garis permukaan:
          - Masih di dalam air & mendekati permukaan (<= OUTSIDE_APPROACH_RANGE
            px dari permukaan) -> ambient mulai kedengaran, makin dekat makin
            kencang, sampai FULL tepat saat menyentuh permukaan.
          - Sudah di udara -> tetap FULL (karena sudah full sejak di permukaan).
          - Jauh dari permukaan (baik lagi nyelam dalam) -> ambient berhenti.
        """
        if self._outside_restart_cooldown > 0:
            self._outside_restart_cooldown -= 1

        base = self._sfx_volume()

        if self.in_air:
            # Sudah di udara: pertahankan full volume. Kalau entah kenapa
            # belum ada player aktif (misal race condition), mulai di full.
            if self._outside_player is None:
                self._start_outside_loop(start_vol=base * OUTSIDE_VOLUME_MAX_FRAC)
            else:
                try:
                    self._outside_player.volume = base * OUTSIDE_VOLUME_MAX_FRAC
                except Exception:
                    pass
            return

        # Masih di air: hitung jarak player ke permukaan dari BAWAH.
        player_top   = player.y + PLAYER_REF_HEIGHT / 2
        dist_below   = self.surface_y - player_top   # >0 = masih di bawah permukaan

        if dist_below <= OUTSIDE_APPROACH_RANGE:
            t = 1.0 - max(0.0, min(1.0, dist_below / OUTSIDE_APPROACH_RANGE))
            frac = OUTSIDE_VOLUME_MIN_FRAC + (OUTSIDE_VOLUME_MAX_FRAC - OUTSIDE_VOLUME_MIN_FRAC) * t
            vol  = max(0.0, min(1.0, base * frac))
            if self._outside_player is None:
                if self._outside_restart_cooldown <= 0:
                    self._start_outside_loop(start_vol=vol)
            else:
                try:
                    self._outside_player.volume = vol
                except Exception:
                    pass
        else:
            # Masih jauh dari permukaan -> pastikan ambient tidak bunyi.
            self._stop_outside_loop()

    def _play_bubble_sustained(self):
        """Mainkan bubble sfx sebagai loop pendek yang bertahan ~1 detik
        (BUBBLE_SUSTAIN_FRAMES), bukan one-shot. Ini membuat bubble sfx
        konsisten kedengaran setiap kali nyebrang permukaan, tidak
        tergantung durasi asli file bubble.mp3."""
        if self._bubble_sfx is None:
            return
        # Stop instance bubble sebelumnya kalau masih ada (jaga-jaga biar
        # tidak dobel/tumpuk saat lompat cepat berturut-turut)
        if self._bubble_player is not None:
            try:
                arcade.stop_sound(self._bubble_player)
            except Exception:
                pass
            audio_registry.unregister(self._bubble_player)
            self._bubble_player = None
        try:
            self._bubble_player = arcade.play_sound(
                self._bubble_sfx, volume=self._sfx_volume(), loop=True
            )
            audio_registry.register(self._bubble_player)
        except Exception as e:
            print(f"Gagal memutar sfx bubble: {e}")
        self._bubble_timer = BUBBLE_SUSTAIN_FRAMES

    def _tick_bubble_sustain(self):
        """Panggil tiap frame — hentikan bubble sfx otomatis setelah
        BUBBLE_SUSTAIN_FRAMES (~1 detik)."""
        if self._bubble_timer <= 0:
            return
        self._bubble_timer -= 1
        if self._bubble_timer <= 0 and self._bubble_player is not None:
            try:
                arcade.stop_sound(self._bubble_player)
            except Exception:
                pass
            audio_registry.unregister(self._bubble_player)
            self._bubble_player = None

    # ──────────────────────────────────────────────────────────────────────────

    def update(self, player, mouse_world_x=None):
        if getattr(player, 'is_spawning', False):
            # Player bisa tiba-tiba di-respawn (misal dimakan huge fish /
            # dangerous fish) SAAT MASIH DI UDARA/DEKAT PERMUKAAN. Kalau
            # begitu, method ini langsung return di sini SETIAP frame
            # selama animasi respawn, jadi jalur normal yang biasanya
            # menghentikan ambient 'outside' tidak akan tercapai. Tanpa
            # ini, sfx bisa nyangkut terus-menerus — hentikan di sini.
            if self._outside_player is not None:
                self._stop_outside_loop()
            if self._bubble_player is not None:
                try:
                    arcade.stop_sound(self._bubble_player)
                except Exception:
                    pass
                audio_registry.unregister(self._bubble_player)
                self._bubble_player = None
            self._bubble_timer = 0
            self.in_air      = False
            self._air_frames = 0
            return

        if not self.in_air:
            self._update_in_water(player)
        else:
            self._update_in_air(player, mouse_world_x)

        self._update_outside_ambient(player)
        self._tick_bubble_sustain()

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

            # ── SFX: (1) lompat keluar air, (2) bubble di perbatasan
            # (sustained ~1 detik). Ambient 'outside' TIDAK di-start di
            # sini lagi — sudah ditangani _update_outside_ambient() yang
            # mulai membesar saat MENDEKATI permukaan (sebelum lompat),
            # jadi di titik ini seharusnya sudah full volume. ──
            self._play_one_shot(self._jump_sfx)
            self._play_bubble_sustained()
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

            # ── SFX: (2) jatuh ke air, (3) bubble di perbatasan
            # (sustained ~1 detik, baru hilang setelahnya), (4) hentikan
            # ambient 'outside' karena sudah kembali ke air. Cooldown
            # singkat dipasang supaya sistem approach (_update_outside_ambient)
            # tidak langsung menyalakannya lagi di frame yang sama persis
            # (posisi masih pas di garis permukaan). ──
            self._play_one_shot(self._splash_sfx)
            self._play_bubble_sustained()
            self._stop_outside_loop()
            self._outside_restart_cooldown = 20

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