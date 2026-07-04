import arcade

SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 560


EATEN_DURATION = 240

# Ukuran kotak placeholder (ganti dengan ukuran image kamu nanti)
BOX_WIDTH  = 300
BOX_HEIGHT = 200
BOX_COLOR  = (180, 50, 50)   # merah gelap — ganti sesuai selera / image


class EatenScreen:
    """Komponen 'dimakan': tampilkan kotak placeholder di tengah layar selama 4 detik,
    lalu panggil callback respawn.

    Cara pakai di GameView:
        self.eaten_screen = EatenScreen()
        # Saat player mati:
        self.eaten_screen.start(callback=self._do_respawn)
        # Di on_update:
        self.eaten_screen.update()
        # Di on_draw (gui camera, paling atas):
        self.eaten_screen.draw()
        # Blokir update game saat aktif:
        if self.eaten_screen.active:
            return
    """

    def __init__(self):
        self.active    = False
        self.timer     = 0
        self._callback = None

    def start(self, callback=None):
        """Mulai layar dimakan."""
        self.active    = True
        self.timer     = EATEN_DURATION
        self._callback = callback

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
        """Gambar satu kotak placeholder di tengah layar.

        UNTUK MENGGANTI DENGAN IMAGE:
            Ganti baris arcade.draw_rect_filled(...) dengan:
            arcade.draw_texture_rect(texture, arcade.rect.XYWH(cx, cy, BOX_WIDTH, BOX_HEIGHT))
        """
        if not self.active:
            return

        cx = screen_width  / 2
        cy = screen_height / 2

        # ── Kotak placeholder (ganti dengan image) ──
        arcade.draw_rect_filled(
            arcade.rect.XYWH(cx, cy, BOX_WIDTH, BOX_HEIGHT),
            BOX_COLOR
        )