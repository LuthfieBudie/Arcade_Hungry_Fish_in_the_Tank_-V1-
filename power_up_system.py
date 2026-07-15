# power_up_system.py
#
# Sistem power-up untuk main_fish:
#
#   1) Saat main_fish makan kotak power-up (lihat power_up.py), TIDAK
#      langsung dapat efek. Bar power-up di tengah bawah layar akan
#      menampilkan animasi "gambling": teks berganti-ganti acak di
#      antara 5 nama power-up selama 1.5 detik (dengan SFX SEKALI saat
#      undian dimulai), lalu berhenti (dengan efek glow sebentar) di
#      hasil final yang sudah ditentukan.
#   2) Setelah animasi selesai, power-up hasil undian DISIMPAN (bukan
#      langsung dipakai) — bar yang sama kini menampilkan nama power-up
#      yang tersimpan itu, siap dipakai.
#   3) Player memakai power-up yang tersimpan dengan menekan tombol E —
#      setiap power-up punya SFX aktivasinya sendiri (dimainkan sekali
#      saat dipakai).
#      Slot cuma 1 — kotak power-up baru tidak bisa diambil selama masih
#      ada power-up tersimpan / animasi undian masih berjalan.
#
# 5 jenis power-up:
#   FAST        -> main_fish bergerak lebih cepat 10 detik
#   FREEZE      -> semua ikan (termasuk dangerous fish & bugs) berhenti
#                  bergerak 7 detik (main_fish tidak terpengaruh)
#   LIVES       -> +1 nyawa (no-op kalau nyawa sudah penuh)
#   INVINCIBLE  -> main_fish tidak bisa dimakan selama 8 detik
#   CHOMP       -> main_fish bisa memakan ikan apa saja termasuk
#                  dangerous fish selama 8 detik

import os
import random
import math

import arcade

POWERUP_ORDER = ["FAST", "FREEZE", "LIVES", "INVINCIBLE", "CHOMP"]

POWERUP_LABELS = {
    "FAST":       "FAST",
    "FREEZE":     "FREEZE",
    "LIVES":      "1+ LIVES",
    "INVINCIBLE": "INVINCIBLE",
    "CHOMP":      "CHOMP CHOMP",
}

POWERUP_COLORS = {
    "FAST":       (70, 170, 255),
    "FREEZE":     (150, 220, 255),
    "LIVES":      (230, 70, 70),
    "INVINCIBLE": (255, 215, 60),
    "CHOMP":      (255, 110, 190),
}

# ── Animasi gambling ──
GAMBLE_DURATION    = 60   # 1 detik @ 60fps — fase acak berganti-ganti
GAMBLE_CYCLE_EVERY = 5    # ganti teks tiap 5 frame selama fase acak
RESULT_HOLD        = 45   # tampilkan hasil final sebentar sebelum masuk bar

# ── Durasi efek (frame @ 60fps) ──
FAST_DURATION        = 600   # 10 detik
FREEZE_DURATION      = 420   # 7 detik
INVINCIBLE_DURATION  = 480   # 8 detik
CHOMP_DURATION       = 480   # 8 detik

FAST_SPEED_MULTIPLIER = 1.8   # main_fish 1.8x lebih cepat saat FAST aktif

# ── Path SFX ──
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
GAMBLE_SFX_PATH = os.path.join(BASE_DIR, "assets", "sfx", "eat_sfx", "eat_fishfood.mp3")

# SFX aktivasi tiap power-up (dimainkan sekali saat tombol E dipakai).
# Kalau suatu key tidak punya file (mis. INVINCIBLE belum ada asetnya),
# cukup jangan dimasukkan ke dict ini — otomatis di-skip tanpa error.
POWERUP_SFX_DIR = os.path.join(BASE_DIR, "assets", "sfx", "powerup_sfx")
POWERUP_SFX_FILES = {
    "FAST":   "fast.mp3",
    "FREEZE": "freeze.mp3",
    "CHOMP":  "chompchomp.mp3",
    "LIVES":  "health1.mp3",
}


# ─────────────────────────────────────────────────────────────────────────
# ANIMASI GAMBLING
# ─────────────────────────────────────────────────────────────────────────
class PowerUpRevealAnimation:
    """Teks berganti acak di antara 5 power-up selama GAMBLE_DURATION frame,
    lalu 'berhenti' tepat di hasil final (result_key) yang sudah ditentukan
    dari awal — mirip animasi gacha/slot machine.

    on_complete: callback opsional (result_key), dipanggil sekali saat
    animasi selesai total (dipakai untuk menyimpan power-up ke slot).
    """

    def __init__(self, result_key, on_complete=None):
        self.result_key  = result_key
        self.on_complete = on_complete

        self.timer     = 0
        self.total     = GAMBLE_DURATION + RESULT_HOLD
        self.cycle_key = random.choice(POWERUP_ORDER)
        self._settled  = False
        self.done      = False

    def update(self):
        if self.done:
            return

        self.timer += 1

        if self.timer < GAMBLE_DURATION:
            if self.timer % GAMBLE_CYCLE_EVERY == 0:
                self.cycle_key = random.choice(POWERUP_ORDER)
        elif not self._settled:
            self._settled  = True
            self.cycle_key = self.result_key

        if self.timer >= self.total:
            self.done = True
            callback, self.on_complete = self.on_complete, None
            if callback:
                callback(self.result_key)


# ─────────────────────────────────────────────────────────────────────────
# INVENTORY (slot penyimpanan + efek aktif)
# ─────────────────────────────────────────────────────────────────────────
class PowerUpInventory:
    """Mengelola satu slot power-up yang dipegang main_fish, animasi undian
    saat mendapatkannya, dan efek-efek aktif saat power-up dipakai (tombol E).

    Cara pakai di GameView:
        self.powerup_inventory = PowerUpInventory(self)

        # Saat kotak power-up dimakan main_fish (lihat power_up.py):
        self.powerup_inventory.start_gamble()   # hanya jalan kalau can_pickup()

        # Di on_update():
        self.powerup_inventory.update()
        self.powerup_inventory.apply_fast_boost()   # setelah player_fish.update()

        # Di on_key_press(): tombol E
        self.powerup_inventory.use_held()

        # Di on_draw() (gui camera):
        self.powerup_inventory.draw(self.window.width, self.window.height)

        # Cek efek aktif dari mana saja:
        self.powerup_inventory.is_freeze_active
        self.powerup_inventory.is_chomp_active
    """

    def __init__(self, game_view):
        self.game = game_view

        self.held        = None   # key power-up yang tersimpan, siap dipakai
        self.reveal_anim = None   # PowerUpRevealAnimation yang sedang berjalan

        # Timer efek aktif (frame tersisa) — properties is_xxx_active di
        # bawah dihitung LANGSUNG dari timer ini, jadi jangan di-assign
        # manual (mis. `self.is_fast_active = False`) — itu yang bikin
        # crash "property has no setter" sebelumnya.
        self.fast_timer       = 0
        self.freeze_timer     = 0
        self.invincible_timer = 0
        self.chomp_timer      = 0

        # ── Load SEMUA sfx SEKALI di sini (murni load, TIDAK diputar) ──
        self._gamble_sfx    = None
        self._gamble_player = None   # media player suara gambling yang SEDANG main
        try:
            self._gamble_sfx = arcade.load_sound(GAMBLE_SFX_PATH)
        except Exception as e:
            print(f"Gagal memuat sfx gambling: {e}")

        # SFX aktivasi per power-up, di-load sekali dan disimpan di dict —
        # supaya use_held() tinggal play, tidak load ulang tiap ditekan.
        self._powerup_sfx = {}
        for key, filename in POWERUP_SFX_FILES.items():
            path = os.path.join(POWERUP_SFX_DIR, filename)
            try:
                self._powerup_sfx[key] = arcade.load_sound(path)
            except Exception as e:
                print(f"Gagal memuat sfx power-up {key}: {e}")
                self._powerup_sfx[key] = None

    # ── PICKUP ───────────────────────────────────────────────────────────
    def can_pickup(self):
        """True kalau slot kosong & tidak sedang animasi undian — artinya
        kotak power-up baru boleh dimakan/dikonsumsi."""
        return self.reveal_anim is None and self.held is None

    def start_gamble(self):
        """Mulai animasi undian. Hasil final ditentukan SEKARANG (acak),
        animasi hanya menampilkan proses 'gambling' menuju hasil itu."""
        if not self.can_pickup():
            return
        result_key = random.choice(POWERUP_ORDER)
        self.reveal_anim = PowerUpRevealAnimation(
            result_key,
            on_complete=self._finish_gamble,
        )
        # SFX dimainkan SEKALI di sini, saat gambling dimulai.
        self._play_gamble_sfx()

    def _finish_gamble(self, key):
        self.held        = key
        self.reveal_anim = None

    def _play_gamble_sfx(self):
        if self._gamble_sfx is None:
            return

        # Hentikan dulu suara sebelumnya kalau (entah kenapa) masih main —
        # jaga-jaga supaya tidak ada 2 instance bunyi bersamaan.
        if self._gamble_player is not None:
            try:
                arcade.stop_sound(self._gamble_player)
            except Exception:
                pass
            self._gamble_player = None

        try:
            self._gamble_player = arcade.play_sound(self._gamble_sfx, volume=self._sfx_volume())
        except Exception as e:
            print(f"Gagal memutar sfx gambling: {e}")

    def _play_powerup_sfx(self, key):
        """Mainkan SEKALI SFX aktivasi untuk power-up tertentu (kalau ada)."""
        sfx = self._powerup_sfx.get(key)
        if sfx is None:
            return
        try:
            arcade.play_sound(sfx, volume=self._sfx_volume())
        except Exception as e:
            print(f"Gagal memutar sfx power-up {key}: {e}")

    def _sfx_volume(self):
        try:
            from setting import load_settings as _ls
            return _ls().get("sfx_volume", 0.6)
        except Exception:
            return 0.6

    # ── UPDATE ───────────────────────────────────────────────────────────
    def update(self):
        if self.reveal_anim is not None:
            self.reveal_anim.update()

        if self.fast_timer > 0:
            self.fast_timer -= 1
        if self.freeze_timer > 0:
            self.freeze_timer -= 1
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.chomp_timer > 0:
            self.chomp_timer -= 1

    def apply_fast_boost(self):
        """Panggil setiap frame SETELAH player_fish.update() dipanggil.
        Menambah dorongan ekstra sebanding kecepatan saat ini, sehingga
        main_fish terasa lebih cepat tanpa mengubah fisika dasarnya."""
        if self.fast_timer <= 0:
            return
        player = self.game.player_fish
        extra = FAST_SPEED_MULTIPLIER - 1.0
        player.x += player.speed_x * extra
        player.y += player.speed_y * extra

    # ── PROPERTIES EFEK AKTIF ────────────────────────────────────────────
    @property
    def is_fast_active(self):
        return self.fast_timer > 0

    @property
    def is_freeze_active(self):
        return self.freeze_timer > 0

    @property
    def is_invincible_active(self):
        return self.invincible_timer > 0

    @property
    def is_chomp_active(self):
        return self.chomp_timer > 0

    # ── PAKAI (tombol E) ─────────────────────────────────────────────────
    def use_held(self):
        if self.held is None:
            return

        key = self.held
        self.held = None

        # SFX aktivasi dimainkan SEKALI di sini untuk semua jenis power-up
        # (dict-nya sudah di-load sekali di __init__, jadi tinggal play).
        self._play_powerup_sfx(key)

        if key == "FAST":
            self.fast_timer = FAST_DURATION

        elif key == "FREEZE":
            self.freeze_timer = FREEZE_DURATION

        elif key == "LIVES":
            g = self.game
            if g.lives < g.MAX_LIVES:
                g.lives += 1

        elif key == "INVINCIBLE":
            self.invincible_timer = INVINCIBLE_DURATION
            # Manfaatkan kebal_timer yang sudah dipakai di seluruh sistem
            # tabrakan (check_collision_and_respawn & dangerous fish) agar
            # main_fish otomatis tidak bisa dimakan apa pun selama durasi ini.
            player = self.game.player_fish
            player.kebal_timer = max(player.kebal_timer, INVINCIBLE_DURATION)

        elif key == "CHOMP":
            self.chomp_timer = CHOMP_DURATION

    # ── DRAW ──────────────────────────────────────────────────────────────
    def draw(self, screen_width, screen_height):
        BAR_W, BAR_H = 190, 34
        BAR_X = screen_width / 2
        BAR_Y = 40

        if self.reveal_anim is not None:
            anim  = self.reveal_anim
            color = POWERUP_COLORS[anim.cycle_key]
            label = POWERUP_LABELS[anim.cycle_key]

            if anim._settled:
                # Hasil sudah didapat — bar berkedip/"glow" sebentar sebagai
                # penekanan, sebelum masuk ke tampilan tersimpan biasa.
                pulse   = 1.0 + 0.08 * math.sin(anim.timer * 0.6)
                bar_w   = BAR_W * pulse
                bar_h   = BAR_H * pulse
                border_color = color
                hint = f"GOT: {label}!"
            else:
                # Masih 'mengundi' — teks berganti-ganti, border ikut berkedip
                bar_w, bar_h = BAR_W, BAR_H
                flicker = (anim.timer // 3) % 2 == 0
                border_color = (235, 235, 235) if flicker else (110, 110, 110)
                hint = f"? {label} ?"

            arcade.draw_rect_filled(
                arcade.rect.XYWH(BAR_X, BAR_Y, bar_w, bar_h), (20, 20, 25, 220)
            )
            arcade.draw_rect_filled(
                arcade.rect.XYWH(BAR_X, BAR_Y, bar_w - 6, bar_h - 6), color
            )
            arcade.draw_rect_outline(
                arcade.rect.XYWH(BAR_X, BAR_Y, bar_w, bar_h), border_color, border_width=3
            )
            arcade.draw_text(
                hint, x=BAR_X, y=BAR_Y,
                color=arcade.color.WHITE, font_size=13, bold=True,
                anchor_x="center", anchor_y="center",
            )

        else:
            # ── Bar slot power-up dalam kondisi normal (kosong / tersimpan) ──
            arcade.draw_rect_filled(
                arcade.rect.XYWH(BAR_X, BAR_Y, BAR_W, BAR_H), (20, 20, 25, 200)
            )

            if self.held is not None:
                fill_color = POWERUP_COLORS[self.held]
                hint = f"{POWERUP_LABELS[self.held]}  [E]"
            else:
                fill_color = (45, 45, 50, 160)
                hint = ""

            arcade.draw_rect_filled(
                arcade.rect.XYWH(BAR_X, BAR_Y, BAR_W - 6, BAR_H - 6), fill_color
            )
            arcade.draw_rect_outline(
                arcade.rect.XYWH(BAR_X, BAR_Y, BAR_W, BAR_H), arcade.color.WHITE, border_width=2
            )

            if hint:
                arcade.draw_text(
                    hint, x=BAR_X, y=BAR_Y,
                    color=arcade.color.WHITE, font_size=13, bold=True,
                    anchor_x="center", anchor_y="center",
                )

        # ── Indikator efek aktif (di atas bar slot) ──
        active_labels = []
        if self.is_fast_active:
            active_labels.append(("FAST", self.fast_timer, POWERUP_COLORS["FAST"]))
        if self.is_freeze_active:
            active_labels.append(("FREEZE", self.freeze_timer, POWERUP_COLORS["FREEZE"]))
        if self.is_invincible_active:
            active_labels.append(("INVINCIBLE", self.invincible_timer, POWERUP_COLORS["INVINCIBLE"]))
        if self.is_chomp_active:
            active_labels.append(("CHOMP CHOMP", self.chomp_timer, POWERUP_COLORS["CHOMP"]))

        for i, (name, timer, color) in enumerate(active_labels):
            ay = BAR_Y + BAR_H / 2 + 20 + i * 20
            sisa = timer / 60
            arcade.draw_text(
                f"{name}: {sisa:.1f}s", x=BAR_X, y=ay,
                color=color, font_size=12, bold=True,
                anchor_x="center", anchor_y="center",
            )