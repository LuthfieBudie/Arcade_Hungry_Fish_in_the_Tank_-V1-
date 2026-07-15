import arcade
import random
import math
import os

import audio_registry


class DangerousFishWarning:
    def __init__(self, direction, screen_width, screen_height, duration=90):
        self.direction = direction
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.timer = duration
        self.max_timer = duration

        self.blink_timer = 0
        self.visible = True

        self.size = 45

        self.x, self.y = self._hitung_posisi()




    def _hitung_posisi(self):
        margin = 45
        w, h = self.screen_width, self.screen_height





        posisi_per_arah = {
            "right":        (w - margin, h / 2),
            "left":         (margin, h / 2),
            "top":          (w / 2, h - margin),
            "bottom":       (w / 2, margin),
            "top_right":    (w - margin, h - margin),
            "top_left":     (margin, h - margin),
            "bottom_right": (w - margin, margin),
            "bottom_left":  (margin, margin),
        }
        return posisi_per_arah.get(self.direction, (w / 2, h / 2))




    def update(self):
        self.timer -= 1

        self.blink_timer += 1
        kecepatan_kedip = max(3, int(self.timer / 6))
        if self.blink_timer >= kecepatan_kedip:
            self.blink_timer = 0
            self.visible = not self.visible





    def is_done(self):
        return self.timer <= 0
    


    def draw(self):
        if not self.visible:
            return
        rect = arcade.rect.XYWH(self.x, self.y, self.size, self.size)
        arcade.draw_rect_filled(rect, arcade.color.RED)
        arcade.draw_rect_outline(rect, arcade.color.WHITE, border_width=3)






class dangerousfish:
    def __init__(self, start_x, start_y, waypoints, speed=3.5, patrol=False):
        """
        patrol=False (default): perilaku klasik — masuk dari tepi map,
            melintas mengikuti waypoints, lalu keluar map & dihapus
            (dipakai untuk entrance dramatis dengan warning).
        patrol=True: ikan sudah berada di dalam air sejak awal dan terus
            berenang berkeliling di dalam batas air (tidak pernah keluar
            map / dihapus). Dipakai untuk dangerous fish tambahan yang
            muncul seiring waktu (difficulty scaling) tanpa tanda peringatan.
        """

        self.x = start_x
        self.y = start_y

        self.width = 220
        self.height = 90

        self.speed = speed
        self.waypoints = list(waypoints)
        self.current_wp = 0

        self.is_dangerous = True
        self.markedfor_removal = False
        self.patrol = patrol

        self._update_direction()
        self.eat_cooldown = 0

    def _pick_random_patrol_waypoint(self, map_width, map_height):
        """Pilih titik acak baru di dalam air untuk mode patrol (loop terus)."""
        try:
            from outside import SURFACE_MARGIN_FROM_TOP
            surface_y = map_height - SURFACE_MARGIN_FROM_TOP
        except Exception:
            surface_y = map_height * 0.7

        margin = 250
        water_top    = max(200, surface_y - 150)
        water_bottom = 150
        if water_top <= water_bottom:
            water_top = water_bottom + 200

        nx = random.uniform(margin, max(margin + 1, map_width - margin))
        ny = random.uniform(water_bottom, water_top)
        self.waypoints = [(nx, ny)]
        self.current_wp = 0
        self._update_direction()





    def _update_direction(self):
        if self.current_wp >= len(self.waypoints):
            return
        tx, ty = self.waypoints[self.current_wp]
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist == 0:
            dist = 1
        self.dir_x = dx / dist
        self.dir_y = dy / dist




    def draw(self):
        body = arcade.rect.XYWH(self.x, self.y, self.width, self.height)
        arcade.draw_rect_filled(body, arcade.color.BLACK)
        arcade.draw_rect_outline(body, arcade.color.RED, border_width=4)

        # Tanda mata/sirip kecil agar terasa seperti hiu
        eye = arcade.rect.XYWH(self.x + 80, self.y + 15, 10, 10)
        arcade.draw_rect_filled(eye, arcade.color.WHITE)




    def update(self, map_width=0, map_height=0):
        if self.markedfor_removal:
            return

        self.x += self.dir_x * self.speed
        self.y += self.dir_y * self.speed

        if self.eat_cooldown > 0:
            self.eat_cooldown -= 1

        if self.current_wp < len(self.waypoints):
            tx, ty = self.waypoints[self.current_wp]
            jarak = math.sqrt((tx - self.x)**2 + (ty - self.y)**2)
            if jarak < 40:
                if self.patrol:
                    # Mode patrol: sudah sampai target, pilih target baru
                    # secara acak di dalam air dan terus berenang (loop).
                    self._pick_random_patrol_waypoint(map_width, map_height)
                else:
                    self.current_wp += 1
                    if self.current_wp < len(self.waypoints):
                        self._update_direction()
                    else:
                        # Sudah sampai titik KELUAR (yang sengaja ditaruh di
                        # luar kamera, lihat _buat_waypoints: padding=300).
                        # Anggap despawn DI SINI — jangan nunggu sampai
                        # benar-benar mentok ke ujung MAP absolut, karena
                        # itu bisa jauh sekali dari kamera (map berukuran
                        # 4x layar) dan bikin sfx loop nyangkut lama
                        # walau ikannya sudah tidak terlihat di layar.
                        self.markedfor_removal = True

        if self.patrol:
            # Ikan patrol tidak pernah keluar map — clamp ke dalam batas air
            # supaya tidak nyasar ke area udara atau keluar dari peta.
            try:
                from outside import SURFACE_MARGIN_FROM_TOP
                surface_y = map_height - SURFACE_MARGIN_FROM_TOP
            except Exception:
                surface_y = map_height * 0.7
            half_w, half_h = self.width / 2, self.height / 2
            min_x, max_x = half_w + 20, max(half_w + 21, map_width - half_w - 20)
            min_y, max_y = 100, max(101, surface_y - 100)
            if self.x < min_x or self.x > max_x:
                self.x = max(min_x, min(self.x, max_x))
                self.dir_x *= -1
            if self.y < min_y or self.y > max_y:
                self.y = max(min_y, min(self.y, max_y))
                self.dir_y *= -1
        else:
            MARGIN = 350
            if (self.x < -MARGIN or self.x > map_width + MARGIN or
                    self.y < -MARGIN or self.y > map_height + MARGIN):
                self.markedfor_removal = True




    def eat_nearby_fish(self, enemy_list, eat_animations):
        if self.eat_cooldown > 0:
            return

        fish_left   = self.x - self.width / 2
        fish_right  = self.x + self.width / 2
        fish_top    = self.y + self.height / 2
        fish_bottom = self.y - self.height / 2




        for prey in enemy_list:
            if getattr(prey, 'is_panik', False):
                continue
            if getattr(prey, 'kebal_timer', 0) > 0:
                continue





            nama = prey.__class__.__name__
            if nama == "hugefish":
                pw, ph = 150, 75
            elif nama in ("mediumfish", "speedmediumfish"):
                pw, ph = 90, 45
            elif nama in ("smallfish", "jumpingsmallfish"):
                pw, ph = 50, 25
            else:
                continue

            prey_left   = prey.x - pw / 2
            prey_right  = prey.x + pw / 2
            prey_top    = prey.y + ph / 2
            prey_bottom = prey.y - ph / 2

            colliding = (
                fish_right  >= prey_left  and
                fish_left   <= prey_right and
                fish_top    >= prey_bottom and
                fish_bottom <= prey_top
            )

            if colliding:
                from eat_fish import EatAnimation



                class _FakePlayer:
                    def __init__(self, x, y):
                        self.x = x
                        self.y = y

                eat_animations.append(EatAnimation(prey, _FakePlayer(self.x, self.y)))





                map_w = prey.screen_width if hasattr(prey, 'screen_width') else 3200
                map_h = prey.screen_height if hasattr(prey, 'screen_height') else 2240
                try:
                    from outside import SURFACE_MARGIN_FROM_TOP as _SMT
                    _wmax = map_h - _SMT - 80
                except Exception:
                    _wmax = map_h - 80
                for _ in range(50):
                    nx = random.uniform(80, map_w - 80)
                    ny = random.uniform(80, _wmax)
                    if math.sqrt((nx - self.x)**2 + (ny - self.y)**2) > 400:
                        prey.x = nx
                        prey.y = ny
                        if hasattr(prey, 'target_x'):
                            prey.target_x = random.uniform(80, map_w - 80)
                            prey.target_y = random.uniform(80, _wmax)
                        break





                self.eat_cooldown = 15
                break  


class DangerousFishManager:
    """Mengelola dangerous fish dengan sistem difficulty scaling.

    - Ikan PERTAMA selalu muncul dengan cara klasik & dramatis: tanda
      peringatan (kotak merah berkedip di tepi layar) lalu ikan masuk
      dari tepi map, melintas, dan keluar lagi (di-remove), lalu siklus
      ini berulang terus sepanjang game (perilaku asli, tetap dijaga).

    - Seiring waktu bermain (total_time) DAN saat status player naik
      (MEDIUM/HUGE), jumlah "slot" dangerous fish yang diizinkan aktif
      makin banyak. Slot tambahan ini diisi oleh dangerous fish "ambient"
      yang SUDAH berada di dalam air sejak awal (tanpa tanda peringatan),
      berenang berkeliling (patrol) di dalam batas air selamanya — mirip
      peningkatan kesulitan bertahap ala "endless runner".
    """

    ARAH_LIST = [
        "right", "left",
    ]

    # ── SFX 'jumpscare' — di-LOOP terus-menerus mulai dari tanda
    # peringatan muncul sampai ikan klasik ini despawn (keluar map).
    # Satu file tetap (TIDAK acak).
    JUMPSCARE_SFX_FILE = "dangerous.mp3"
    JUMPSCARE_SFX_DIR  = ("assets", "sfx", "dangerous_sfx")

    # ── Volume dinamis berdasarkan jarak ke main_fish ──
    # Jauh (>= MAX_DIST)  -> volume normal (baseline dari settings sfx_volume)
    # Dekat (<= MIN_DIST) -> volume naik bertahap sampai JUMPSCARE_VOLUME_MAX
    JUMPSCARE_VOLUME_MAX_DIST = 900    # px — mulai dari sini volume masih normal
    JUMPSCARE_VOLUME_MIN_DIST = 150    # px — di titik ini volume sudah maksimum
    JUMPSCARE_VOLUME_MAX      = 1.0    # volume tertinggi saat sangat dekat

    # ── Konfigurasi difficulty scaling ──
    BASE_SLOT            = 1     # slot dasar (ikan klasik dengan warning)
    DIFFICULTY_TIME_STEP = 45    # tiap sekian detik, +1 slot dari waktu
    DIFFICULTY_TIME_CAP  = 5     # maksimum slot tambahan dari waktu bermain
    MEDIUM_STATUS_BONUS  = 2     # slot tambahan saat player status MEDIUM
    HUGE_STATUS_BONUS    = 5     # slot tambahan saat player status HUGE
    ABSOLUTE_MAX_SLOT    = 9     # batas keras jumlah dangerous fish aktif

    AMBIENT_SPAWN_MIN = 60 * 5    # jeda minimum antar spawn ambient (detik*60)
    AMBIENT_SPAWN_MAX = 60 * 10   # jeda maksimum antar spawn ambient

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # ── Slot utama (klasik, dengan warning) ──
        self.warning = None
        self.active_fish = None
        self.arah_terpilih = None
        self.spawn_timer = random.uniform(60 * 15, 60 * 30)
        self.warning_duration = 100

        # ── Slot ambient (tanpa warning, sudah di dalam air) ──
        self.ambient_fish_list = []
        self.ambient_spawn_timer = random.uniform(self.AMBIENT_SPAWN_MIN, self.AMBIENT_SPAWN_MAX)

        # ── SFX jumpscare: di-load SEKALI di sini (bukan tiap kali dipicu) ──
        self._jumpscare_sfx = None
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            sfx_path = os.path.join(base_dir, *self.JUMPSCARE_SFX_DIR, self.JUMPSCARE_SFX_FILE)
            self._jumpscare_sfx = arcade.load_sound(sfx_path)
        except Exception as e:
            print(f"Gagal memuat sfx jumpscare dangerous fish: {e}")

        # Referensi player suara yang SEDANG loop — dipakai untuk
        # menghentikannya nanti saat ikan despawn, dan untuk mengubah-ubah
        # volumenya secara real-time berdasarkan jarak ke main_fish.
        self._jumpscare_player = None
        self._jumpscare_base_volume = 3   # diisi ulang tiap loop dimulai

    def _start_jumpscare_loop(self):
        """Mulai memutar sfx SECARA LOOP. Dipanggil sekali saat tanda
        peringatan (warning) muncul — sfx terus berputar selama warning
        DAN selama ikan klasik itu masih ada, sampai despawn."""
        if self._jumpscare_sfx is None:
            return

        # Jaga-jaga: hentikan dulu instance lama kalau (entah kenapa)
        # masih ada yang berjalan, supaya tidak dobel/menumpuk.
        self._stop_jumpscare_loop()

        try:
            from setting import load_settings as _ls
            volume = _ls().get("sfx_volume", 0.6)
        except Exception:
            volume = 0.6

        # Simpan sebagai baseline — inilah volume 'normal' saat ikan masih
        # jauh. Volume akan naik dari titik ini seiring makin dekatnya ikan.
        self._jumpscare_base_volume = volume

        try:
            self._jumpscare_player = arcade.play_sound(
                self._jumpscare_sfx, volume=volume, loop=True
            )
            audio_registry.register(self._jumpscare_player)
        except Exception as e:
            print(f"Gagal memutar sfx jumpscare dangerous fish: {e}")

    def _update_jumpscare_volume(self, player):
        """Sesuaikan volume sfx loop berdasarkan jarak active_fish ke
        main_fish — makin dekat, makin kencang. Panggil tiap frame selama
        active_fish masih ada."""
        if self._jumpscare_player is None or player is None or self.active_fish is None:
            return

        jarak = math.sqrt(
            (self.active_fish.x - player.x) ** 2 +
            (self.active_fish.y - player.y) ** 2
        )

        # t = 0 saat sejauh MAX_DIST (atau lebih jauh) -> volume normal
        # t = 1 saat sedekat MIN_DIST (atau lebih dekat) -> volume maksimum
        span = self.JUMPSCARE_VOLUME_MAX_DIST - self.JUMPSCARE_VOLUME_MIN_DIST
        if span <= 0:
            t = 1.0
        else:
            t = (self.JUMPSCARE_VOLUME_MAX_DIST - jarak) / span
        t = max(0.0, min(1.0, t))

        volume = self._jumpscare_base_volume + (self.JUMPSCARE_VOLUME_MAX - self._jumpscare_base_volume) * t

        try:
            self._jumpscare_player.volume = volume
        except Exception:
            pass

    def _stop_jumpscare_loop(self):
        """Hentikan sfx loop (dipanggil saat ikan klasik despawn)."""
        if self._jumpscare_player is None:
            return
        try:
            arcade.stop_sound(self._jumpscare_player)
        except Exception:
            pass
        audio_registry.unregister(self._jumpscare_player)
        self._jumpscare_player = None

    def _hitung_target_slot(self, total_time, player_status):
        """Hitung total jumlah dangerous fish yang boleh aktif bersamaan,
        berdasarkan lama waktu bermain dan status evolusi player.
        """
        time_slot = min(self.DIFFICULTY_TIME_CAP, int(total_time // self.DIFFICULTY_TIME_STEP))

        status_bonus = 0
        if player_status == "HUGE":
            status_bonus = self.HUGE_STATUS_BONUS
        elif player_status == "MEDIUM":
            status_bonus = self.MEDIUM_STATUS_BONUS

        target = self.BASE_SLOT + time_slot + status_bonus
        return min(self.ABSOLUTE_MAX_SLOT, target)

    def update(self, camera, map_width, map_height, enemy_list=None,
               eat_animations=None, total_time=0.0, player_status="SMALL", player=None):

        # ── Slot utama (klasik: warning -> masuk -> melintas -> keluar) ──
        if self.warning is None and self.active_fish is None:
            self.spawn_timer -= 1
            if self.spawn_timer <= 0:
                self._mulai_peringatan()
        elif self.warning is not None:
            self.warning.update()
            if self.warning.is_done():
                self._spawn_ikan(camera, map_width, map_height)
                self.warning = None
        elif self.active_fish is not None:
            self.active_fish.update(map_width, map_height)

            if enemy_list is not None and eat_animations is not None:
                self.active_fish.eat_nearby_fish(enemy_list, eat_animations)

            # Volume sfx loop menyesuaikan jarak ke main_fish tiap frame.
            self._update_jumpscare_volume(player)

            if self.active_fish.markedfor_removal:
                # Ikan despawn (keluar map) -> hentikan sfx loop di sini.
                self._stop_jumpscare_loop()
                self.active_fish = None
                self.spawn_timer = random.uniform(60 * 30, 60 * 60)

        # ── Slot ambient (difficulty scaling — tanpa warning) ──
        target_slot = self._hitung_target_slot(total_time, player_status)
        # Slot ambient = total target dikurangi 1 slot utama (klasik)
        target_ambient = max(0, target_slot - self.BASE_SLOT)

        if len(self.ambient_fish_list) < target_ambient:
            self.ambient_spawn_timer -= 1
            if self.ambient_spawn_timer <= 0:
                self._spawn_ambient(camera, map_width, map_height)
                self.ambient_spawn_timer = random.uniform(
                    self.AMBIENT_SPAWN_MIN, self.AMBIENT_SPAWN_MAX
                )

        for fish in self.ambient_fish_list:
            fish.update(map_width, map_height)
            if enemy_list is not None and eat_animations is not None:
                fish.eat_nearby_fish(enemy_list, eat_animations)

        # Ikan ambient tidak pernah markedfor_removal (mode patrol tidak
        # pernah keluar map), tapi tetap disaring untuk jaga-jaga.
        self.ambient_fish_list = [f for f in self.ambient_fish_list if not f.markedfor_removal]




    def _mulai_peringatan(self):
        self.arah_terpilih = random.choice(self.ARAH_LIST)
        self.warning = DangerousFishWarning(
            self.arah_terpilih, self.screen_width, self.screen_height,
            duration=self.warning_duration
        )
        # Sfx mulai LOOP dari sini — terus berputar selama warning tampil
        # DAN selama ikannya melintas, sampai despawn (lihat _stop_jumpscare_loop).
        self._start_jumpscare_loop()





    def _buat_waypoints(self, camera, map_width, map_height):





        from outside import SURFACE_MARGIN_FROM_TOP
        surface_y   = map_height - SURFACE_MARGIN_FROM_TOP





        water_min_y = 100
        water_max_y = surface_y - 80

        cam_x, cam_y = camera.position
        half_w  = self.screen_width / 2
        padding = 300





        spawn_y = random.uniform(water_min_y, water_max_y)

        if self.arah_terpilih == "right":
            # Masuk dari kanan, keluar ke kiri
            start = (cam_x + half_w + padding, spawn_y)
            end   = (cam_x - half_w - padding, spawn_y)
        else:
            # Masuk dari kiri, keluar ke kanan
            start = (cam_x - half_w - padding, spawn_y)
            end   = (cam_x + half_w + padding, spawn_y)



        waypoints = [end]

        return start, waypoints

    def _spawn_ikan(self, camera, map_width, map_height):
        start, waypoints = self._buat_waypoints(camera, map_width, map_height)
        self.active_fish = dangerousfish(
            start[0], start[1],
            waypoints,
            speed=random.uniform(3.0, 4.5)
        )

    def _spawn_ambient(self, camera, map_width, map_height):
        """Spawn dangerous fish tambahan LANGSUNG di dalam air, tanpa tanda
        peringatan — dipakai untuk peningkatan kesulitan seiring waktu.
        """
        try:
            from outside import SURFACE_MARGIN_FROM_TOP
            surface_y = map_height - SURFACE_MARGIN_FROM_TOP
        except Exception:
            surface_y = map_height * 0.7

        margin = 250
        water_top    = max(200, surface_y - 150)
        water_bottom = 150
        if water_top <= water_bottom:
            water_top = water_bottom + 200

        x = random.uniform(margin, max(margin + 1, map_width - margin))
        y = random.uniform(water_bottom, water_top)

        fish = dangerousfish(
            x, y, [(x, y)],
            speed=random.uniform(3.0, 4.5),
            patrol=True,
        )
        fish._pick_random_patrol_waypoint(map_width, map_height)
        self.ambient_fish_list.append(fish)

    def _semua_ikan_aktif(self):
        """Kumpulkan semua dangerous fish yang sedang aktif (klasik + ambient)."""
        semua = list(self.ambient_fish_list)
        if self.active_fish is not None:
            semua.append(self.active_fish)
        return semua

    def check_collision(self, player, window, screen_width, screen_height, map_width, map_height,
                         chomp_active=False, eat_animations=None):
        if player.is_spawning or player.kebal_timer > 0:
            return

        player_left   = player.x - (player.width / 2)
        player_right  = player.x + (player.width / 2)
        player_top    = player.y + (player.height / 2)
        player_bottom = player.y - (player.height / 2)

        for fish in self._semua_ikan_aktif():
            fish_left   = fish.x - (fish.width / 2)
            fish_right  = fish.x + (fish.width / 2)
            fish_top    = fish.y + (fish.height / 2)
            fish_bottom = fish.y - (fish.height / 2)

            is_colliding = (
                player_right  >= fish_left  and
                player_left   <= fish_right and
                player_top    >= fish_bottom and
                player_bottom <= fish_top
            )

            if not is_colliding:
                continue

            if chomp_active:
                # CHOMP CHOMP aktif — main_fish memakan dangerous fish,
                # bukan dimakan olehnya. Ikan tidak dihapus permanen,
                # tapi dipindah (mirip prinsip foodchain: relokasi, bukan
                # hapus) supaya populasi dangerous fish tetap stabil.
                player.score = getattr(player, 'score', 0) + random.randint(15, 25)
                player.total_points = getattr(player, 'total_points', 0) + 20
                if hasattr(player, 'check_evolution'):
                    player.check_evolution()

                if eat_animations is not None:
                    from eat_fish import EatAnimation
                    eat_animations.append(EatAnimation(fish, player))

                if fish.patrol:
                    fish._pick_random_patrol_waypoint(map_width, map_height)
                    fish.x, fish.y = fish.waypoints[0]
                else:
                    fish.markedfor_removal = True
                return

            player.score = max(0, player.score - 9999)
            spawn_x = map_width // 2
            spawn_y = map_height // 2
            player.trigger_respawn(spawn_x, spawn_y, map_height, eaten_by=(fish.x, fish.y))
            window.set_mouse_position(screen_width // 2, screen_height // 2)
            return

    def draw_world(self):
        for fish in self._semua_ikan_aktif():
            fish.draw()




    def draw_gui(self):
        if self.warning is not None:
            self.warning.draw()