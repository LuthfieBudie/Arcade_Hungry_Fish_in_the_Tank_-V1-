# small_fish.py
import arcade
import random
import math
import os
from outside import SURFACE_MARGIN_FROM_TOP

# ── SFX untuk jumpingsmallfish (lompat/mendarat) ──
# Di-cache di level MODULE (bukan per-instance) karena bisa ada BANYAK
# jumpingsmallfish sekaligus (schooling) — supaya file sfx cuma di-load
# SEKALI walau ikannya banyak, bukan dobel-dobel tiap ikan.
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_jump_sfx_cache   = None
_splash_sfx_cache = None


def _get_jump_sfx():
    global _jump_sfx_cache
    if _jump_sfx_cache is None:
        try:
            path = os.path.join(_BASE_DIR, "assets", "sfx", "jump_sfx", "jump.mp3")
            _jump_sfx_cache = arcade.load_sound(path)
        except Exception as e:
            print(f"Gagal memuat sfx jump (jumpingsmallfish): {e}")
    return _jump_sfx_cache


def _get_splash_sfx():
    global _splash_sfx_cache
    if _splash_sfx_cache is None:
        try:
            path = os.path.join(_BASE_DIR, "assets", "sfx", "jump_sfx", "splash.mp3")
            _splash_sfx_cache = arcade.load_sound(path)
        except Exception as e:
            print(f"Gagal memuat sfx splash (jumpingsmallfish): {e}")
    return _splash_sfx_cache


# ── Jarak dengar untuk sfx lompat/splash jumpingsmallfish ──
# Di bawah radius ini, sfx full volume. Di antara FULL dan HEAR, volume
# meredup linear. Di luar HEAR radius sama sekali, sfx tidak dimainkan
# (supaya ikan yang jauh di luar kamera tidak kedengaran lompatannya).
JUMP_SFX_FULL_VOLUME_RADIUS = 220
JUMP_SFX_HEAR_RADIUS        = 700


def _distance_volume_mult(fish_x, fish_y, player):
    """Hitung faktor volume (0.0 - 1.0) berdasar jarak fish ke player,
    dipakai supaya sfx lompat/splash jumpingsmallfish yang jauh dari
    kamera tidak kedengaran, dan yang dekat kedengaran penuh."""
    if player is None:
        return 1.0
    d = math.sqrt((fish_x - player.x) ** 2 + (fish_y - player.y) ** 2)
    if d <= JUMP_SFX_FULL_VOLUME_RADIUS:
        return 1.0
    if d >= JUMP_SFX_HEAR_RADIUS:
        return 0.0
    t = (d - JUMP_SFX_FULL_VOLUME_RADIUS) / (JUMP_SFX_HEAR_RADIUS - JUMP_SFX_FULL_VOLUME_RADIUS)
    return max(0.0, 1.0 - t)


def _play_sfx(sfx, volume_mult=1.0):
    if sfx is None or volume_mult <= 0:
        return
    try:
        from setting import load_settings as _ls
        volume = _ls().get("sfx_volume", 0.6)
    except Exception:
        volume = 0.6
    try:
        arcade.play_sound(sfx, volume=volume * volume_mult)
    except Exception as e:
        print(f"Gagal memutar sfx: {e}")

class smallfish:
    def __init__(self, width, height, x, y):
        self.screen_width = width
        self.screen_height = height
        self.water_max_y = height - SURFACE_MARGIN_FROM_TOP - 50
        self.x = x
        self.y = y
        self.speed = random.uniform(1.2, 2.0)

        # Target bergerak
        self.target_x = random.randint(50, self.screen_width - 50)
        self.target_y = random.randint(50, max(100, int(self.water_max_y)))

        # Waktu ganti arah acak (biar terasa hidup)
        self.wander_timer = random.uniform(60, 150)

        # Fleeing
        self.flee_radius = 180  # jarak mulai lari dari player/huge
        self.is_fleeing = False

        # ── SISTEM SCHOOLING (berkelompok) ──
        # school_id = None  -> ikan ini SENDIRIAN (solitary), berenang dengan
        #                       rute sendiri, tidak tertarik ke ikan kecil lain.
        # school_id = angka -> ikan ini anggota satu KELOMPOK. Semua ikan yang
        #                       punya school_id sama akan saling mendekat
        #                       (cohesion) sehingga terlihat berenang bersama.
        # Nilai ini biasanya di-set dari luar (lihat generate_fish di bawah,
        # atau logika spawn di main.py), default-nya None (sendirian).
        self.school_id = None

    def draw(self):
        body = arcade.rect.XYWH(self.x, self.y, 50, 25)
        arcade.draw_rect_filled(body, arcade.color.YELLOW)

    def update(self, player=None, huge_list=None, all_small=None):
        threat_x, threat_y = None, None
        closest_dist = self.flee_radius

        # Cek ancaman: player dan huge fish
        threats = []
        if player:
            threats.append((player.x, player.y))
        if huge_list:
            for h in huge_list:
                threats.append((h.x, h.y))

        for tx, ty in threats:
            d = math.sqrt((self.x - tx)**2 + (self.y - ty)**2)
            if d < closest_dist:
                closest_dist = d
                threat_x, threat_y = tx, ty

        if threat_x is not None:
            # Lari menjauh dari ancaman
            self.is_fleeing = True
            flee_dx = self.x - threat_x
            flee_dy = self.y - threat_y
            dist = math.sqrt(flee_dx**2 + flee_dy**2)
            if dist > 0:
                flee_speed = self.speed * 2.2
                self.x += (flee_dx / dist) * flee_speed
                # Klem Y langsung setelah flee agar tidak menembus batas air
                self.y += (flee_dy / dist) * flee_speed
                if self.y > self.water_max_y:
                    self.y = self.water_max_y
        else:
            self.is_fleeing = False
            # Wandering dengan ganti arah berkala
            self.wander_timer -= 1
            if self.wander_timer <= 0:
                self.target_x = random.randint(50, self.screen_width - 50)
                self.target_y = random.randint(50, max(100, int(self.water_max_y)))
                self.wander_timer = random.uniform(80, 200)

            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist < 10:
                self.target_x = random.randint(50, self.screen_width - 50)
                self.target_y = random.randint(50, max(100, int(self.water_max_y)))
            else:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed

            # ── BERGEROMBOL HANYA DENGAN ANGGOTA KELOMPOK YANG SAMA ──
            # Kalau school_id ikan ini None (sendirian), bagian ini dilewati
            # sepenuhnya sehingga ikan benar-benar berenang sendiri tanpa
            # tertarik oleh ikan kecil lain di sekitarnya.
            if all_small and self.school_id is not None:
                avg_x, avg_y = 0, 0
                nearby = 0
                for other in all_small:
                    if other is self:
                        continue
                    # Hanya hitung ikan lain yang satu kelompok (school_id sama)
                    if other.school_id != self.school_id:
                        continue
                    d = math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
                    if d < 150:
                        avg_x += other.x
                        avg_y += other.y
                        nearby += 1
                if nearby > 0:
                    avg_x /= nearby
                    avg_y /= nearby
                    # Tarikan ke arah pusat kelompok (lebih kuat dari sebelumnya
                    # supaya kelompok benar-benar terlihat menyatu saat berenang)
                    self.x += (avg_x - self.x) * 0.03
                    self.y += (avg_y - self.y) * 0.03

        # Batas layar — hard clamp, termasuk paksa balik jika sudah melewati batas air
        self.x = max(25, min(self.x, self.screen_width - 25))
        self.y = max(25, min(self.y, self.water_max_y))
        # Safety: jika entah bagaimana sudah di atas batas air, paksa turun
        if self.y > self.water_max_y:
            self.y = self.water_max_y
            if hasattr(self, 'speed_y') and self.speed_y > 0:
                self.speed_y = 0

    def generate_fish(quantity, width, height, min_distance):
        """Membuat sejumlah ikan kecil dengan campuran:
        - sekitar 60% dikelompokkan menjadi grup kecil (3-5 ekor) yang
          spawn berdekatan dan diberi school_id yang sama (berenang bareng)
        - sisanya dibuat sendirian (school_id = None)

        Catatan: kalau main.py punya logika spawn sendiri (grid spread),
        fungsi ini tetap disediakan sebagai cara alternatif/standalone
        untuk membuat banyak ikan kecil sekaligus, misalnya untuk testing.
        """
        fishes = []
        sisa = quantity
        next_school_id = 0
        target_grouped = int(quantity * 0.6)
        sudah_grouped = 0

        while sisa > 0:
            if sudah_grouped < target_grouped:
                ukuran_grup = min(random.randint(3, 5), sisa)
                school_id = next_school_id
                next_school_id += 1
            else:
                ukuran_grup = 1
                school_id = None

            # Cari titik pusat untuk grup/ikan ini
            pusat_x, pusat_y = None, None
            attempts = 0
            while pusat_x is None and attempts < 100:
                kandidat_x = random.randint(60, width - 60)
                kandidat_y = random.randint(60, height - 60)
                too_close = any(
                    math.sqrt((kandidat_x - f.x)**2 + (kandidat_y - f.y)**2) < min_distance
                    for f in fishes
                )
                if not too_close:
                    pusat_x, pusat_y = kandidat_x, kandidat_y
                attempts += 1
            if pusat_x is None:
                pusat_x = random.randint(60, width - 60)
                pusat_y = random.randint(60, height - 60)

            for _ in range(ukuran_grup):
                offset_x = random.randint(-35, 35)
                offset_y = random.randint(-35, 35)
                fx = max(25, min(pusat_x + offset_x, width - 25))
                fy = max(25, min(pusat_y + offset_y, height - 25))
                fish = smallfish(width, height, fx, fy)
                fish.school_id = school_id
                fishes.append(fish)

            if school_id is not None:
                sudah_grouped += ukuran_grup
            sisa -= ukuran_grup

        return fishes


# ═════════════════════════════════════════════════════════════════════════
# JUMPING SMALL FISH — varian ikan kecil yang hidup berkelompok (schooling)
# sama seperti smallfish, TAPI bisa melompat ke udara (outside) secara
# berkala dan memakan bugs saat sedang melompat. Warna kotak berbeda (cyan)
# supaya gampang dibedakan dari smallfish biasa (kuning) walau ukurannya
# tetap sama kategori "small" (50x25).
# ═════════════════════════════════════════════════════════════════════════
class jumpingsmallfish:
    def __init__(self, width, height, x, y):
        self.screen_width = width
        self.screen_height = height
        self.surface_y = height - SURFACE_MARGIN_FROM_TOP
        self.water_max_y = self.surface_y - 50
        self.x = x
        self.y = y
        self.speed = random.uniform(1.3, 2.1)

        # Target bergerak (sama seperti smallfish)
        self.target_x = random.randint(50, self.screen_width - 50)
        self.target_y = random.randint(50, max(100, int(self.water_max_y)))
        self.wander_timer = random.uniform(60, 150)

        # Fleeing (sama seperti smallfish)
        self.flee_radius = 180
        self.is_fleeing = False

        # ── SISTEM SCHOOLING ── sama seperti smallfish, None = sendirian.
        # Hanya bergerombol dengan sesama jumpingsmallfish yang school_id-nya sama.
        self.school_id = None

        # ── LOMPAT KE UDARA ──
        self.is_jumping    = False
        self.jump_progress = 0.0
        self.jump_speed    = 0.045          # kecepatan animasi lompat
        self.jump_cooldown = random.uniform(90, 240)
        self.JUMP_HEIGHT   = random.uniform(90, 160)
        self._jump_start_x = 0.0
        self._jump_start_y = 0.0
        self._jump_dir_x   = 1
        self._jump_horiz   = 0.0
        # Saat cooldown habis, ikan akan berenang naik dulu ke dekat
        # permukaan sebelum benar-benar melompat (biar tidak nunggu
        # kebetulan lewat situ pas wandering biasa).
        self._menuju_permukaan = False

        # Placeholder aman agar kompatibel dengan kode lain yang mengecek
        # kebal_timer (mis. saat dihisap player / dimakan predator lain)
        self.kebal_timer = 0

    def draw(self):
        body = arcade.rect.XYWH(self.x, self.y, 50, 25)
        arcade.draw_rect_filled(body, (0, 200, 180))     # cyan — beda dari smallfish kuning

    # ── LOMPAT ──
    def _mulai_lompat(self, player=None):
        self.is_jumping    = True
        self.jump_progress = 0.0
        self._jump_start_x = self.x
        self._jump_start_y = self.y

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        self._jump_dir_x = (dx / dist) if dist > 0 else random.choice([-1, 1])
        self._jump_horiz = random.uniform(60, 130)

        # SFX (1): lompat keluar air — persis di titik mulai lompat.
        # Volume diskalakan berdasar jarak ke player supaya ikan yang jauh
        # dari kamera tidak kedengaran lompatannya.
        mult = _distance_volume_mult(self.x, self.y, player)
        _play_sfx(_get_jump_sfx(), mult)

    def _update_lompat(self, bugs, eat_animations, player=None):
        self.jump_progress += self.jump_speed
        t = min(1.0, self.jump_progress)

        # Gerak horizontal linear searah tujuan sebelumnya
        self.x = self._jump_start_x + self._jump_dir_x * self._jump_horiz * t
        # Gerak vertikal berbentuk parabola: naik ke JUMP_HEIGHT lalu turun balik
        peak_y = self.surface_y + self.JUMP_HEIGHT
        self.y = self._jump_start_y + (peak_y - self._jump_start_y) * 4 * t * (1 - t)

        # Coba makan bugs selama benar-benar berada di atas permukaan air
        if bugs and self.y > self.surface_y:
            self._coba_makan_bug(bugs, eat_animations)

        if self.jump_progress >= 1.0:
            self.is_jumping    = False
            self.jump_progress = 0.0
            self.jump_cooldown = random.uniform(150, 320)
            self.y = min(self.y, self.water_max_y)
            self.target_x = random.randint(50, self.screen_width - 50)
            self.target_y = random.randint(50, max(100, int(self.water_max_y)))

            # SFX (2): jatuh/mendarat kembali ke air — persis di titik lompat
            # selesai. Sama seperti sfx lompat, volume diskalakan berdasar
            # jarak ke player (kalau jauh dari kamera, tidak kedengaran).
            mult = _distance_volume_mult(self.x, self.y, player)
            _play_sfx(_get_splash_sfx(), mult)

    def _coba_makan_bug(self, bugs, eat_animations):
        EAT_RADIUS = 32
        for bug in bugs:
            if getattr(bug, 'eaten', False):
                continue
            d = math.sqrt((self.x - bug.x) ** 2 + (self.y - bug.y) ** 2)
            if d < EAT_RADIUS:
                bug.eaten = True
                if eat_animations is not None:
                    from eat_fish import EatAnimation
                    eat_animations.append(EatAnimation(bug, self))
                break  # satu bug per frame biar tidak terlalu rakus

    def update(self, player=None, huge_list=None, all_small=None,
               bugs=None, eat_animations=None):
        # Kalau sedang melompat, jalankan animasi lompat & jangan lakukan
        # gerakan renang/flee biasa dulu.
        if self.is_jumping:
            self._update_lompat(bugs, eat_animations, player)
            self.x = max(25, min(self.x, self.screen_width - 25))
            return

        # Waktunya lompat sudah tiba: arahkan dulu berenang naik ke dekat
        # permukaan air, baru melompat begitu benar-benar sampai di sana.
        # (Kalau cuma menunggu kebetulan lewat situ, jarang kejadian.)
        if self.jump_cooldown <= 0:
            if not self._menuju_permukaan:
                self._menuju_permukaan = True
                self.target_x = random.randint(50, self.screen_width - 50)
                self.target_y = max(50, self.water_max_y - random.uniform(0, 25))
            if self.y >= self.water_max_y - 40:
                self._menuju_permukaan = False
                self._mulai_lompat(player)
                return
        else:
            self.jump_cooldown -= 1

        threat_x, threat_y = None, None
        closest_dist = self.flee_radius

        threats = []
        if player:
            threats.append((player.x, player.y))
        if huge_list:
            for h in huge_list:
                threats.append((h.x, h.y))

        for tx, ty in threats:
            d = math.sqrt((self.x - tx) ** 2 + (self.y - ty) ** 2)
            if d < closest_dist:
                closest_dist = d
                threat_x, threat_y = tx, ty

        if threat_x is not None:
            self.is_fleeing = True
            flee_dx = self.x - threat_x
            flee_dy = self.y - threat_y
            dist = math.sqrt(flee_dx**2 + flee_dy**2)
            if dist > 0:
                flee_speed = self.speed * 2.2
                self.x += (flee_dx / dist) * flee_speed
                self.y += (flee_dy / dist) * flee_speed
                if self.y > self.water_max_y:
                    self.y = self.water_max_y
        else:
            self.is_fleeing = False

            # Kalau lagi menuju permukaan untuk lompat, jangan ganti target
            # lewat wander biasa — biarkan dia benar-benar sampai dulu.
            if not self._menuju_permukaan:
                self.wander_timer -= 1
                if self.wander_timer <= 0:
                    self.target_x = random.randint(50, self.screen_width - 50)
                    self.target_y = random.randint(50, max(100, int(self.water_max_y)))
                    self.wander_timer = random.uniform(80, 200)

            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist < 10:
                if not self._menuju_permukaan:
                    self.target_x = random.randint(50, self.screen_width - 50)
                    self.target_y = random.randint(50, max(100, int(self.water_max_y)))
            else:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed

            # ── BERGEROMBOL HANYA DENGAN SESAMA jumpingsmallfish ──
            if all_small and self.school_id is not None and not self._menuju_permukaan:
                avg_x, avg_y = 0, 0
                nearby = 0
                for other in all_small:
                    if other is self:
                        continue
                    if other.school_id != self.school_id:
                        continue
                    d = math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
                    if d < 150:
                        avg_x += other.x
                        avg_y += other.y
                        nearby += 1
                if nearby > 0:
                    avg_x /= nearby
                    avg_y /= nearby
                    self.x += (avg_x - self.x) * 0.03
                    self.y += (avg_y - self.y) * 0.03

        self.x = max(25, min(self.x, self.screen_width - 25))
        self.y = max(25, min(self.y, self.water_max_y))

    @staticmethod
    def generate_fish(quantity, width, height, min_distance):
        """Sama seperti smallfish.generate_fish: sebagian dikelompokkan jadi
        grup schooling kecil (3-5 ekor), sisanya sendirian."""
        fishes = []
        sisa = quantity
        next_school_id = 0
        target_grouped = int(quantity * 0.6)
        sudah_grouped = 0

        while sisa > 0:
            if sudah_grouped < target_grouped:
                ukuran_grup = min(random.randint(3, 5), sisa)
                school_id = next_school_id
                next_school_id += 1
            else:
                ukuran_grup = 1
                school_id = None

            pusat_x, pusat_y = None, None
            attempts = 0
            while pusat_x is None and attempts < 100:
                kandidat_x = random.randint(60, width - 60)
                kandidat_y = random.randint(60, height - 60)
                too_close = any(
                    math.sqrt((kandidat_x - f.x) ** 2 + (kandidat_y - f.y) ** 2) < min_distance
                    for f in fishes
                )
                if not too_close:
                    pusat_x, pusat_y = kandidat_x, kandidat_y
                attempts += 1
            if pusat_x is None:
                pusat_x = random.randint(60, width - 60)
                pusat_y = random.randint(60, height - 60)

            for _ in range(ukuran_grup):
                offset_x = random.randint(-35, 35)
                offset_y = random.randint(-35, 35)
                fx = max(25, min(pusat_x + offset_x, width - 25))
                fy = max(25, min(pusat_y + offset_y, height - 25))
                fish = jumpingsmallfish(width, height, fx, fy)
                fish.school_id = school_id
                fishes.append(fish)

            if school_id is not None:
                sudah_grouped += ukuran_grup
            sisa -= ukuran_grup

        return fishes


# ═════════════════════════════════════════════════════════════════════════
# SPEED MEDIUM FISH — varian mediumfish yang jauh lebih cepat dari ikan
# lain (small, medium, huge). Kalau player masih SMALL dan berada cukup
# dekat, ikan ini akan MENGEJAR untuk memakan player. Tapi begitu player
# sudah jadi MEDIUM (atau lebih besar), ikan ini justru KABUR menjauh.
# Bentuk & ukuran tetap kotak kategori "medium" (90x45) seperti mediumfish,
# hanya warnanya berbeda (magenta) agar mudah dibedakan.
# ═════════════════════════════════════════════════════════════════════════
class speedmediumfish:
    def __init__(self, width, height, x, y):
        self.screen_width = width
        self.screen_height = height
        self.water_max_y = height - SURFACE_MARGIN_FROM_TOP - 50
        self.x = x
        self.y = y

        # Jauh lebih cepat dari smallfish (1.2-2.0), mediumfish (1.0-1.6),
        # dan hugefish (0.7-1.1)
        self.speed = random.uniform(2.5, 3.3)

        self.target_x = random.randint(50, self.screen_width - 50)
        self.target_y = random.randint(50, max(100, int(self.water_max_y)))
        self.wander_timer = random.uniform(80, 180)

        self.flee_radius  = 240   # kabur dari huge fish & player MEDIUM+
        self.chase_radius = 280   # kejar player selama player masih SMALL

        self.is_chasing = False
        self.is_fleeing = False

    def draw(self):
        body = arcade.rect.XYWH(self.x, self.y, 90, 45)
        arcade.draw_rect_filled(body, (210, 30, 140))    # magenta — beda dari mediumfish oranye

    def update(self, player=None, huge_list=None):
        # ── PRIORITAS 1: kejar player selama masih berstatus SMALL ──
        if player and player.status == "SMALL":
            d_player = math.sqrt((self.x - player.x) ** 2 + (self.y - player.y) ** 2)
            if d_player < self.chase_radius:
                self.is_chasing = True
                self.is_fleeing = False
                dx = player.x - self.x
                dy = player.y - self.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    chase_speed = self.speed * 1.15
                    self.x += (dx / dist) * chase_speed
                    self.y += (dy / dist) * chase_speed
                self.x = max(45, min(self.x, self.screen_width - 45))
                self.y = max(25, min(self.y, self.water_max_y))
                return
        self.is_chasing = False

        # ── PRIORITAS 2: kabur dari ancaman (huge fish & player MEDIUM+) ──
        threat_x, threat_y = None, None
        closest_dist = self.flee_radius

        threats = []
        if huge_list:
            for h in huge_list:
                threats.append((h.x, h.y))
        if player and player.status != "SMALL":
            threats.append((player.x, player.y))

        for tx, ty in threats:
            d = math.sqrt((self.x - tx) ** 2 + (self.y - ty) ** 2)
            if d < closest_dist:
                closest_dist = d
                threat_x, threat_y = tx, ty

        if threat_x is not None:
            self.is_fleeing = True
            flee_dx = self.x - threat_x
            flee_dy = self.y - threat_y
            dist = math.sqrt(flee_dx**2 + flee_dy**2)
            if dist > 0:
                flee_speed = self.speed * 1.8
                self.x += (flee_dx / dist) * flee_speed
                self.y += (flee_dy / dist) * flee_speed
        else:
            self.is_fleeing = False
            self.wander_timer -= 1
            if self.wander_timer <= 0:
                self.target_x = random.randint(50, self.screen_width - 50)
                self.target_y = random.randint(50, max(100, int(self.water_max_y)))
                self.wander_timer = random.uniform(100, 220)

            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist < 10:
                self.target_x = random.randint(50, self.screen_width - 50)
                self.target_y = random.randint(50, max(100, int(self.water_max_y)))
            else:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed

        self.x = max(45, min(self.x, self.screen_width - 45))
        self.y = max(25, min(self.y, self.water_max_y))

    @staticmethod
    def generate_fish(quantity, width, height, min_distance):
        fishes = []
        for _ in range(quantity):
            valid_position = False
            attempts = 0
            while not valid_position and attempts < 100:
                kandidat_x = random.randint(45, width - 45)
                kandidat_y = random.randint(45, height - 45)
                too_close = any(
                    math.sqrt((kandidat_x - f.x) ** 2 + (kandidat_y - f.y) ** 2) < min_distance
                    for f in fishes
                )
                if not too_close:
                    fishes.append(speedmediumfish(width, height, kandidat_x, kandidat_y))
                    valid_position = True
                attempts += 1
        return fishes