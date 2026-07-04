# gameover.py
import arcade

SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 560

# Ukuran kotak notifikasi game over
BOX_WIDTH  = 340
BOX_HEIGHT = 220
BOX_COLOR  = (20, 20, 25)


class GameOverScreen:
    """Komponen 'Game Over': tampil sebagai kotak notifikasi di tengah layar
    saat nyawa main_fish habis (3x dimakan), dengan tombol RESTART dan MAIN MENU.

    Cara pakai di GameView:
        self.game_over_screen = GameOverScreen()
        # Saat nyawa habis (dipanggil SETELAH eaten_screen selesai):
        self.game_over_screen.start()
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

    def start(self):
        """Tampilkan layar game over."""
        self.active = True
        self.restart_hovered = False
        self.menu_hovered    = False

    def reset(self):
        """Sembunyikan kembali (dipakai saat restart/kembali ke menu)."""
        self.active = False

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

        # ── Kotak notifikasi ──
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.box_cx, self.box_cy, BOX_WIDTH, BOX_HEIGHT),
            BOX_COLOR
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(self.box_cx, self.box_cy, BOX_WIDTH, BOX_HEIGHT),
            arcade.color.RED, border_width=3
        )

        arcade.draw_text(
            "GAME OVER",
            x=self.box_cx, y=self.box_cy + 60,
            color=arcade.color.RED, font_size=26, bold=True,
            anchor_x="center", anchor_y="center",
        )
        arcade.draw_text(
            "Nyawamu telah habis!",
            x=self.box_cx, y=self.box_cy + 20,
            color=arcade.color.WHITE, font_size=13,
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
            return "restart"
        if self._hit_menu(x, y):
            return "menu"
        return None