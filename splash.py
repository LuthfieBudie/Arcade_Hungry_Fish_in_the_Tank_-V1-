import os
import arcade

WIDTH  = 800
HEIGHT = 560

# ── Durasi tiap fase (detik) ──
FADE_IN_TIME  = 1.0
HOLD_TIME     = 1.2
FADE_OUT_TIME = 0.8

BG_COLOR = (255, 255, 255)   # Putih bersih (sesuai pengaturan kamu)

# Lebar logo = sekian persen dari lebar window (ubah di sini kalau mau
# lebih besar/kecil lagi)
LOGO_WIDTH_RATIO = 0.20


class SplashScreen(arcade.View):
    """Logo studio yang fade-in -> hold -> fade-out, lalu pindah view.

    on_finish: fungsi tanpa argumen yang HARUS mengembalikan sebuah
    arcade.View baru. Kalau tidak diisi, defaultnya akan menuju MenuView.
    Klik mouse / tekan tombol apa saja akan langsung skip ke akhir animasi.
    """

    def __init__(self, on_finish=None):
        super().__init__()
        self._on_finish = on_finish

        self._elapsed = 0.0
        self._skipped = False
        self._done = False

        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, "assets", "image", "logo", "logo1.png")

        self.logo_sprite = None
        self.logo_list = arcade.SpriteList()
        self._logo_base_width = 0
        if os.path.exists(logo_path):
            self.logo_sprite = arcade.Sprite(logo_path)
            self._logo_base_width = self.logo_sprite.width   # lebar ASLI, sebelum di-scale
            self.logo_list.append(self.logo_sprite)

        self._intro_sfx = None
        try:
            sfx_path = os.path.join(base_dir, "assets", "sfx", "intro_sfx", "intro.mp3")
            if os.path.exists(sfx_path):
                self._intro_sfx = arcade.load_sound(sfx_path)
        except Exception as e:
            print(f"Gagal memuat file SFX intro: {e}")
            self._intro_sfx = None

    # ── LIFECYCLE ────────────────────────────────────────────────────────
    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)
        self.window.set_mouse_visible(True)
        self._update_positions()

        # Ambil volume SFX dari file settings, default ke 0.5 jika file/key tidak ditemukan
        try:
            from setting import load_settings as _ls
            _svol = _ls().get("sfx_volume", 0)
        except Exception:
            _svol = 0.5

        # Putar musik/SFX intro secara otomatis saat splash screen pertama kali muncul
        if self._intro_sfx is not None:
            try:
                arcade.play_sound(self._intro_sfx, volume=_svol)
            except Exception as e:
                print(f"Gagal memutar SFX intro: {e}")

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self._update_positions()

    def _update_positions(self):
        CX = self.window.width  // 2
        CY = self.window.height // 2
        if self.logo_sprite:
            self.logo_sprite.center_x = CX
            self.logo_sprite.center_y = CY
            # PENTING: pakai self._logo_base_width (lebar ASLI tekstur), bukan
            # self.logo_sprite.width (itu sudah ikut ter-scale) -> supaya
            # tidak "loncat-loncat" tiap frame.
            target_w = self.window.width * LOGO_WIDTH_RATIO
            scale = target_w / self._logo_base_width if self._logo_base_width else 1
            self.logo_sprite.scale = scale

    # ── ANIMASI ──────────────────────────────────────────────────────────
    def _current_alpha(self):
        """Hitung alpha (0-255) logo berdasarkan fase animasi saat ini."""
        if self._skipped:
            return 0

        t = self._elapsed
        if t < FADE_IN_TIME:
            progress = t / FADE_IN_TIME
            eased = 1 - (1 - progress) ** 3   # ease-out cubic: mulus, melambat di akhir
            return int(255 * eased)
        t -= FADE_IN_TIME

        if t < HOLD_TIME:
            return 255
        t -= HOLD_TIME

        if t < FADE_OUT_TIME:
            return int(255 * (1 - t / FADE_OUT_TIME))

        return 0

    def on_update(self, delta_time):
        if self._done:
            return

        # PENTING: frame pertama sering punya delta_time besar (karena window
        # baru dibuka / masih memuat logo & SFX intro sebelum frame pertama
        # sempat ke-render). Kalau delta_time itu langsung ditambahkan mentah2,
        # animasi fade-in jadi "meloncat" -> logo terlihat langsung muncul
        # penuh alih-alih fade bertahap. Makanya di-clamp dulu di sini.
        delta_time = min(delta_time, 1 / 30)

        self._elapsed += delta_time
        total = FADE_IN_TIME + HOLD_TIME + FADE_OUT_TIME
        if self._skipped or self._elapsed >= total:
            self._finish()

    def _finish(self):
        if self._done:
            return
        self._done = True

        if self._on_finish is not None:
            next_view = self._on_finish()
        else:
            from menu import MenuView
            next_view = MenuView()
        self.window.show_view(next_view)

    # ── DRAW ─────────────────────────────────────────────────────────────
    def on_draw(self):
        self.clear()
        self.window.default_camera.use()
        self._update_positions()

        alpha = self._current_alpha()

        if self.logo_sprite:
            self.logo_sprite.alpha = max(0, min(255, alpha))
            self.logo_list.draw()

    # ── INPUT (klik/tekan apa saja untuk langsung skip) ──────────────────
    def _skip(self):
        if not self._skipped and not self._done:
            self._skipped = True
            # Intro SFX tidak diputar ulang di sini agar suaranya tidak saling bertumpukan

    def on_mouse_press(self, x, y, button, modifiers):
        self._skip()

    def on_key_press(self, key, modifiers):
        self._skip()


def main():
    window = arcade.Window(WIDTH, HEIGHT, "Splash Test")
    window.show_view(SplashScreen())
    arcade.run()


if __name__ == "__main__":
    main()