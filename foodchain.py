# foodchain.py
#
# Sistem rantai makanan antar NPC:
#   hugefish   -> makan mediumfish dan smallfish
#   mediumfish -> makan smallfish
#
# PRINSIP UTAMA: ikan yang dimakan NPC TIDAK DIHAPUS — langsung di-respawn
# ke posisi baru yang jauh. Ini menjaga populasi tetap stabil tanpa perlu
# sistem replenish yang kompleks.
#
# Replenish tetap ada sebagai jaring pengaman kalau populasi entah kenapa
# turun (misalnya banyak dimakan player sekaligus).

import math
import random
from small_fish import smallfish
from medium_fish import mediumfish
from huge_fish import hugefish
from eat_fish import EatAnimation
from outside import SURFACE_MARGIN_FROM_TOP

# ── Populasi minimum (jaring pengaman) ──
MIN_SMALL  = 28
MIN_MEDIUM = 8
MIN_HUGE   = 3

# ── Radius berburu NPC ──
# Dibuat lebih kecil dari sebelumnya agar huge fish tidak terlalu agresif
# mengejar small fish (yang akibatnya membuat small fish cepat habis).
HUNT_RADIUS_HUGE   = 220   # huge lebih fokus ke medium
HUNT_RADIUS_MEDIUM = 160   # medium kejar small, tapi tidak terlalu jauh

# Huge fish lebih diutamakan memakan medium, bukan small
# Radius khusus huge->small lebih kecil supaya small fish lebih aman
HUNT_RADIUS_HUGE_VS_SMALL = 120

# ── Cooldown berburu per predator (frame) ──
# Setiap predator punya cooldown pribadi. Setelah makan, harus tunggu dulu
# sebelum bisa makan lagi. Ini mencegah satu predator menghabiskan semua
# mangsa dalam hitungan detik.
HUNT_COOLDOWN_HUGE   = 300   # ~5 detik @ 60fps
HUNT_COOLDOWN_MEDIUM = 240   # ~4 detik

# ── Jarak respawn mangsa setelah dimakan NPC ──
RESPAWN_MIN_DIST_FROM_PREDATOR = 600

# ── Jarak aman dari player saat auto-spawn ──
SPAWN_SAFE_FROM_PLAYER = 350


class FoodChain:
    def __init__(self, map_width, map_height):
        self.map_width  = map_width
        self.map_height = map_height

        # Cooldown hunt per objek predator: { id(predator): sisa_frame }
        self._hunt_cd = {}

        # Replenish timer (jaring pengaman)
        self.respawn_timer = 0
        self.RESPAWN_INTERVAL = 120   # cek tiap ~2 detik

    # ─────────────────────────────────────────────────────────────────
    # UPDATE UTAMA
    # ─────────────────────────────────────────────────────────────────
    def update(self, enemy_list, player, map_width, map_height, eat_animations):
        self._process_hunting(enemy_list, eat_animations, map_width, map_height)

        # Replenish (jaring pengaman)
        self.respawn_timer -= 1
        if self.respawn_timer <= 0:
            self.respawn_timer = self.RESPAWN_INTERVAL
            self._replenish_population(enemy_list, player, map_width, map_height)

        # Bersihkan cooldown untuk predator yang sudah tidak ada
        alive_ids = {id(f) for f in enemy_list}
        stale = [k for k in self._hunt_cd if k not in alive_ids]
        for k in stale:
            del self._hunt_cd[k]

    # ─────────────────────────────────────────────────────────────────
    # PROSES BERBURU
    # ─────────────────────────────────────────────────────────────────
    def _process_hunting(self, enemy_list, eat_animations, map_width, map_height):
        huge_list   = [f for f in enemy_list if f.__class__.__name__ == "hugefish"]
        medium_list = [f for f in enemy_list if f.__class__.__name__ in ("mediumfish", "speedmediumfish")]
        small_list  = [f for f in enemy_list if f.__class__.__name__ in ("smallfish", "jumpingsmallfish")
                       and not getattr(f, 'is_panik', False)]

        # ── Huge fish: utamakan medium, baru small (radius lebih kecil) ──
        for predator in huge_list:
            pid = id(predator)
            # Tick down cooldown
            if self._hunt_cd.get(pid, 0) > 0:
                self._hunt_cd[pid] -= 1
                continue

            # Cari mangsa: medium dulu, kalau tidak ada baru small (radius lebih kecil)
            prey = self._find_closest(predator, medium_list, HUNT_RADIUS_HUGE, [])
            radius_used = HUNT_RADIUS_HUGE
            if prey is None:
                prey = self._find_closest(predator, small_list, HUNT_RADIUS_HUGE_VS_SMALL, [])
                radius_used = HUNT_RADIUS_HUGE_VS_SMALL

            if prey is None:
                continue

            # Gerak menuju mangsa
            dx = prey.x - predator.x
            dy = prey.y - predator.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                predator.x += (dx / dist) * predator.speed * 1.3
                predator.y += (dy / dist) * predator.speed * 1.3

            # Makan kalau sudah cukup dekat
            if dist < 85:
                eat_animations.append(EatAnimation(prey, _fake_player(predator)))
                self._respawn_prey(prey, predator, map_width, map_height, enemy_list)
                self._hunt_cd[pid] = HUNT_COOLDOWN_HUGE

        # ── Medium fish: kejar small ──
        for predator in medium_list:
            pid = id(predator)
            if self._hunt_cd.get(pid, 0) > 0:
                self._hunt_cd[pid] -= 1
                continue

            prey = self._find_closest(predator, small_list, HUNT_RADIUS_MEDIUM, [])
            if prey is None:
                continue

            dx = prey.x - predator.x
            dy = prey.y - predator.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                predator.x += (dx / dist) * predator.speed * 1.2
                predator.y += (dy / dist) * predator.speed * 1.2

            if dist < 55:
                eat_animations.append(EatAnimation(prey, _fake_player(predator)))
                self._respawn_prey(prey, predator, map_width, map_height, enemy_list)
                self._hunt_cd[pid] = HUNT_COOLDOWN_MEDIUM

    def _find_closest(self, predator, prey_list, radius, skip_list):
        closest = None
        closest_dist = radius
        for prey in prey_list:
            if prey in skip_list:
                continue
            if getattr(prey, 'kebal_timer', 0) > 0:
                continue
            d = math.sqrt((predator.x - prey.x)**2 + (predator.y - prey.y)**2)
            if d < closest_dist:
                closest_dist = d
                closest = prey
        return closest

    def _respawn_prey(self, prey, predator, map_width, map_height, enemy_list):
        """Pindahkan mangsa ke posisi baru yang jauh dari predator.

        MANGSA TIDAK DIHAPUS — hanya dipindahkan. Posisi selalu di dalam
        area air (di bawah surface_y), tidak pernah di area udara.
        """
        margin = 80
        # Batas atas area air — ikan tidak boleh respawn di area udara
        water_max_y = map_height - SURFACE_MARGIN_FROM_TOP - margin

        for _ in range(60):
            nx = random.uniform(margin, map_width - margin)
            ny = random.uniform(margin, water_max_y)
            if math.sqrt((nx - predator.x)**2 + (ny - predator.y)**2) < RESPAWN_MIN_DIST_FROM_PREDATOR:
                continue
            too_close = any(
                math.sqrt((nx - f.x)**2 + (ny - f.y)**2) < 80
                for f in enemy_list if f is not prey
            )
            if not too_close:
                prey.x = nx
                prey.y = ny
                if hasattr(prey, 'target_x'):
                    prey.target_x = random.uniform(margin, map_width - margin)
                    prey.target_y = random.uniform(margin, water_max_y)
                return
        # Fallback
        for _ in range(30):
            nx = random.uniform(margin, map_width - margin)
            ny = random.uniform(margin, water_max_y)
            if math.sqrt((nx - predator.x)**2 + (ny - predator.y)**2) > 400:
                prey.x = nx
                prey.y = ny
                if hasattr(prey, 'target_x'):
                    prey.target_x = random.uniform(margin, map_width - margin)
                    prey.target_y = random.uniform(margin, water_max_y)
                return

    # ─────────────────────────────────────────────────────────────────
    # REPLENISH — jaring pengaman, spawn kalau populasi benar-benar turun
    # ─────────────────────────────────────────────────────────────────
    def _replenish_population(self, enemy_list, player, map_width, map_height):
        jumlah_small  = sum(1 for f in enemy_list if f.__class__.__name__ == "smallfish")
        jumlah_medium = sum(1 for f in enemy_list if f.__class__.__name__ == "mediumfish")
        jumlah_huge   = sum(1 for f in enemy_list if f.__class__.__name__ == "hugefish")

        # Spawn beberapa sekaligus kalau jauh di bawah minimum
        def spawn_beberapa(jumlah_sekarang, minimum, factory):
            kekurangan = minimum - jumlah_sekarang
            if kekurangan <= 0:
                return
            # Spawn paling banyak 3 per interval agar tidak burst
            untuk_spawn = min(kekurangan, 3)
            for _ in range(untuk_spawn):
                pos = self._cari_posisi_spawn(enemy_list, player, map_width, map_height)
                if pos:
                    enemy_list.append(factory(pos[0], pos[1]))

        spawn_beberapa(
            jumlah_small, MIN_SMALL,
            lambda x, y: self._buat_small(x, y, map_width, map_height)
        )
        spawn_beberapa(
            jumlah_medium, MIN_MEDIUM,
            lambda x, y: mediumfish(map_width, map_height, x, y)
        )
        spawn_beberapa(
            jumlah_huge, MIN_HUGE,
            lambda x, y: hugefish(map_width, map_height, x, y)
        )

    def _buat_small(self, x, y, map_width, map_height):
        ikan = smallfish(map_width, map_height, x, y)
        ikan.school_id = random.randint(0, 9)
        return ikan

    def _cari_posisi_spawn(self, enemy_list, player, map_width, map_height):
        margin = 100
        # Batas atas area air
        water_max_y = map_height - SURFACE_MARGIN_FROM_TOP - margin

        for _ in range(60):
            x = random.uniform(margin, map_width - margin)
            y = random.uniform(margin, water_max_y)
            if player and math.sqrt((x - player.x)**2 + (y - player.y)**2) < SPAWN_SAFE_FROM_PLAYER:
                continue
            too_close = any(
                math.sqrt((x - f.x)**2 + (y - f.y)**2) < 100
                for f in enemy_list
            )
            if not too_close:
                return (x, y)
        return (random.uniform(margin, map_width - margin),
                random.uniform(margin, water_max_y))


class _fake_player:
    """Objek dummy untuk EatAnimation — hanya butuh .x dan .y."""
    def __init__(self, predator):
        self.x = predator.x
        self.y = predator.y