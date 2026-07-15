import arcade
import os

SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 560

EATEN_DURATION = 120

# Ukuran kotak placeholder (ganti dengan ukuran image kamu nanti)
BOX_WIDTH  = 300
BOX_HEIGHT = 200
BOX_COLOR  = (180, 50, 50)   # merah gelap

# ─── PATH AUDIO ───────────────────────────────────────────────────────────────
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
RESPAWN_SFX_PATH = os.path.join(BASE_DIR, "assets", "sfx", "respawn_sfx", "respawn.mp3") 
DEAD_SFX_PATH    = os.path.join(BASE_DIR, "assets", "sfx", "gameover_sfx", "gameover.mp3") 


class EatenScreen:
    """Komponen 'dimakan': tampilkan kotak placeholder di tengah layar selama 4 detik,
    lalu panggil callback respawn.
    """

    def __init__(self):
        self.active    = False
        self.timer     = 0
        self._callback = None

        # ─── LOAD AUDIO ───────────────────────────────────────────────────────
        self._dead_sfx = None
        try:
            self._dead_sfx = arcade.load_sound(DEAD_SFX_PATH)
        except Exception as e:
            print(f"Gagal memuat SFX Kematian (dead.mp3): {e}")

    def start(self, callback=None):
        """Mulai layar dimakan."""
        self.active    = True
        self.timer     = EATEN_DURATION
        self._callback = callback

        # Catatan: arcade.play_sound sengaja dipindah ke GameView agar suara 
        # pas dengan animasi menciut/dimakan musuh sebelum kotak ini muncul.

    def update(self):
        if not self.active:
            return
        self.timer -= 1
        if self.timer <= 0:
            self.active = False
            if self._callback:
                self._callback()
                self._callback = None

    def draw(self, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT):
        """Gambar satu kotak placeholder di tengah layar."""
        if not self.active:
            return

        cx = screen_width  / 2
        cy = screen_height / 2

        # ── Kotak placeholder (ganti dengan image) ──
        arcade.draw_rect_filled(
            arcade.rect.XYWH(cx, cy, BOX_WIDTH, BOX_HEIGHT),
            BOX_COLOR
        )