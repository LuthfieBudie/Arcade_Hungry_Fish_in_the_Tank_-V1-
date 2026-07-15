import arcade

WIDTH  = 800
HEIGHT = 560

FRAMES_BEFORE_LOAD = 2

DOT_INTERVAL = 0.35


class LoadingScreen(arcade.View):

    def __init__(self, on_ready=None):
        super().__init__()
        self._on_ready = on_ready

        self._frame_count     = 0
        self._loading_started = False

        self._dot_timer = 0.0
        self._dot_count = 0

    # ── LIFECYCLE ────────────────────────────────────────────────────────
    def on_show_view(self):
        arcade.set_background_color((10, 20, 35))
        self._frame_count     = 0
        self._loading_started = False
        self._dot_timer = 0.0
        self._dot_count = 0

    # ── DRAW ─────────────────────────────────────────────────────────────
    def on_draw(self):
        self.clear()
        # Reset ke kamera default (konsisten dengan view menu/help/setting lain)
        self.window.default_camera.use()

        cx = self.window.width  / 2
        cy = self.window.height / 2

        arcade.draw_text(
            "FeastQuarium",
            x=cx, y=cy + 40,
            color=arcade.color.YELLOW, font_size=30, bold=True,
            anchor_x="center", anchor_y="center",
        )

        dots = "." * (self._dot_count + 1)
        arcade.draw_text(
            f"Loading{dots}",
            x=cx, y=cy - 20,
            color=arcade.color.WHITE, font_size=18, bold=True,
            anchor_x="center", anchor_y="center",
        )

    # ── UPDATE ───────────────────────────────────────────────────────────
    def on_update(self, delta_time):
        # Animasi titik-titik berjalan terus (murni kosmetik)
        self._dot_timer += delta_time
        if self._dot_timer >= DOT_INTERVAL:
            self._dot_timer = 0.0
            self._dot_count = (self._dot_count + 1) % 3

        if self._loading_started:
            return

        # Tunggu beberapa frame supaya teks "Loading..." di atas SUDAH
        # sempat tergambar ke layar sebelum kita memanggil proses berat.
        self._frame_count += 1
        if self._frame_count >= FRAMES_BEFORE_LOAD:
            self._loading_started = True
            self._go_next()

    def _go_next(self):
        if self._on_ready is not None:
            next_view = self._on_ready()
        else:
            from game import GameView
            next_view = GameView()
        self.window.show_view(next_view)