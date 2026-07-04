import arcade
import random
import math


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
    def __init__(self, start_x, start_y, waypoints, speed=3.5):






        self.x = start_x
        self.y = start_y

        self.width = 220
        self.height = 90

        self.speed = speed
        self.waypoints = list(waypoints)  
        self.current_wp = 0             

        self.is_dangerous = True
        self.markedfor_removal = False




        self._update_direction()
        self.eat_cooldown = 0





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
                self.current_wp += 1
                if self.current_wp < len(self.waypoints):
                    self._update_direction()





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





    ARAH_LIST = [
        "right", "left",  
    ]

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.warning = None
        self.active_fish = None
        self.arah_terpilih = None

        self.spawn_timer = random.uniform(60 * 15, 60 * 30)
        self.warning_duration = 100






    def update(self, camera, map_width, map_height, enemy_list=None, eat_animations=None):



        if self.warning is None and self.active_fish is None:
            self.spawn_timer -= 1
            if self.spawn_timer <= 0:
                self._mulai_peringatan()
            return





        if self.warning is not None:
            self.warning.update()
            if self.warning.is_done():
                self._spawn_ikan(camera, map_width, map_height)
                self.warning = None
            return




        if self.active_fish is not None:
            self.active_fish.update(map_width, map_height)





            if enemy_list is not None and eat_animations is not None:
                self.active_fish.eat_nearby_fish(enemy_list, eat_animations)

            if self.active_fish.markedfor_removal:
                self.active_fish = None
                self.spawn_timer = random.uniform(60 * 30, 60 * 60)




    def _mulai_peringatan(self):
        self.arah_terpilih = random.choice(self.ARAH_LIST)
        self.warning = DangerousFishWarning(
            self.arah_terpilih, self.screen_width, self.screen_height,
            duration=self.warning_duration
        )





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

    def check_collision(self, player, window, screen_width, screen_height, map_width, map_height):
        if self.active_fish is None:
            return
        if player.is_spawning or player.kebal_timer > 0:
            return

        fish = self.active_fish

        player_left   = player.x - (player.width / 2)
        player_right  = player.x + (player.width / 2)
        player_top    = player.y + (player.height / 2)
        player_bottom = player.y - (player.height / 2)

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

        if is_colliding:
            player.score = max(0, player.score - 9999)
            spawn_x = map_width // 2
            spawn_y = map_height // 2
            player.trigger_respawn(spawn_x, spawn_y, map_height, eaten_by=(fish.x, fish.y))
            window.set_mouse_position(screen_width // 2, screen_height // 2)




    def draw_world(self):
        if self.active_fish is not None:
            self.active_fish.draw()




    def draw_gui(self):
        if self.warning is not None:
            self.warning.draw()