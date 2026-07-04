import math


# ─── Ease functions ───────────────────────────────────────────────────────────

def _ease_out_bounce(t: float) -> float:
    """Efek 'mental' memantul saat mendarat."""
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


def _ease_in_out_quad(t: float) -> float:
    """Ease in-out halus untuk horizontal drift."""
    if t < 0.5:
        return 2 * t * t
    return 1 - (-2 * t + 2) ** 2 / 2


# ─── Konstanta ────────────────────────────────────────────────────────────────

# Tinggi di atas batas atas MAP dari mana ikan mulai jatuh
SPAWN_ABOVE_MAP = 200

# Kecepatan animasi (nilai kecil = lebih lambat / dramatis)
SPAWN_SPEED = 0.028   # naik per frame; selesai dalam ~36 frame ≈ 0.6 detik


# ─── Animator ─────────────────────────────────────────────────────────────────

class RespawnAnimator:
    """Mengelola animasi jatuh player dari atas ke posisi target.

    Animator ini bekerja terpisah dari mainfish.trigger_respawn() bawaan
    agar bisa dipakai bersama EatenScreen (delay 4 detik sebelum jatuh).

    Setelah animasi selesai, on_done_callback dipanggil (opsional).
    """

    def __init__(self):
        self.running  = False
        self._player  = None
        self._start_y = 0.0
        self._tgt_y   = 0.0
        self._tgt_x   = 0.0
        self._progress = 0.0
        self._on_done  = None

    # ──────────────────────────────────────────────────────────────────────────
    def start(self, player, target_x: float, target_y: float,
              map_height: float, on_done=None):
        """Mulai animasi.

        Parameters
        ----------
        player      : objek mainfish
        target_x/y  : koordinat pendaratan di world space
        map_height  : tinggi total map (untuk hitung titik awal jatuh)
        on_done     : callback opsional saat animasi selesai
        """
        self._player   = player
        self._tgt_x    = float(target_x)
        self._tgt_y    = float(target_y)
        self._start_y  = float(map_height) + SPAWN_ABOVE_MAP
        self._progress = 0.0
        self._on_done  = on_done
        self.running   = True

        # Set posisi awal pada player dan tandai spawning
        player.x           = target_x
        player.y           = self._start_y
        player.speed_x     = 0.0
        player.speed_y     = 0.0
        player.is_spawning = True
        player.spawn_start_y  = self._start_y
        player.spawn_target_y = self._tgt_y
        player.spawn_progress = 0.0

        # Invincibility selama + sesudah animasi
        player.kebal_timer    = player.KEBAL_DURASI
        player.blink_visible  = True
        player.blink_timer    = 0

        # Hentikan dash / suck yang mungkin aktif
        if getattr(player, 'is_dashing', False):
            player.is_dashing = False
            try:
                import arcade
                arcade.unschedule(player._perform_dash_step)
            except Exception:
                pass
        player.is_sucking        = False
        player.suck_active_timer = 0

    # ──────────────────────────────────────────────────────────────────────────
    def update(self):
        """Panggil setiap frame dari GameView.on_update()."""
        if not self.running:
            return

        p = self._player
        self._progress += SPAWN_SPEED
        if self._progress >= 1.0:
            self._progress = 1.0

        t      = self._progress
        ease_t = _ease_out_bounce(t)

        # Posisi Y: jatuh dari start ke target dengan bounce
        p.y = self._start_y + (self._tgt_y - self._start_y) * ease_t

        # Sync ke atribut bawaan mainfish agar blink dll. tetap jalan
        p.spawn_progress = t
        p.spawn_start_y  = self._start_y
        p.spawn_target_y = self._tgt_y

        if self._progress >= 1.0:
            # Selesai
            p.y            = self._tgt_y
            p.x            = self._tgt_x
            p.is_spawning  = False
            p.spawn_progress = 1.0
            self.running   = False
            if self._on_done:
                self._on_done()
                self._on_done = None