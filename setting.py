# setting.py
import arcade
import os
import json

WIDTH  = 800
HEIGHT = 560

SETTINGS_FILE = "settings.json"

DEFAULT = {
    "sfx_volume":   0.6,
    "music_volume": 0.5,
    "display_mode": "windowed",
}

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
BTN_SFX_DIR = os.path.join(BASE_DIR, "assets", "sfx", "button_sfx")




def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in DEFAULT.items():
                    data.setdefault(k, v)
                return data
        except Exception:
            pass
    return dict(DEFAULT)


def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Gagal simpan setting: {e}")


def apply_display(window, mode):
    """Terapkan mode layar. Dipanggil saat SAVE di setting."""
    try:
        if mode == "fullscreen":
            if not window.fullscreen:
                window.set_fullscreen(True)
        else:
            # Keluar dari fullscreen dulu jika perlu
            if window.fullscreen:
                window.set_fullscreen(False)
            # Set ukuran hanya jika berbeda dari sekarang
            target_w = 1280 if mode == "fixed" else 800
            target_h = 720  if mode == "fixed" else 560
            if window.width != target_w or window.height != target_h:
                window.set_size(target_w, target_h)
    except Exception as e:
        print(f"Gagal set display: {e}")


def play_btn_sfx(volume=0.6):
    try:
        import random
        sfx_files = [f for f in os.listdir(BTN_SFX_DIR) if f.endswith(".mp3")]
        if sfx_files:
            path = os.path.join(BTN_SFX_DIR, random.choice(sfx_files))
            arcade.play_sound(arcade.load_sound(path), volume=volume)
    except Exception:
        pass


# ── Helper tombol ──────────────────────────────────────────────────────────────

class _Btn:
    C_NORMAL = (30, 28, 24)
    C_HOVER  = (78, 62, 38)
    C_ACTIVE = (198, 150, 76)

    def __init__(self, cx, cy, w, h, label):
        self.cx = cx; self.cy = cy
        self.w  = w;  self.h  = h
        self.label   = label
        self.hovered = False

    def hit(self, x, y):
        return (self.cx - self.w/2 <= x <= self.cx + self.w/2 and
                self.cy - self.h/2 <= y <= self.cy + self.h/2)

    def draw(self, active=False):
        col = self.C_ACTIVE if active else (self.C_HOVER if self.hovered else self.C_NORMAL)
        arcade.draw_rect_filled(arcade.rect.XYWH(self.cx, self.cy, self.w, self.h), col)
        arcade.draw_rect_outline(arcade.rect.XYWH(self.cx, self.cy, self.w, self.h),
                                 (255, 255, 255), border_width=1)
        fs = 18 if len(self.label) <= 6 else 13
        arcade.draw_text(self.label, self.cx, self.cy, (255, 255, 255),
                         font_size=fs, bold=True,
                         anchor_x="center", anchor_y="center")


# ── View utama ─────────────────────────────────────────────────────────────────

class setting(arcade.View):

    def __init__(self):
        super().__init__()
        self.data = load_settings()

        # Buat tombol dengan posisi dummy (akan diupdate di _update_pos)
        self.sfx_minus = _Btn(0, 0, 44, 44, "−")
        self.sfx_plus  = _Btn(0, 0, 44, 44, "+")
        self.mus_minus = _Btn(0, 0, 44, 44, "−")
        self.mus_plus  = _Btn(0, 0, 44, 44, "+")
        self.btn_win   = _Btn(0, 0, 150, 44, "800×560")
        self.btn_fixed = _Btn(0, 0, 150, 44, "1280×720")
        self.btn_full  = _Btn(0, 0, 150, 44, "Fullscreen")
        self.btn_save  = _Btn(0, 0, 190, 50, "SAVE")
        self.btn_back  = _Btn(0, 0, 190, 50, "MAIN MENU")

        self._all = [
            self.sfx_minus, self.sfx_plus,
            self.mus_minus, self.mus_plus,
            self.btn_win, self.btn_fixed, self.btn_full,
            self.btn_save, self.btn_back,
        ]

    def _play_click_sfx(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            sfx_path = os.path.join(base_dir, "assets", "sfx", "button_sfx", "4.mp3")
            click_sound = arcade.load_sound(sfx_path)
            
            # Ambil setelan volume sfx dari file setting bawaan game Anda
            try:
                from setting import load_settings as _ls
                _svol = _ls().get("sfx_volume", 0.0)
            except Exception:
                _svol = 0.0
                
            arcade.play_sound(click_sound, volume=_svol)
        except Exception as e:
            print(f"Gagal memutar SFX tombol: {e}")

    def _update_pos(self):
        CX = self.window.width  // 2
        CY = self.window.height // 2
        self.sfx_minus.cx  = CX - 120;  self.sfx_minus.cy  = CY + 95
        self.sfx_plus.cx   = CX + 120;  self.sfx_plus.cy   = CY + 95
        self.mus_minus.cx  = CX - 120;  self.mus_minus.cy  = CY + 20
        self.mus_plus.cx   = CX + 120;  self.mus_plus.cy   = CY + 20
        self.btn_win.cx    = CX - 185;  self.btn_win.cy    = CY - 75
        self.btn_fixed.cx  = CX;        self.btn_fixed.cy  = CY - 75
        self.btn_full.cx   = CX + 185;  self.btn_full.cy   = CY - 75
        self.btn_save.cx   = CX - 110;  self.btn_save.cy   = CY - 170
        self.btn_back.cx   = CX + 110;  self.btn_back.cy   = CY - 170

    def _dummy_sep(self):
        pass

    # ── lifecycle ──────────────────────────────────────────────────────────────

    def on_show_view(self):
        arcade.set_background_color((9, 26, 45))
        self.window.set_mouse_visible(True)
        self._update_pos()

    # ── draw ───────────────────────────────────────────────────────────────────

    def on_draw(self):
        self.clear()
        # Reset ke kamera default supaya tidak mewarisi kamera custom
        # yang ditinggalkan aktif oleh GameView.
        self.window.default_camera.use()
        self._update_pos()
        CX = self.window.width  // 2
        CY = self.window.height // 2

        # Judul
        arcade.draw_text("SETTINGS", CX, CY + 220,
                         (216, 178, 92), font_size=26, bold=True,
                         anchor_x="center", anchor_y="center")

        # ── SFX ──
        arcade.draw_text("SFX VOLUME", CX, CY + 130,
                         (238, 230, 210), font_size=13, bold=True,
                         anchor_x="center", anchor_y="center")
        self._draw_bar(CX, CY + 95, self.data["sfx_volume"])
        self.sfx_minus.draw()
        self.sfx_plus.draw()

        # ── MUSIK ──
        arcade.draw_text("MUSIC VOLUME", CX, CY + 55,
                         (238, 230, 210), font_size=13, bold=True,
                         anchor_x="center", anchor_y="center")
        self._draw_bar(CX, CY + 20, self.data["music_volume"])
        self.mus_minus.draw()
        self.mus_plus.draw()

        # ── DISPLAY ──
        arcade.draw_text("DISPLAY MODE", CX, CY - 40,
                         (238, 230, 210), font_size=13, bold=True,
                         anchor_x="center", anchor_y="center")
        dm = self.data["display_mode"]
        self.btn_win.draw(active=(dm == "windowed"))
        self.btn_fixed.draw(active=(dm == "fixed"))
        self.btn_full.draw(active=(dm == "fullscreen"))

        # ── SAVE / BACK ──
        self.btn_save.draw()
        self.btn_back.draw()

    def _draw_bar(self, cx, cy, value):
        """10 kotak kecil sebagai bar volume."""
        steps = 10
        bw, bh, gap = 18, 20, 4
        total_w = steps * (bw + gap) - gap
        sx = cx - total_w / 2
        filled = round(value * steps)

        for i in range(steps):
            bx = sx + i * (bw + gap) + bw / 2
            col = (66, 158, 132) if i < filled else (24, 40, 54)
            arcade.draw_rect_filled(arcade.rect.XYWH(bx, cy, bw, bh), col)
            arcade.draw_rect_outline(arcade.rect.XYWH(bx, cy, bw, bh),
                                     (150, 138, 108), border_width=1)

        arcade.draw_text(f"{int(value * 100)}%", cx, cy - bh // 2 - 11,
                         arcade.color.LIGHT_GRAY, font_size=10,
                         anchor_x="center", anchor_y="center")

    # ── input ──────────────────────────────────────────────────────────────────

    def on_mouse_motion(self, x, y, dx, dy):
        for b in self._all:
            b.hovered = b.hit(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            self._play_click_sfx()
            return

        STEP = 0.1

        if self.sfx_minus.hit(x, y):
            self.data["sfx_volume"] = max(0.0, round(self.data["sfx_volume"] - STEP, 1))
            play_btn_sfx(self.data["sfx_volume"])

        elif self.sfx_plus.hit(x, y):
            self.data["sfx_volume"] = min(1.0, round(self.data["sfx_volume"] + STEP, 1))
            play_btn_sfx(self.data["sfx_volume"])

        elif self.mus_minus.hit(x, y):
            self.data["music_volume"] = max(0.0, round(self.data["music_volume"] - STEP, 1))
            self._apply_music_vol()

        elif self.mus_plus.hit(x, y):
            self.data["music_volume"] = min(1.0, round(self.data["music_volume"] + STEP, 1))
            self._apply_music_vol()

        elif self.btn_win.hit(x, y):
            self._play_click_sfx()
            self.data["display_mode"] = "windowed"

        elif self.btn_fixed.hit(x, y):
            self._play_click_sfx()
            self.data["display_mode"] = "fixed"

        elif self.btn_full.hit(x, y):
            self._play_click_sfx()
            self.data["display_mode"] = "fullscreen"

        elif self.btn_save.hit(x, y):
            self._play_click_sfx()
            save_settings(self.data)
            apply_display(self.window, self.data["display_mode"])
            self._go_menu()

        elif self.btn_back.hit(x, y):
            self._play_click_sfx()
            self._go_menu()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self._play_click_sfx()
            self._go_menu()

    # ── helpers ────────────────────────────────────────────────────────────────

    def _apply_music_vol(self):
        if hasattr(self.window, "current_player") and self.window.current_player:
            try:
                self.window.current_player.volume = self.data["music_volume"]
            except Exception:
                pass

    def _go_menu(self):
        from menu import MenuView
        self.window.show_view(MenuView())