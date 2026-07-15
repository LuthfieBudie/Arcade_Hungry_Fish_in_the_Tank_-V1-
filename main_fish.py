# main_fish.py
import arcade
import math
import os

import audio_registry
from Fish_Evolution import small_evo
from Fish_Evolution import medium_evo
from Fish_Evolution import huge_evo


class mainfish:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed_x = 0
        self.speed_y = 0

        self.score  = 0
        self.status = "SMALL"
        self.width  = 60
        self.height = 30

        self.total_points = 0

        self.last_dir_x = 1
        self.is_dashing = False

        # ── FLIP ANIMATION ──
        self.facing     = 1
        self.flip_frame = 0
        self.FLIP_TOTAL = 4

        # ── RESPAWN ANIMATION ──
        self.is_spawning    = False
        self.spawn_start_y  = 0
        self.spawn_target_y = 0
        self.spawn_progress = 0.0
        self.spawn_speed    = 0.035

        # ── INVINCIBILITY ──
        self.kebal_timer  = 0
        self.KEBAL_DURASI = 120
        self.blink_visible = True
        self.blink_timer   = 0





        self.DASH_MAX_CHARGES  = 3
        self.DASH_CHARGES      = 3       
        self.DASH_COOLDOWN_PER = 180     
        self.dash_cooldown     = 0       






        self.SUCK_BAR_MAX  = 120    # 2 detik hisap penuh @ 60fps
        self.SUCK_REGEN    = 0.4    # bar regen per frame (~5 detik regen penuh)
        self.suck_bar      = float(self.SUCK_BAR_MAX)
        self.is_sucking    = False





        self.suck_active_timer = self.SUCK_BAR_MAX
        self.SUCK_MAX_DURATION = self.SUCK_BAR_MAX
        self.suck_cooldown     = 0   # selalu 0, tidak dipakai

        # Kekuatan & jangkauan hisap
        self.SUCK_RANGE    = 280
        self.SUCK_CONE_DEG = 55
        self.suck_sound_player = None





    def draw(self):
        if self.kebal_timer > 0 and not self.blink_visible:
            return

        if self.flip_frame > 0:
            t = self.flip_frame / self.FLIP_TOTAL
            scale = (1.0 - t / 0.5) if t <= 0.5 else ((t - 0.5) / 0.5)
            draw_w = max(2, self.width * scale)
        else:
            draw_w = self.width

        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.x, self.y, draw_w, self.height),
            arcade.color.PURPLE
        )







    def _update_flip(self, new_dir):
        if new_dir != self.facing and self.flip_frame == 0:
            self.flip_frame = 1
        if self.flip_frame > 0:
            self.flip_frame += 1
            if self.flip_frame == self.FLIP_TOTAL // 2 + 1:
                self.facing = new_dir
            if self.flip_frame > self.FLIP_TOTAL:
                self.flip_frame = 0






    def trigger_respawn(self, target_x, target_y, map_height, eaten_by=None):
        self.x              = target_x
        self.spawn_start_y  = map_height + 100
        self.spawn_target_y = target_y
        self.y              = self.spawn_start_y
        self.speed_x        = 0
        self.speed_y        = 0
        self.is_spawning    = True
        self.spawn_progress = 0.0
        self.kebal_timer    = self.KEBAL_DURASI
        self.blink_visible  = True
        self.blink_timer    = 0
        # Batalkan ability aktif
        self._cancel_dash()
        self.is_sucking = False
        # Sama seperti dash, hentikan juga SUARA suck yang mungkin masih
        # jalan (bukan cuma flag is_sucking) — kalau tidak, sfx suck bisa
        # nyangkut terus walau player sudah di-respawn.
        if self.suck_sound_player is not None:
            try:
                arcade.stop_sound(self.suck_sound_player)
            except Exception:
                pass
            audio_registry.unregister(self.suck_sound_player)
            self.suck_sound_player = None

    def _cancel_dash(self):
        if self.is_dashing:
            self.is_dashing = False
            try:
                arcade.unschedule(self._perform_dash_step)
            except Exception:
                pass

    def _update_kebal_blink(self):
        """Update blink saja tanpa gerak — dipanggil saat di udara."""
        if self.kebal_timer > 0:
            self.kebal_timer -= 1
            self.blink_timer += 1
            if self.blink_timer >= 5:
                self.blink_timer = 0
                self.blink_visible = not self.blink_visible
        else:
            self.blink_visible = True







    def update(self, mouse_x, mouse_y, width, height):
        # Kebal & blink
        if self.kebal_timer > 0:
            self.kebal_timer -= 1
            self.blink_timer += 1
            if self.blink_timer >= 5:
                self.blink_timer = 0
                self.blink_visible = not self.blink_visible
        else:
            self.blink_visible = True

        # Animasi jatuh (spawn)
        if self.is_spawning:
            self.spawn_progress += self.spawn_speed
            if self.spawn_progress >= 1.0:
                self.spawn_progress = 1.0
                self.is_spawning    = False
            self.y = self.spawn_start_y + (
                self.spawn_target_y - self.spawn_start_y
            ) * _ease_out_bounce(self.spawn_progress)
            return

        # Gerak normal / dash
        if not self.is_dashing:
            dx   = mouse_x - self.x
            dy   = mouse_y - self.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 15:
                accel = 0.018 * min(dist / 300, 1.0)
                self.speed_x += dx * accel
                self.speed_y += dy * accel

            if abs(self.speed_x) > 0.3:
                nd = 1 if self.speed_x > 0 else -1
                self._update_flip(nd)
                self.last_dir_x = nd
            elif self.flip_frame > 0:
                self._update_flip(self.facing)

            self.speed_x *= 0.75
            self.speed_y *= 0.75
            mag = math.sqrt(self.speed_x**2 + self.speed_y**2)
            if mag > 8:
                self.speed_x = self.speed_x / mag * 8
                self.speed_y = self.speed_y / mag * 8

            self.x += self.speed_x
            self.y += self.speed_y
        else:
            dy = mouse_y - self.y
            self.speed_y += dy * 0.05
            self.y       += self.speed_y
            self.speed_y *= 0.65

        # Batas dinding
        bx, by = self.width / 2, self.height / 2
        if self.x < bx:         self.x = bx;         self.speed_x *= -0.5
        if self.x > width - bx: self.x = width - bx; self.speed_x *= -0.5
        if self.y < by:          self.y = by;          self.speed_y *= -0.5
        if self.y > height - by: self.y = height - by; self.speed_y *= -0.5






    def dash(self, main_window):
        """Gunakan 1 charge dash.

        Jika cooldown sedang berjalan (mengisi charge yang sudah terpakai):
          - Cooldown TIDAK di-reset dan TIDAK ditambah
          - Hanya stok DASH_CHARGES yang dikurangi 1
          - Cooldown tetap berjalan untuk mengembalikan charge berikutnya
        """
        if self.is_dashing or self.is_spawning:
            return 0
        if self.DASH_CHARGES <= 0:
            return 0

        self.DASH_CHARGES -= 1

        # Mulai cooldown hanya jika belum ada yang berjalan
        # (jika sudah ada cooldown, biarkan — tidak reset, tidak tambah)
        if self.dash_cooldown <= 0:
            self.dash_cooldown = self.DASH_COOLDOWN_PER

        self.is_dashing           = True
        total_distance            = 75 * self.last_dir_x
        self.dash_steps_remaining = 5
        self.dash_step_distance   = total_distance / 5

        try:
            _base = os.path.dirname(os.path.abspath(__file__))
            sfx_path = os.path.join(_base, "assets", "sfx", "abillities_sfx", "dash.mp3")
            dash_sfx = arcade.load_sound(sfx_path)
            try:
                from setting import load_settings as _ls
                _svol = _ls().get("sfx_volume", 0.6)
            except Exception:
                _svol = 0.6
            arcade.play_sound(dash_sfx, volume=_svol)
        except Exception as e:
            print(f"Gagal memutar SFX makan: {e}")

                    
        arcade.schedule(self._perform_dash_step, 1 / 60)
        return total_distance

    def _perform_dash_step(self, delta_time):
        self.x += self.dash_step_distance
        self.dash_steps_remaining -= 1
        if self.dash_steps_remaining <= 0:
            self.is_dashing = False
            self.speed_x    = 0
            arcade.unschedule(self._perform_dash_step)

                

    def update_dash_cooldown(self):
        """Tick cooldown tiap frame. Panggil dari game.py."""
        if self.dash_cooldown > 0 and self.DASH_CHARGES < self.DASH_MAX_CHARGES:
            self.dash_cooldown -= 1
            if self.dash_cooldown <= 0:
                self.DASH_CHARGES += 1
                # Jika masih ada charge yang hilang, mulai cooldown untuk berikutnya
                if self.DASH_CHARGES < self.DASH_MAX_CHARGES:
                    self.dash_cooldown = self.DASH_COOLDOWN_PER





    def start_suck(self):
        if self.is_spawning:
            return
        if self.suck_bar <= 0:
            return     # tunggu bar regen
        self.is_sucking = True

        if self.suck_sound_player is None:
            try:
                _base = os.path.dirname(os.path.abspath(__file__))
                sfx_path = os.path.join(_base, "assets", "sfx", "abillities_sfx", "suck.wav")
                suck_sfx = arcade.load_sound(sfx_path)
                try:
                    from setting import load_settings as _ls
                    _svol = _ls().get("sfx_volume", 0.6)
                except Exception:
                    _svol = 0.6
                self.suck_sound_player = arcade.play_sound(suck_sfx, volume=_svol, loop=True)
                audio_registry.register(self.suck_sound_player)
            except Exception as e:
                print(f"Gagal memutar SFX makan: {e}")

    def stop_suck(self):
        self.is_sucking = False

        # BUG LAMA: kondisi ini sebelumnya "is None" (kebalik), jadi
        # stop_sound cuma pernah dipanggil saat player-nya sudah None
        # (tidak pernah benar-benar menghentikan suara yang sedang jalan).
        if self.suck_sound_player is not None:
            try:
                arcade.stop_sound(self.suck_sound_player)
            except Exception:
                pass
            audio_registry.unregister(self.suck_sound_player)
            self.suck_sound_player = None

    def update_suck(self, enemy_list, eat_animations, map_width, map_height):
        """Kelola bar suck dan tarik ikan. Panggil tiap frame dari game.py."""
        if not self.is_sucking or self.is_spawning:
            # Regen bar saat tidak hisap
            self.suck_bar = min(self.SUCK_BAR_MAX, self.suck_bar + self.SUCK_REGEN)
            # Sync alias HUD
            self.suck_active_timer = int(self.suck_bar)
            self.suck_cooldown     = 0

            if self.suck_sound_player is not None:
                try: arcade.stop_sound(self.suck_sound_player)
                except Exception: pass
                audio_registry.unregister(self.suck_sound_player)
                self.suck_sound_player = None
            return []

        # Hisap aktif: kurangi bar
        self.suck_bar -= 1
        self.suck_active_timer = int(self.suck_bar)

        if self.suck_bar <= 0:
            self.suck_bar   = 0
            self.is_sucking = False
            if self.suck_sound_player is not None:
                try: arcade.stop_sound(self.suck_sound_player)
                except Exception: pass
                audio_registry.unregister(self.suck_sound_player)
                self.suck_sound_player = None
            return []
        
        

        # Tarik ikan dalam corong
        mouth_x = self.x + self.facing * (self.width / 2)
        mouth_y = self.y
        suck_dir_x = float(self.facing)
        cos_limit  = math.cos(math.radians(self.SUCK_CONE_DEG))

        PULL = {"small": 18.0, "medium": 9.0, "huge": 4.0}
        mul  = {"SMALL": 1.0, "MEDIUM": 1.3, "HUGE": 1.6}.get(self.status, 1.0)

        dimakan = []
        for fish in enemy_list:
            if fish in dimakan:
                continue
            # Kebal (PanikFish baru lahir kebal 1 detik — setelah itu bisa dihisap)
            if getattr(fish, 'kebal_timer', 0) > 0:
                continue

            nama = fish.__class__.__name__
            # PanikFish (ikan dari seaweed) & jumpingsmallfish diperlakukan seperti smallfish
            if   nama in ("smallfish", "PanikFish", "jumpingsmallfish"): spd = PULL["small"]  * mul
            elif nama in ("mediumfish", "speedmediumfish"):              spd = PULL["medium"] * mul
            elif nama == "hugefish":                                     spd = PULL["huge"]   * mul
            else: continue

            fx   = fish.x - mouth_x
            fy   = fish.y - mouth_y
            dist = math.sqrt(fx**2 + fy**2)

            if dist < 1:
                from eat_fish import EatAnimation
                eat_animations.append(EatAnimation(fish, self))
                dimakan.append(fish)
                continue

            if dist > self.SUCK_RANGE:
                continue

            dot = (fx / dist) * suck_dir_x  # suck_dir_y = 0
            if dot < cos_limit:
                continue

            step = min(spd, dist)
            fish.x -= (fx / dist) * step
            fish.y -= (fy / dist) * step

            if math.sqrt((fish.x - mouth_x)**2 + (fish.y - mouth_y)**2) < 18:
                from eat_fish import EatAnimation
                eat_animations.append(EatAnimation(fish, self))
                dimakan.append(fish)

        return dimakan

    def draw_suck_cone(self):
        if not self.is_sucking or self.is_spawning:
            return
        mouth_x = self.x + self.facing * (self.width / 2)
        mouth_y = self.y
        CYCLE   = 30
        phase   = int(self.SUCK_BAR_MAX - self.suck_bar) % CYCLE

        for deg in [0, 25, -25]:
            for i in range(3):
                t         = ((phase + i * (CYCLE // 3)) % CYCLE) / float(CYCLE)
                dist_efek = self.SUCK_RANGE * (1.0 - t)
                rad       = math.radians(deg)
                px        = mouth_x + self.facing * math.cos(rad) * dist_efek
                py        = mouth_y + math.sin(rad) * dist_efek
                size      = max(3, int(10 * (1.0 - t)))
                alpha     = max(40, int(200 * (1.0 - t * 0.7)))
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(px, py, size, size),
                    (120, 210, 255, alpha)
                )

    def check_evolution(self):
        if   self.status == "SMALL":  small_evo.check_small_evolution(self)
        elif self.status == "MEDIUM": medium_evo.check_medium_evolution(self)
        elif self.status == "HUGE":   huge_evo.check_huge_evolution(self)


def _ease_out_bounce(t):
    n1, d1 = 7.5625, 2.75
    if   t < 1 / d1:       return n1 * t * t
    elif t < 2 / d1:       t -= 1.5 / d1;  return n1 * t * t + 0.75
    elif t < 2.5 / d1:     t -= 2.25 / d1; return n1 * t * t + 0.9375
    else:                   t -= 2.625 / d1; return n1 * t * t + 0.984375