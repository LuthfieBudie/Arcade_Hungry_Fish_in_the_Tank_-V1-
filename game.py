import arcade
import random
import math
import os
from pause import pause
from main_fish import mainfish
from small_fish import smallfish, jumpingsmallfish, speedmediumfish
from medium_fish import mediumfish
from huge_fish import hugefish
from seaweed import seaweed
from eat_fish import check_collision_and_respawn, PlayerEatenAnimation
from dangerous_fish import DangerousFishManager
from foodchain import FoodChain
from eaten import EatenScreen
from respawn import RespawnAnimator
from outside import WaterBoundary
from bugs import BugManager
from gameover import GameOverScreen


try:
    import win32api
    import win32con
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

WIDTH = 800
HEIGHT = 560


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_PATH = os.path.join(BASE_DIR, "assets", "music", "freeplay", "Pixel_Parade_1.mp3")


class GameView(arcade.View):


    def __init__(self):
        super().__init__()

        self.is_resuming = False
        # Dunia game selalu 3200×2240 terlepas dari ukuran layar
        self.MAP_WIDTH  = 800 * 4
        self.MAP_HEIGHT = 560 * 4

        # ── Sistem nyawa (lives) ──
        # Main fish punya 3 nyawa. Setiap kali dimakan, nyawa berkurang 1.
        # Saat nyawa habis (0), setelah eaten screen selesai, tampilkan Game Over.
        self.MAX_LIVES = 3
        self.lives     = self.MAX_LIVES
        self.game_over_screen = GameOverScreen()

        # ── Urutan "main fish dimakan" ──
        # 1) animasi mengecil menuju predator (mirip animasi makan biasa)
        # 2) jeda diam 2 detik
        # 3) baru kotak notifikasi "dimakan" muncul
        self._player_eaten_anim      = None   # objek animasi yang sedang berjalan
        self._death_wait_timer       = 0      # sisa frame jeda sebelum kotak muncul
        self._pending_death_callback = None   # _do_respawn atau _trigger_game_over
        self.DEATH_NOTIFY_DELAY      = 120    # 2 detik @ 60 FPS

        # ── Smoothing bar evolusi ──
        # Nilai skor yang ditampilkan di HUD "mengejar" skor asli secara
        # perlahan, supaya bar terlihat "pelan-pelan terisi" saat makan ikan.
        self._evo_display_score = 0.0

        self.camera     = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()

        self.player_fish = mainfish(x=self.MAP_WIDTH // 2, y=self.MAP_HEIGHT // 2)
        self.player_fish.is_being_eaten = False
        # Override trigger_respawn agar mati -> eaten screen (4 detik) -> respawn animasi
        _game_ref = self
        _orig_trigger = self.player_fish.trigger_respawn
        def _patched_trigger_respawn(target_x, target_y, map_height, eaten_by=None):
            # Jangan proses lagi kalau game sudah over (mencegah nyawa minus
            # akibat collision lain yang mungkin masih terdeteksi di frame yang sama)
            if _game_ref.game_over_screen.active:
                return
            # Jangan proses lagi kalau sedang dalam urutan "dimakan"
            # (animasi mengecil / jeda 2 detik) — cegah trigger dobel
            if self.player_fish.is_being_eaten:
                return

            # Reset skor dan state (sama seperti original)
            self.player_fish.score = max(0, self.player_fish.score - 9999)
            self.player_fish.speed_x = 0
            self.player_fish.speed_y = 0
            self.player_fish.is_sucking = False
            self.player_fish.suck_active_timer = 0
            if getattr(self.player_fish, 'is_dashing', False):
                self.player_fish.is_dashing = False
                try:
                    import arcade as _arc
                    _arc.unschedule(self.player_fish._perform_dash_step)
                except Exception:
                    pass

            # Kurangi nyawa setiap kali dimakan
            _game_ref.lives = max(0, _game_ref.lives - 1)

            # Tentukan aksi yang akan dijalankan SETELAH seluruh urutan
            # "dimakan" (animasi + jeda + kotak notifikasi) selesai
            if _game_ref.lives <= 0:
                _game_ref._pending_death_callback = _game_ref._trigger_game_over
            else:
                _game_ref._pending_death_callback = _game_ref._do_respawn

            # ── Mulai animasi "main fish dimakan" ──
            # Meniru animasi makan biasa, tapi terbalik: player yang
            # mengecil dan bergerak menuju predator yang memakannya.
            if eaten_by is not None:
                pred_x, pred_y = eaten_by
            else:
                pred_x, pred_y = self.player_fish.x, self.player_fish.y

            anim = PlayerEatenAnimation(self.player_fish, pred_x, pred_y)
            _game_ref._player_eaten_anim = anim
            _game_ref.eat_animations.append(anim)

            # Sembunyikan gambar main_fish normal selama seluruh urutan dimakan
            self.player_fish.is_being_eaten = True
        self.player_fish.trigger_respawn = _patched_trigger_respawn

        self.enemy_list = self.generate_enemies(
            jumlah_small=30, jumlah_medium=10, jumlah_huge=4, jarak_minimum=70
        )

        # ── Ikan kecil pelompat (schooling + makan bugs di udara) ──
        from outside import SURFACE_MARGIN_FROM_TOP as _SMT_INIT
        _water_max_y_init = self.MAP_HEIGHT - _SMT_INIT - 80
        for _grp in range(2):
            _cx = random.uniform(200, self.MAP_WIDTH - 200)
            _cy = random.uniform(max(100, _water_max_y_init - 250), _water_max_y_init)
            _sid = 900 + _grp
            for _ in range(4):
                _fx = max(25, min(_cx + random.uniform(-40, 40), self.MAP_WIDTH - 25))
                _fy = max(25, min(_cy + random.uniform(-40, 40), _water_max_y_init))
                _jf = jumpingsmallfish(self.MAP_WIDTH, self.MAP_HEIGHT, _fx, _fy)
                _jf.school_id = _sid
                self.enemy_list.append(_jf)

        # ── Medium fish cepat (kejar player SMALL, kabur dari player MEDIUM+) ──
        for _ in range(3):
            _sx = random.uniform(150, self.MAP_WIDTH - 150)
            _sy = random.uniform(150, _water_max_y_init)
            self.enemy_list.append(speedmediumfish(self.MAP_WIDTH, self.MAP_HEIGHT, _sx, _sy))

        self.seaweed_list = [
            seaweed(x=300,  y=80, width=60, height=90, color=arcade.color.GREEN),
            seaweed(x=1000, y=85, width=60, height=90, color=arcade.color.GREEN),
            seaweed(x=2000, y=80, width=60, height=90, color=arcade.color.GREEN),
            seaweed(x=2800, y=85, width=60, height=90, color=arcade.color.GREEN),
        ]

        self.eat_animations = []

        self.dangerous_manager = DangerousFishManager(WIDTH, HEIGHT)
        self.foodchain = FoodChain(self.MAP_WIDTH, self.MAP_HEIGHT)

        # Fitur baru
        self.eaten_screen   = EatenScreen()
        self.respawn_anim   = RespawnAnimator()
        self.water_boundary = WaterBoundary(
            map_width  = self.MAP_WIDTH,
            map_height = self.MAP_HEIGHT,
            screen_w   = self.window.width,
            screen_h   = self.window.height,
        )
        self.bug_manager = BugManager(
            map_width  = self.MAP_WIDTH,
            map_height = self.MAP_HEIGHT,
            surface_y  = self.water_boundary.surface_y,
        )

        self.mouse_screen_x = self.window.width  // 2
        self.mouse_screen_y = self.window.height // 2

    def on_show_view(self):
        """Dipanggil otomatis saat view ini ditampilkan."""
        arcade.set_background_color((10, 30, 50))
        self.window.set_mouse_position(self.window.width // 2, self.window.height // 2)
        self.window.set_mouse_visible(False)
        self._confine_mouse()

        try:
            self.window.current_music = arcade.Sound(MUSIC_PATH)
            try:
                from setting import load_settings as _ls
                _mvol = _ls().get("music_volume", 0.5)
            except Exception:
                _mvol = 0.5
            self.window.current_player = self.window.current_music.play(volume=_mvol, loop=True)
            
            # --- TAMBAHKAN BARIS INI DI GAME.PY ---
            self.window.current_music_name = "game"
            
            print("🎵 Musik gameplay berhasil diputar!")
        except Exception as e:
            print(f"No music {MUSIC_PATH}. Error: {e}")

    def on_hide_view(self):
        """Dipanggil otomatis saat view ini disembunyikan / diganti view lain."""
        self._release_mouse()
        self.window.set_mouse_visible(True)
        # PENTING: reset ke kamera default window saat keluar dari GameView.
        # Tanpa ini, self.camera / self.gui_camera tetap menjadi kamera
        # aktif terakhir, sehingga view berikutnya (menu, setting, dst.)
        # ikut menggambar lewat proyeksi kamera game yang salah ukuran
        # setelah window di-resize — inilah penyebab tombol menu
        # menumpuk/berantakan setelah main game lalu ganti ukuran layar.
        self.window.default_camera.use()

    def _confine_mouse(self):
        if not HAS_WIN32:
            return
        try:
            hwnd = win32gui.GetForegroundWindow()
            rect = win32gui.GetClientRect(hwnd)
            left_top     = win32gui.ClientToScreen(hwnd, (rect[0], rect[1]))
            right_bottom = win32gui.ClientToScreen(hwnd, (rect[2], rect[3]))
            win32api.ClipCursor((left_top[0], left_top[1], right_bottom[0], right_bottom[1]))
        except Exception:
            pass

    def _release_mouse(self):
        if HAS_WIN32:
            try:
                win32api.ClipCursor(None)
            except Exception:
                pass

    def generate_enemies(self, jumlah_small, jumlah_medium, jumlah_huge, jarak_minimum):
        fishes = []

        RADIUS = {"small": 40, "medium": 75, "huge": 130}
        BUFFER_EXTRA = 25

        placed = []

        # Batas area air (NPC tidak boleh spawn di area udara)
        from outside import SURFACE_MARGIN_FROM_TOP
        WATER_MAX_Y = self.MAP_HEIGHT - SURFACE_MARGIN_FROM_TOP - 30  # 30px safety margin

        def posisi_cukup_jauh(x, y, tipe_baru):
            r_baru = RADIUS[tipe_baru]
            for (px, py, tipe_lain) in placed:
                jarak_wajib = r_baru + RADIUS[tipe_lain] + BUFFER_EXTRA
                if math.sqrt((x - px) ** 2 + (y - py) ** 2) < jarak_wajib:
                    return False
            return True

        grid_cols, grid_rows = 6, 5
        cell_w = self.MAP_WIDTH / grid_cols
        cell_h = WATER_MAX_Y / grid_rows   # grid hanya di area air
        CEL_MARGIN = 30
        semua_sel = [(c, r) for c in range(grid_cols) for r in range(grid_rows)]

        def buat_urutan_sel(jumlah_dibutuhkan):
            urutan = []
            while len(urutan) < jumlah_dibutuhkan:
                satu_siklus = semua_sel.copy()
                random.shuffle(satu_siklus)
                urutan.extend(satu_siklus)
            return urutan[:jumlah_dibutuhkan]

        def titik_acak_di_sel(col, row):
            cell_min_x = col * cell_w
            cell_min_y = row * cell_h
            lo_x = max(25, cell_min_x + CEL_MARGIN)
            hi_x = min(self.MAP_WIDTH - 25, cell_min_x + cell_w - CEL_MARGIN)
            lo_y = max(25, cell_min_y + CEL_MARGIN)
            # Batasi ke WATER_MAX_Y agar tidak spawn di area udara
            hi_y = min(WATER_MAX_Y - CEL_MARGIN, cell_min_y + cell_h - CEL_MARGIN)
            hi_y = max(lo_y + 5, hi_y)  # pastikan hi_y > lo_y
            x = random.uniform(lo_x, hi_x)
            y = random.uniform(lo_y, hi_y)
            return x, y

        def cari_titik(col, row, tipe, percobaan=60):
            for _ in range(percobaan):
                x, y = titik_acak_di_sel(col, row)
                if posisi_cukup_jauh(x, y, tipe):
                    return x, y
            neighbors = [
                ((col + dc) % grid_cols, (row + dr) % grid_rows)
                for dc, dr in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]
            ]
            for nc, nr in neighbors:
                for _ in range(20):
                    x, y = titik_acak_di_sel(nc, nr)
                    if posisi_cukup_jauh(x, y, tipe):
                        return x, y
            for _ in range(percobaan):
                x = random.uniform(25, self.MAP_WIDTH - 25)
                y = random.uniform(25, WATER_MAX_Y)
                if posisi_cukup_jauh(x, y, tipe):
                    return x, y
            return (random.uniform(25, self.MAP_WIDTH - 25),
                    random.uniform(25, WATER_MAX_Y))

        rencana_besar = (["medium"] * jumlah_medium) + (["huge"] * jumlah_huge)
        random.shuffle(rencana_besar)
        urutan_sel_besar = buat_urutan_sel(len(rencana_besar))

        for i, tipe in enumerate(rencana_besar):
            col, row = urutan_sel_besar[i]
            x, y = cari_titik(col, row, tipe)
            placed.append((x, y, tipe))
            if tipe == "medium":
                fishes.append(mediumfish(self.MAP_WIDTH, self.MAP_HEIGHT, x, y))
            else:
                fishes.append(hugefish(self.MAP_WIDTH, self.MAP_HEIGHT, x, y))

        target_grouped = int(jumlah_small * 0.6)
        rencana_grup = []
        sisa_hitung = jumlah_small
        sudah_grouped_hitung = 0
        while sisa_hitung > 0:
            if sudah_grouped_hitung < target_grouped:
                ukuran = min(random.randint(3, 5), sisa_hitung)
                rencana_grup.append(ukuran)
                sudah_grouped_hitung += ukuran
            else:
                rencana_grup.append(1)
            sisa_hitung -= rencana_grup[-1]

        urutan_sel_small = buat_urutan_sel(len(rencana_grup))

        next_school_id = 0
        for idx, ukuran_grup in enumerate(rencana_grup):
            col, row = urutan_sel_small[idx]

            if ukuran_grup > 1:
                school_id = next_school_id
                next_school_id += 1
            else:
                school_id = None

            pusat_x, pusat_y = cari_titik(col, row, "small")

            for _ in range(ukuran_grup):
                offset_x = random.uniform(-40, 40)
                offset_y = random.uniform(-40, 40)
                fx = max(25, min(pusat_x + offset_x, self.MAP_WIDTH - 25))
                fy = max(25, min(pusat_y + offset_y, WATER_MAX_Y - 25))  # batas air
                fish = smallfish(self.MAP_WIDTH, self.MAP_HEIGHT, fx, fy)
                fish.school_id = school_id
                fishes.append(fish)
                placed.append((fx, fy, "small"))

        return fishes

    

    def on_show_view(self):
        arcade.set_background_color((10, 30, 50))
        self.window.set_mouse_position(self.window.width // 2, self.window.height // 2)
        self.window.set_mouse_visible(False)
        self._confine_mouse()




        if self.is_resuming:
            self.is_resuming = False  
            if hasattr(self.window, "current_player") and self.window.current_player:
                try:
                    self.window.current_player.play()  
                except Exception as e:
                    print(f"Gagal me-resume musik: {e}")
            return  
        



        if hasattr(self.window, "current_music") and self.window.current_music and self.window.current_player:
            self.window.current_music.stop(self.window.current_player)

        try:
            self.window.current_music = arcade.Sound(MUSIC_PATH)
            try:
                from setting import load_settings as _ls
                _mvol = _ls().get("music_volume", 0.5)
            except Exception:
                _mvol = 0.5
            self.window.current_player = self.window.current_music.play(volume=_mvol, loop=True)
        except Exception as e:
            print(f"No music {MUSIC_PATH}. Error: {e}")

    

    def on_hide_view(self):
        self._release_mouse()
        self.window.set_mouse_visible(True)

        if not self.is_resuming:
            if hasattr(self.window, "current_music") and self.window.current_music and self.window.current_player:
                self.window.current_music.stop(self.window.current_player)
        




    
    def on_draw(self):
        self.clear()

        self.camera.use()

        sand = arcade.rect.XYWH(self.MAP_WIDTH / 2, 20, self.MAP_WIDTH, 40)
        arcade.draw_rect_filled(sand, arcade.color.DESERT_SAND)

        for weed in self.seaweed_list:
            weed.draw()

        # Ikan yang sedang melompat digambar BELAKANGAN (setelah garis
        # permukaan/langit), sama seperti player saat di udara — supaya
        # benar-benar terlihat keluar dari air, bukan tertutup lapisan langit.
        for fish in self.enemy_list:
            if not getattr(fish, 'is_jumping', False):
                fish.draw()

        self.dangerous_manager.draw_world()

        # Gambar batas air (surface line, sky, percikan)
        self.water_boundary.draw_world()

        # Ikan yang sedang melompat — digambar di atas garis air
        for fish in self.enemy_list:
            if getattr(fish, 'is_jumping', False):
                fish.draw()

        # Gambar bugs di udara
        self.bug_manager.draw()

        for anim in self.eat_animations:
            anim.draw()

        self.player_fish.draw_suck_cone()
        # Sembunyikan gambar player normal selama animasi "dimakan" berjalan
        # (animasi shrink-menuju-predator sudah digambar lewat eat_animations di atas)
        if not self.player_fish.is_being_eaten:
            # Jika player di udara, gambar dengan animasi terbang
            if self.water_boundary.in_air:
                self.water_boundary.draw_player_in_air(self.player_fish)
            else:
                self.player_fish.draw()

        self.gui_camera.use()

        player = self.player_fish

        # ── Tentukan status/target evolusi & threshold skor ──
        if player.status == "SMALL":
            teks_target   = "MEDIUM"
            evo_threshold = 100
        elif player.status == "MEDIUM":
            teks_target   = "HUGE"
            evo_threshold = 500
        else:
            teks_target   = "MAX"
            evo_threshold = None   # HUGE sudah status maksimal

        # Nilai skor yang ditampilkan di bar "mengejar" skor asli secara
        # perlahan (easing) — supaya bar terlihat pelan-pelan terisi saat
        # main_fish memakan ikan, bukan langsung melompat penuh seketika.
        self._evo_display_score += (player.score - self._evo_display_score) * 0.06

        if evo_threshold:
            evo_progress = max(0.0, min(1.0, self._evo_display_score / evo_threshold))
        else:
            evo_progress = 1.0

        # ── BAR EVOLUSI (pengganti tampilan teks "GROW TO" & "POIN") ──
        EVO_W, EVO_H = 180, 16
        EVO_X = self.window.width - EVO_W - 20
        EVO_Y = self.window.height - 52

        if player.status == "SMALL":
            evo_color = (80, 220, 120)
        elif player.status == "MEDIUM":
            evo_color = (255, 170, 60)
        else:
            evo_color = (255, 215, 60)

        if evo_threshold:
            evo_num_label = f"[{int(self._evo_display_score)}/{evo_threshold}]"
        else:
            evo_num_label = f"[{player.score} PTS]"

        arcade.draw_text(f"GROW TO: {teks_target}  {evo_num_label}",
                         x=EVO_X, y=EVO_Y + EVO_H + 6,
                         color=arcade.color.WHITE, font_size=12, bold=True)

        arcade.draw_rect_filled(
            arcade.rect.XYWH(EVO_X + EVO_W/2, EVO_Y + EVO_H/2, EVO_W, EVO_H),
            (30, 30, 30, 180)
        )
        evo_fill_w = max(2, EVO_W * evo_progress)
        arcade.draw_rect_filled(
            arcade.rect.XYWH(EVO_X + evo_fill_w/2, EVO_Y + EVO_H/2, evo_fill_w, EVO_H),
            evo_color
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(EVO_X + EVO_W/2, EVO_Y + EVO_H/2, EVO_W, EVO_H),
            arcade.color.WHITE, border_width=1
        )

        if player.kebal_timer > 0:
            sisa = player.kebal_timer / 60
            arcade.draw_text(f"KEBAL: {sisa:.1f}s", x=10, y=self.window.height - 30,
                             color=arcade.color.YELLOW, font_size=13, bold=True)

        # ── BAR HISAP ──
        SUCK_X, SUCK_Y, SUCK_W, SUCK_H = 10, 10, 120, 14
        suck_progress = player.suck_bar / player.SUCK_BAR_MAX
        if player.is_sucking:
            suck_color = (80, 160, 255)
            suck_label = "HISAP AKTIF"
        elif player.suck_bar < player.SUCK_BAR_MAX:
            suck_color = (200, 140, 40)
            suck_label = "HISAP [ISI ULANG...]"
        else:
            suck_color = (60, 200, 100)
            suck_label = "HISAP [KLIK KANAN]"

        arcade.draw_rect_filled(
            arcade.rect.XYWH(SUCK_X + SUCK_W/2, SUCK_Y + SUCK_H/2, SUCK_W, SUCK_H),
            (30, 30, 30, 180)
        )
        fill_w = max(2, SUCK_W * suck_progress)
        arcade.draw_rect_filled(
            arcade.rect.XYWH(SUCK_X + fill_w/2, SUCK_Y + SUCK_H/2, fill_w, SUCK_H),
            suck_color
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(SUCK_X + SUCK_W/2, SUCK_Y + SUCK_H/2, SUCK_W, SUCK_H),
            arcade.color.WHITE, border_width=1
        )
        arcade.draw_text(suck_label, x=SUCK_X, y=SUCK_Y + SUCK_H + 2,
                         color=arcade.color.WHITE, font_size=9)

        # ── BAR DASH (3 charges) ──
        DASH_X, DASH_Y, DASH_W, DASH_H = 10, 45, 120, 14
        # Tampilkan 3 kotak kecil untuk charge
        charge_gap = 4
        charge_w   = (DASH_W - charge_gap * (player.DASH_MAX_CHARGES - 1)) / player.DASH_MAX_CHARGES
        for i in range(player.DASH_MAX_CHARGES):
            cx = DASH_X + i * (charge_w + charge_gap)
            if i < player.DASH_CHARGES:
                # Charge tersedia
                c_color = (255, 200, 40)
            else:
                # Charge sedang cooldown — tunjukkan progress regen charge berikutnya
                if i == player.DASH_CHARGES and player.dash_cooldown > 0:
                    prog = 1.0 - (player.dash_cooldown / player.DASH_COOLDOWN_PER)
                    prog = max(0.0, min(1.0, prog))
                    c_color = (255, 200, 40)
                    # Gambar background dulu
                    arcade.draw_rect_filled(
                        arcade.rect.XYWH(cx + DASH_W/2/player.DASH_MAX_CHARGES, DASH_Y + DASH_H/2, charge_w, DASH_H),
                        (50, 50, 20, 180)
                    )
                    fill_c = max(2, charge_w * prog)
                    arcade.draw_rect_filled(
                        arcade.rect.XYWH(cx + fill_c/2, DASH_Y + DASH_H/2, fill_c, DASH_H),
                        (200, 150, 20)
                    )
                    arcade.draw_rect_outline(
                        arcade.rect.XYWH(cx + charge_w/2, DASH_Y + DASH_H/2, charge_w, DASH_H),
                        arcade.color.WHITE, border_width=1
                    )
                    continue
                else:
                    c_color = (50, 50, 20, 180)
            arcade.draw_rect_filled(
                arcade.rect.XYWH(cx + charge_w/2, DASH_Y + DASH_H/2, charge_w, DASH_H),
                c_color
            )
            arcade.draw_rect_outline(
                arcade.rect.XYWH(cx + charge_w/2, DASH_Y + DASH_H/2, charge_w, DASH_H),
                arcade.color.WHITE, border_width=1
            )
        dash_label = f"DASH [{player.DASH_CHARGES}/{player.DASH_MAX_CHARGES}] [KLIK KIRI]"
        arcade.draw_text(dash_label, x=DASH_X, y=DASH_Y + DASH_H + 2,
                         color=arcade.color.WHITE, font_size=9)

        # ── BAR NYAWA (3 charges, sama gaya dengan bar dash) ──
        LIVES_X, LIVES_Y, LIVES_W, LIVES_H = 10, 80, 120, 14
        lives_gap = 4
        live_w = (LIVES_W - lives_gap * (self.MAX_LIVES - 1)) / self.MAX_LIVES
        for i in range(self.MAX_LIVES):
            lx = LIVES_X + i * (live_w + lives_gap)
            if i < self.lives:
                l_color = (220, 40, 40)       # nyawa tersisa — merah
            else:
                l_color = (50, 20, 20, 180)   # nyawa hilang — gelap
            arcade.draw_rect_filled(
                arcade.rect.XYWH(lx + live_w/2, LIVES_Y + LIVES_H/2, live_w, LIVES_H),
                l_color
            )
            arcade.draw_rect_outline(
                arcade.rect.XYWH(lx + live_w/2, LIVES_Y + LIVES_H/2, live_w, LIVES_H),
                arcade.color.WHITE, border_width=1
            )
        lives_label = f"NYAWA [{self.lives}/{self.MAX_LIVES}]"
        arcade.draw_text(lives_label, x=LIVES_X, y=LIVES_Y + LIVES_H + 2,
                         color=arcade.color.WHITE, font_size=9)

        self.dangerous_manager.draw_gui()
        self.water_boundary.draw_gui()

        # Layar hitam saat dimakan (paling atas, menutupi segalanya)
        self.eaten_screen.draw(self.window.width, self.window.height)

        # Notifikasi GAME OVER (paling atas dari segalanya, muncul setelah
        # kotak "dimakan" selesai DAN nyawa sudah habis)
        self.game_over_screen.draw(self.window.width, self.window.height)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_screen_x = x
        self.mouse_screen_y = y
        if self.game_over_screen.active:
            self.game_over_screen.check_hover(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        # Layar GAME OVER aktif: hanya tombol RESTART / MAIN MENU yang berfungsi
        if self.game_over_screen.active:
            if button == arcade.MOUSE_BUTTON_LEFT:
                aksi = self.game_over_screen.check_click(x, y)
                if aksi == "restart":
                    self._restart_game()
                elif aksi == "menu":
                    self._go_to_menu()
            return

        # Tidak bisa pakai ability saat dimakan (eaten screen aktif)
        if self.eaten_screen.active:
            return
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.player_fish.dash(self.window)
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self.player_fish.start_suck()

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.player_fish.stop_suck()

    def _do_respawn(self):
        """Callback: dipanggil EatenScreen saat 4 detik selesai."""
        self.player_fish.is_being_eaten = False
        self.respawn_anim.start(
            player     = self.player_fish,
            target_x   = self.MAP_WIDTH // 2,
            target_y   = self.MAP_HEIGHT // 2,
            map_height = self.MAP_HEIGHT,
        )
        self.window.set_mouse_position(self.window.width // 2, self.window.height // 2)

    def _trigger_game_over(self):
        """Callback: dipanggil EatenScreen setelah kotak 'dimakan' selesai
        DAN nyawa sudah habis (0). Menampilkan notifikasi GAME OVER."""
        self.player_fish.is_being_eaten = False
        self.game_over_screen.start()
        self._release_mouse()
        self.window.set_mouse_visible(True)
        if hasattr(self.window, "current_player") and self.window.current_player:
            try:
                self.window.current_player.pause()
            except Exception:
                pass

    def _restart_game(self):
        """Tombol RESTART pada layar Game Over: mulai game baru dari awal."""
        self._release_mouse()
        new_view = GameView()
        self.window.show_view(new_view)

    def _go_to_menu(self):
        """Tombol MAIN MENU pada layar Game Over: kembali ke menu utama."""
        self._release_mouse()
        self.window.set_mouse_visible(True)
        from menu import MenuView
        self.window.show_view(MenuView())

    def on_update(self, delta_time):
        # Update layar "dimakan" (timer 4 detik)
        self.eaten_screen.update()

        # Update animasi respawn (jatuh dari atas)
        self.respawn_anim.update()

        # ── Update NPC dan animasi tetap jalan saat eaten screen aktif ──
        # (ikan lain tetap bergerak, hanya player yang di-freeze)
        huge_list     = [f for f in self.enemy_list if f.__class__.__name__ == "hugefish"]
        small_list    = [f for f in self.enemy_list if f.__class__.__name__ == "smallfish"]
        jumping_list  = [f for f in self.enemy_list if f.__class__.__name__ == "jumpingsmallfish"]

        for fish in self.enemy_list:
            name = fish.__class__.__name__
            if name == "smallfish":
                fish.update(player=self.player_fish, huge_list=huge_list, all_small=small_list)
            elif name == "jumpingsmallfish":
                fish.update(player=self.player_fish, huge_list=huge_list, all_small=jumping_list,
                            bugs=self.bug_manager.bugs, eat_animations=self.eat_animations)
            elif name == "mediumfish":
                fish.update(player=self.player_fish, huge_list=huge_list)
            elif name == "speedmediumfish":
                fish.update(player=self.player_fish, huge_list=huge_list)
            elif name == "hugefish":
                fish.update(player=self.player_fish)
            else:
                fish.update()

        for anim in self.eat_animations:
            anim.update()
        self.eat_animations = [a for a in self.eat_animations if not a.done]

        self.foodchain.update(
            self.enemy_list, self.player_fish,
            self.MAP_WIDTH, self.MAP_HEIGHT, self.eat_animations
        )

        # Dangerous fish selalu bergerak — update DAN kamera selalu diproses
        self.dangerous_manager.update(self.camera, self.MAP_WIDTH, self.MAP_HEIGHT,
                                      enemy_list=self.enemy_list,
                                      eat_animations=self.eat_animations)

        # Kamera selalu mengikuti player (walaupun eaten screen aktif)
        _W = self.window.width; _H = self.window.height
        _tx = max(_W / 2,  min(self.player_fish.x, self.MAP_WIDTH  - _W / 2))
        _ty = max(_H / 2, min(self.player_fish.y, self.MAP_HEIGHT - _H / 2))
        self.camera.position = (
            self.camera.position[0] + (_tx - self.camera.position[0]) * 0.1,
            self.camera.position[1] + (_ty - self.camera.position[1]) * 0.1,
        )

        # ── Urutan "main fish dimakan" ──
        # Tahap 1: animasi mengecil menuju predator masih berjalan.
        # Tahap 2: animasi selesai, mulai hitung mundur jeda 2 detik.
        # Tahap 3: jeda selesai -> baru kotak notifikasi "dimakan" muncul.
        if self.player_fish.is_being_eaten:
            if self._player_eaten_anim is not None:
                if self._player_eaten_anim.done:
                    self._player_eaten_anim = None
                    self._death_wait_timer = self.DEATH_NOTIFY_DELAY
                return

            if self._death_wait_timer > 0:
                self._death_wait_timer -= 1
                if self._death_wait_timer <= 0:
                    callback = self._pending_death_callback
                    self._pending_death_callback = None
                    # Kotak notifikasi mulai tampil sekarang; player boleh
                    # terlihat lagi (diam, seperti perilaku sebelumnya)
                    self.player_fish.is_being_eaten = False
                    self.eaten_screen.start(callback=callback)
                return

        # Jika eaten screen aktif, freeze player — skip semua logic player
        if self.eaten_screen.active:
            return

        # Jika game over aktif, freeze player juga — hanya NPC yang tetap jalan
        if self.game_over_screen.active:
            return

        target_world_x = self.player_fish.x + (self.mouse_screen_x - (self.window.width / 2))
        target_world_y = self.player_fish.y + (self.mouse_screen_y - (self.window.height / 2))

        # Saat di udara, fisika dikontrol penuh oleh water_boundary (outside.py)
        # player.update() tetap dipanggil tapi posisi sudah ditangani di _update_in_air
        if not self.water_boundary.in_air:
            self.player_fish.update(target_world_x, target_world_y, self.MAP_WIDTH, self.MAP_HEIGHT)
        else:
            # Di udara: hanya update kebal/blink, skip gerak normal
            self.player_fish._update_kebal_blink()
        # Tick cooldown dash tiap frame
        self.player_fish.update_dash_cooldown()

        # Update water boundary (menangani fisika udara dan batas permukaan)
        mouse_world_x = self.player_fish.x + (self.mouse_screen_x - self.window.width / 2)
        self.water_boundary.update(self.player_fish, mouse_world_x)

        check_collision_and_respawn(
            self.player_fish, self.enemy_list,
            self.MAP_WIDTH, self.MAP_HEIGHT,
            self.window, self.eat_animations, jarak_minimum=120
        )

        dimakan_suck = self.player_fish.update_suck(
            self.enemy_list, self.eat_animations, self.MAP_WIDTH, self.MAP_HEIGHT
        )
        _water_max_y = self.MAP_HEIGHT - 600 - 30  # sama dengan WATER_MAX_Y
        import random as _rnd
        _eat_sfx_list = ["eat1.mp3","eat2.mp3","eat3.mp3","eat4.mp3","eat5.mp3"]
        try:
            from setting import load_settings as _ls_s
            _svol_suck = _ls_s().get("sfx_volume", 0.6)
        except Exception:
            _svol_suck = 0.6

        for fish in dimakan_suck:
            nama = fish.__class__.__name__

            # PanikFish dari seaweed — hapus permanen, tidak di-respawn
            if getattr(fish, 'is_panik', False):
                if fish in self.enemy_list:
                    self.enemy_list.remove(fish)
                self.player_fish.score += _rnd.randint(1, 3)
            else:
                # Ikan biasa — respawn ke posisi baru di area air
                fish.x = _rnd.uniform(100, self.MAP_WIDTH - 100)
                fish.y = _rnd.uniform(100, _water_max_y)
                if hasattr(fish, 'target_x'):
                    fish.target_x = _rnd.uniform(100, self.MAP_WIDTH - 100)
                    fish.target_y = _rnd.uniform(100, _water_max_y)
                if nama in ("smallfish", "jumpingsmallfish"):
                    self.player_fish.score += _rnd.randint(1, 3)
                elif nama in ("mediumfish", "speedmediumfish"):
                    if self.player_fish.status != "SMALL":
                        self.player_fish.score += _rnd.randint(5, 7)
                elif nama == "hugefish":
                    if self.player_fish.status == "HUGE":
                        self.player_fish.score += _rnd.randint(15, 20)

            self.player_fish.check_evolution()

            # SFX makan saat hisap
            try:
                _sfx_p = os.path.join(BASE_DIR, "assets", "sfx", "eat_sfx",
                                      _rnd.choice(_eat_sfx_list))
                arcade.play_sound(arcade.load_sound(_sfx_p), volume=_svol_suck)
            except Exception:
                pass

        for weed in self.seaweed_list:
            weed.check_dash_collision(
                self.player_fish, self.enemy_list,
                self.MAP_WIDTH, self.MAP_HEIGHT
            )

        self.dangerous_manager.check_collision(
            self.player_fish, self.window, self.window.width, self.window.height, self.MAP_WIDTH, self.MAP_HEIGHT
        )

        # Update bugs di udara
        self.bug_manager.update(self.player_fish, self.water_boundary.in_air, self.eat_animations)
        bug_score = self.bug_manager.consume_score()
        if bug_score > 0:
            self.player_fish.score += bug_score
            self.player_fish.check_evolution()



    def on_key_press(self, key, modifiers):
        # Layar GAME OVER aktif: nonaktifkan pause (ESC) sampai user memilih aksi
        if self.game_over_screen.active:
            return

        if key == arcade.key.ESCAPE:
            self._release_mouse()
            self.window.set_mouse_visible(True)

            try:
                sfx_pause_path = os.path.join(BASE_DIR, "assets", "sfx", "button_sfx", "14.mp3")
                sfx_pause = arcade.load_sound(sfx_pause_path)
                arcade.play_sound(sfx_pause, volume=0.6)
            except Exception as e:
                print(f"Gagal memutar SFX pause: {e}")



            self.is_resuming = True 
            if hasattr(self.window, "current_player") and self.window.current_player:
                try:
                    self.window.current_player.pause()  
                except Exception:
                    pass

            pause_view = pause(self)
            self.window.show_view(pause_view)
    
def main():
    window = arcade.Window(WIDTH, HEIGHT)
    start_view = GameView()
    window.show_view(start_view)
    arcade.run()

if __name__ == "__main__":
    main()