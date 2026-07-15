# gameover.py
import csv
import os
import math

import arcade

SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 560

# Ukuran kotak notifikasi game over
BOX_WIDTH  = 340
BOX_HEIGHT = 250
BOX_COLOR  = (20, 20, 25)

# ── BARU: animasi hitung poin (count-up dari 0 -> total_points) ──
COUNT_DURATION = 60   # ± 1 detik @ 60fps untuk angka naik dari 0 ke total

# ── BARU: animasi banner "NEW HIGH SCORE!" ──
HIGHSCORE_PULSE_SPEED = 0.12   # kecepatan pulsing ukuran teks banner
HIGHSCORE_GOLD        = (255, 215, 0)

# File CSV tempat highscore disimpan — sama persis dengan yang dipakai
# highscore.py, supaya perbandingan "apakah ini rekor baru?" akurat.
FILE_NAME = "username.csv"


def check_is_new_highscore(total_points, filename=FILE_NAME):
    """Cek apakah total_points sesi ini adalah rekor PRIBADI baru untuk
    user yang sedang aktif.

    PENTING soal "user aktif": sama seperti konvensi yang dipakai
    game.py._save_highscore_to_csv() dan highscore.py — user yang sedang
    main adalah baris data PERTAMA di csv (name.py selalu menaruh user
    yang sedang dipakai di baris paling atas). Jadi perbandingannya HARUS
    ke skor terbaik user itu SENDIRI, BUKAN skor tertinggi semua user
    (kalau dibandingkan ke semua user, pemain baru dengan skor kecil
    hampir tidak akan pernah dianggap "rekor baru").

    PENTING: fungsi ini HARUS dipanggil SEBELUM baris skor sesi ini
    ditambahkan ke csv (sebelum _save_highscore_to_csv() dipanggil),
    supaya skor sesi ini tidak ikut dibandingkan dengan dirinya sendiri.
    """
    if not os.path.exists(filename):
        return True   # belum ada data sama sekali -> otomatis rekor baru

    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as f:
            reader = list(csv.reader(f))
    except Exception as e:
        print(f"Gagal membaca highscore untuk perbandingan: {e}")
        return False

    if len(reader) < 2 or not reader[1] or not reader[1][0].strip():
        return True   # belum ada user aktif tercatat -> anggap rekor baru

    active_row = reader[1]   # baris data PERTAMA = user yang sedang aktif
    try:
        prev_best = int(active_row[3].strip())
    except (ValueError, IndexError):
        prev_best = -1

    return total_points > prev_best


class GameOverScreen:
    """Komponen 'Game Over': tampil sebagai kotak notifikasi di tengah layar
    saat nyawa main_fish habis (3x dimakan), dengan tombol RESTART dan MAIN MENU.

    Cara pakai di GameView:
        self.game_over_screen = GameOverScreen()

        # Saat nyawa habis (dipanggil SETELAH eaten_screen selesai):
        # Cek highscore DULU, SEBELUM disimpan ke csv (lihat check_is_new_highscore).
        from gameover import check_is_new_highscore
        is_new_hs = check_is_new_highscore(self.player_fish.total_points)
        self.game_over_screen.start(
            total_points=self.player_fish.total_points,
            total_time=self.total_time,
            is_new_highscore=is_new_hs,
        )
        self._save_highscore_to_csv()   # baru simpan SETELAH is_new_hs dihitung

        # Di on_update():
        self.game_over_screen.update()

        # Di on_draw (gui camera, paling atas, setelah eaten_screen.draw()):
        self.game_over_screen.draw(self.window.width, self.window.height)
        # Di on_mouse_motion:
        self.game_over_screen.check_hover(x, y)
        # Di on_mouse_press:
        aksi = self.game_over_screen.check_click(x, y)
        if aksi == "restart": ...
        elif aksi == "menu": ...
    """

    def __init__(self):
        self.active = False
        self.total_points = 0
        self.total_time = 0.0

        # ── BARU: state animasi count-up angka poin ──
        self.displayed_points = 0     # angka yang SEDANG ditampilkan (0 -> total_points)
        self.count_timer = 0          # penghitung frame untuk animasi count-up
        self._count_done = False      # True kalau count-up sudah selesai

        self.count_sound_player = None

        # ── BARU: state highscore ──
        self.is_new_highscore = False
        self.highscore_timer = 0.0    # penghitung waktu untuk pulsing banner

        self.restart_btn_w = 150
        self.restart_btn_h = 46
        self.menu_btn_w    = 150
        self.menu_btn_h    = 46

        self.restart_hovered = False
        self.menu_hovered    = False

        # Posisi dihitung dinamis (lihat _update_pos)
        self.box_cx = SCREEN_WIDTH  / 2
        self.box_cy = SCREEN_HEIGHT / 2
        self.restart_btn_x = self.box_cx - 85
        self.restart_btn_y = self.box_cy - 65
        self.menu_btn_x    = self.box_cx + 85
        self.menu_btn_y    = self.box_cy - 65

    def start(self, total_points=0, total_time=0.0, is_new_highscore=False):
        """Tampilkan layar game over.

        is_new_highscore: True kalau total_points ini rekor tertinggi baru
        (hitung dengan check_is_new_highscore() SEBELUM data disimpan ke csv).
        """
        self.active = True
        self.total_points = total_points
        self.total_time = total_time
        self.restart_hovered = False
        self.menu_hovered    = False

        # ── BARU: reset animasi count-up setiap kali layar ini dibuka ──
        self.displayed_points = 0
        self.count_timer = 0
        self._count_done = False

        # ── BARU: simpan status highscore & reset timer pulsing banner ──
        self.is_new_highscore = is_new_highscore
        self.highscore_timer = 0.0

        if self.total_points > 0 and self.count_sound_player is None:
            try:
                _base = os.path.dirname(os.path.abspath(__file__))
                sfx_path = os.path.join(_base, "assets", "sfx", "gameover_sfx", "number.wav")
                count_sfx = arcade.load_sound(sfx_path)
                try:
                    from setting import load_settings as _ls
                    _svol = _ls().get("sfx_volume", 0.6)
                except Exception:
                    _svol = 0.6
                self.count_sound_player = arcade.play_sound(count_sfx, volume=_svol, loop=True)
            except Exception as e:
                print(f"Gagal memutar SFX makan: {e}")

    def reset(self):
        """Sembunyikan kembali (dipakai saat restart/kembali ke menu)."""
        self.active = False

    # ── BARU: UPDATE (panggil tiap frame dari GameView.on_update()) ──────
    def update(self):
        if not self.active:
            return

        # Fase 1: angka poin naik dari 0 ke total_points dengan ease-out
        # (cepat di awal, melambat menjelang selesai) selama COUNT_DURATION frame.
        if not self._count_done:
            self.count_timer += 1
            t = min(1.0, self.count_timer / COUNT_DURATION)
            eased = 1 - (1 - t) ** 3   # ease-out cubic
            self.displayed_points = int(self.total_points * eased)

            if self.is_new_highscore and self.count_timer == (COUNT_DURATION - 30):
                try:
                    _base = os.path.dirname(os.path.abspath(__file__))
                    # Ganti "highscore.mp3" dengan nama file SFX selebrasi milikmu
                    hs_sfx_path = os.path.join(_base, "assets", "sfx", "gameover_sfx", "highscore.mp3")
                    hs_sfx = arcade.load_sound(hs_sfx_path)
                    
                    try:
                        from setting import load_settings as _ls
                        _svol = _ls().get("sfx_volume", 0.6)
                    except Exception:
                        _svol = 0.6
                        
                    arcade.play_sound(hs_sfx, volume=_svol) # Sekaligus berbunyi (tanpa loop)
                except Exception as e:
                    print(f"Gagal memutar SFX High Score: {e}")

            if self.count_timer >= COUNT_DURATION:
                self.displayed_points = self.total_points   # pastikan pas di angka akhir
                self._count_done = True

                if self.count_sound_player is not None:
                    try:
                        arcade.stop_sound(self.count_sound_player)
                    except Exception:
                        pass
                    self.count_sound_player = None

        # Fase 2: setelah angka selesai dihitung, kalau ini rekor baru,
        # jalankan timer untuk animasi pulsing banner "NEW HIGH SCORE!".
        elif self.is_new_highscore:
            self.highscore_timer += 1

    def _update_pos(self, screen_width, screen_height):
        self.box_cx = screen_width  / 2
        self.box_cy = screen_height / 2
        self.restart_btn_x = self.box_cx - 85
        self.restart_btn_y = self.box_cy - 65
        self.menu_btn_x    = self.box_cx + 85
        self.menu_btn_y    = self.box_cy - 65

    # ── DRAW ─────────────────────────────────────────────────────────────

    def draw(self, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT):
        if not self.active:
            return

        self._update_pos(screen_width, screen_height)

        # ── BARU: kalau ini rekor baru & angka sudah selesai dihitung,
        # border kotak ikut "berdenyut" emas sebagai penekanan tambahan. ──
        show_highscore_banner = self._count_done and self.is_new_highscore
        if show_highscore_banner:
            pulse = 0.5 + 0.5 * math.sin(self.highscore_timer * HIGHSCORE_PULSE_SPEED)
            border_color = HIGHSCORE_GOLD
            border_width = 3 + int(pulse * 3)   # tebal border berdenyut 3..6
        else:
            border_color = arcade.color.RED
            border_width = 3

        # ── Kotak notifikasi ──
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.box_cx, self.box_cy, BOX_WIDTH, BOX_HEIGHT),
            BOX_COLOR
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(self.box_cx, self.box_cy, BOX_WIDTH, BOX_HEIGHT),
            border_color, border_width=border_width
        )

        arcade.draw_text(
            "GAME OVER",
            x=self.box_cx, y=self.box_cy + 95,
            color=arcade.color.RED, font_size=24, bold=True,
            anchor_x="center", anchor_y="center",
        )

        # ── BARU: banner "NEW HIGH SCORE!" — cuma tampil kalau memang
        # rekor baru DAN animasi count-up sudah kelar (biar gak numpuk
        # sama animasi angka yang masih jalan). Ukurannya pulsing pakai
        # sin() supaya terasa hidup/menarik perhatian. ──
        if show_highscore_banner:
            scale = 1.0 + 0.15 * math.sin(self.highscore_timer * HIGHSCORE_PULSE_SPEED)
            arcade.draw_text(
                "★ NEW HIGH SCORE! ★",
                x=self.box_cx, y=self.box_cy + 65,
                color=HIGHSCORE_GOLD, font_size=int(15 * scale), bold=True,
                anchor_x="center", anchor_y="center",
            )

        # ── BARU: angka poin sekarang pakai self.displayed_points (hasil
        # animasi count-up), BUKAN langsung self.total_points. ──
        arcade.draw_text(
            f"Total Point: {self.displayed_points}",
            x=self.box_cx, y=self.box_cy + 32,
            color=arcade.color.WHITE, font_size=13, bold=True,
            anchor_x="center", anchor_y="center",
        )

        _tt_minutes = int(self.total_time // 60)
        _tt_seconds = int(self.total_time % 60)
        arcade.draw_text(
            f"Total Time: {_tt_minutes:02d}:{_tt_seconds:02d}",
            x=self.box_cx, y=self.box_cy + 4,
            color=arcade.color.WHITE, font_size=13, bold=True,
            anchor_x="center", anchor_y="center",
        )

        # ── Tombol RESTART ──
        r_color = (60, 180, 100) if self.restart_hovered else (40, 130, 70)
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.restart_btn_x, self.restart_btn_y,
                              self.restart_btn_w, self.restart_btn_h),
            r_color
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(self.restart_btn_x, self.restart_btn_y,
                              self.restart_btn_w, self.restart_btn_h),
            arcade.color.WHITE, border_width=1
        )
        arcade.draw_text(
            "RESTART",
            x=self.restart_btn_x, y=self.restart_btn_y,
            color=arcade.color.WHITE, font_size=14, bold=True,
            anchor_x="center", anchor_y="center",
        )

        # ── Tombol MAIN MENU ──
        m_color = (60, 180, 100) if self.menu_hovered else (40, 130, 70)
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.menu_btn_x, self.menu_btn_y,
                              self.menu_btn_w, self.menu_btn_h),
            m_color
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(self.menu_btn_x, self.menu_btn_y,
                              self.menu_btn_w, self.menu_btn_h),
            arcade.color.WHITE, border_width=1
        )
        arcade.draw_text(
            "MAIN MENU",
            x=self.menu_btn_x, y=self.menu_btn_y,
            color=arcade.color.WHITE, font_size=14, bold=True,
            anchor_x="center", anchor_y="center",
        )

    # ── INPUT ────────────────────────────────────────────────────────────

    def _hit_restart(self, x, y):
        half_w, half_h = self.restart_btn_w / 2, self.restart_btn_h / 2
        return (self.restart_btn_x - half_w <= x <= self.restart_btn_x + half_w and
                self.restart_btn_y - half_h <= y <= self.restart_btn_y + half_h)

    def _hit_menu(self, x, y):
        half_w, half_h = self.menu_btn_w / 2, self.menu_btn_h / 2
        return (self.menu_btn_x - half_w <= x <= self.menu_btn_x + half_w and
                self.menu_btn_y - half_h <= y <= self.menu_btn_y + half_h)

    def check_hover(self, x, y):
        """Panggil dari on_mouse_motion. Tidak melakukan apa-apa jika tidak aktif."""
        if not self.active:
            return
        self.restart_hovered = self._hit_restart(x, y)
        self.menu_hovered    = self._hit_menu(x, y)

    def check_click(self, x, y):
        """Panggil dari on_mouse_press. Mengembalikan 'restart', 'menu', atau None."""
        if not self.active:
            return None
        if self._hit_restart(x, y):
            self.reset()
            return "restart"
        if self._hit_menu(x, y):
            self.reset()
            return "menu"
        return None