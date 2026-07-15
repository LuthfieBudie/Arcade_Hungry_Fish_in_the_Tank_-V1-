import arcade
import os    
import csv


WIDTH  = 800
HEIGHT = 560


class MenuView(arcade.View):


    def __init__(self):
        super().__init__()

        self.player_name = "Your Name"
        if os.path.exists("username.csv"): 
            with open("username.csv", mode='r', newline='', encoding='utf-8') as file:
                reader = list(csv.reader(file))
                if len(reader) > 1 and reader[1][0].strip() != "":
                    self.player_name = reader[1][0]

        # Ukuran tombol (tetap)
        self.btnstart_w      = 200
        self.btnstart_h      = 55
        self.exitbtn_w       = 200
        self.exitbtn_h       = 55
        self.helpbtn_w       = 200
        self.helpbtn_h       = 55
        self.scorebtn_w      = 200
        self.scorebtn_h      = 55
        self.settingbtn_w    = 200
        self.settingbtn_h    = 55
        self.namebtn_w       = 200
        self.namebtn_h       = 55

        self.namebtn_hovered    = False
        self.btnstart_hovered   = False
        self.helpbtn_hovered    = False
        self.exitbtn_hovered    = False
        self.settingbtn_hovered = False
        self.scorebtn_hovered   = False

        # === Ukuran & posisi gambar logo (dalam RASIO, bukan pixel tetap) ===
        # Kenapa rasio? Supaya logo tetap proporsional di ukuran window
        # berapa pun (fullscreen, 1280x720, 800x500, dll), karena dihitung
        # ulang dari lebar/tinggi window setiap kali window di-resize.

        # Ukuran logo = persentase dari lebar/tinggi window
        self.bg_w_ratio = 0.85     # lebar logo = 55% dari lebar window
        self.bg_h_ratio = 0.95     # tinggi logo = 30% dari tinggi window

        # Posisi logo = pergeseran dari TITIK TENGAH window (0,0 = tengah)
        # Nilai negatif x = geser ke KIRI, positif = geser ke KANAN
        # Nilai positif y = geser ke ATAS,  negatif = geser ke BAWAH
        self.bg_offset_x_ratio = 0.0    # 0 = tetap di tengah horizontal
        self.bg_offset_y_ratio = 0.25   # geser ke atas sebesar 30% tinggi window

        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Buat SpriteList untuk menampung sprite background agar kompatibel dengan Arcade 3.0+
        self.background_list = arcade.SpriteList()

        # Inisialisasi Background (logo.png)
        bg_path = os.path.join(base_dir, "assets", "image", "logo", "logo.png")
        if os.path.exists(bg_path):
            self.background = arcade.Sprite(bg_path)
            self.background_list.append(self.background)
        else:
            self.background = None



    def _update_positions(self):
        """Hitung ulang posisi tombol berdasarkan ukuran window saat ini."""
        CX = self.window.width  // 2
        CY = self.window.height // 2

        self.btnstart_x   = CX
        self.btnstart_y   = CY - 20

        self.exitbtn_x    = CX
        self.exitbtn_y    = CY - 260

        self.helpbtn_x    = CX
        self.helpbtn_y    = CY - 200

        self.scorebtn_x   = CX
        self.scorebtn_y   = CY - 80

        self.settingbtn_x = CX
        self.settingbtn_y = CY - 140
        
        self.namebtn_x    = CX + 205
        self.namebtn_y    = CY - 20

        # Atur ukuran & posisi background berdasarkan RASIO ukuran window saat ini
        # (JANGAN ubah self.window.width/height, itu akan mengubah ukuran
        # window game itu sendiri, bukan ukuran gambar!)
        if self.background:
            self.background.center_x = CX + (self.window.width  * self.bg_offset_x_ratio)
            self.background.center_y = CY + (self.window.height * self.bg_offset_y_ratio)
            self.background.width  = self.window.width  * self.bg_w_ratio
            self.background.height = self.window.height * self.bg_h_ratio



    def on_resize(self, width, height):
        super().on_resize(width, height)
        self._update_positions()


    def _play_click_sfx(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            sfx_path = os.path.join(base_dir, "assets", "sfx", "button_sfx", "4.mp3")
            click_sound = arcade.load_sound(sfx_path)
            
            # Ambil setelan volume sfx dari file setting bawaan game Anda
            try:
                from setting import load_settings as _ls
                _svol = _ls().get("sfx_volume", 0.0)
            except Exception:
                _svol = 0.0
                
            arcade.play_sound(click_sound, volume=_svol)
        except Exception as e:
            print(f"Gagal memutar SFX tombol: {e}")


    def _dummy(self):
        pass  # spacer

    def on_show_view(self):
        arcade.set_background_color((9, 26, 45))
        self.window.set_mouse_visible(True)
        self._update_positions()

        current_name = getattr(self.window, "current_music_name", None)
        
        is_playing = False
        if hasattr(self.window, "current_player") and self.window.current_player:
            try:
                is_playing = self.window.current_player.playing
            except Exception:
                is_playing = False


        if current_name == "menu" and is_playing:
            return 

        if hasattr(self.window, "current_music") and self.window.current_music and self.window.current_player:
            try:
                self.window.current_music.stop(self.window.current_player)
            except Exception:
                pass

        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            menu_music_path = os.path.join(base_dir, "assets", "music", "menu", "menu1.mp3")
            
            self.window.current_music = arcade.Sound(menu_music_path)
            try:
                from setting import load_settings as _ls
                _mvol = _ls().get("music_volume", 0.5)
            except Exception:
                _mvol = 0.5
            self.window.current_player = self.window.current_music.play(volume=_mvol, loop=True)
            
            self.window.current_music_name = "menu" 
        except Exception as e:
            print(f"Gagal memutar musik menu: {e}")







    def on_draw(self):
        self.clear()
        # PENTING: reset kamera ke default setiap kali menggambar.
        self.window.default_camera.use()
        self._update_positions()

        

        # Menggambar Background
        if self.background:
            self.background_list.draw()


        if self.btnstart_hovered:
            btnstart_color    = (78, 62, 38)     # Perunggu hangat saat hover
        else:
            btnstart_color    = (30, 28, 24)     # Charcoal gelap, senada tekstur logo

        if self.exitbtn_hovered:
            exitbtn_color    = (78, 62, 38)
        else:
            exitbtn_color    = (30, 28, 24)

        if self.helpbtn_hovered:
            helpbtn_color    = (78, 62, 38)
        else:
            helpbtn_color    = (30, 28, 24)

        if self.scorebtn_hovered:
            scorebtn_color    = (78, 62, 38)
        else:
            scorebtn_color    = (30, 28, 24)

        if self.settingbtn_hovered:
            settingbtn_color    = (78, 62, 38)
        else:
            settingbtn_color    = (30, 28, 24)

        if self.namebtn_hovered:
            namebtn_color    = (78, 62, 38)
        else:
            namebtn_color    = (30, 28, 24)









        # Gambar kotak tombol

        outline_color = (255, 255, 255) # Warna outline: putih, persis seperti logo
        outline_thick = 3

        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.btnstart_x, self.btnstart_y, self.btnstart_w, self.btnstart_h),
            btnstart_color,
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(self.btnstart_x, self.btnstart_y, self.btnstart_w, self.btnstart_h),
            outline_color,
            border_width=outline_thick
        )

        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.exitbtn_x, self.exitbtn_y, self.exitbtn_w, self.exitbtn_h),
            exitbtn_color,
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(self.exitbtn_x, self.exitbtn_y, self.exitbtn_w, self.exitbtn_h),
            outline_color,
            border_width=outline_thick
        )

        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.helpbtn_x, self.helpbtn_y, self.helpbtn_w, self.helpbtn_h),
            helpbtn_color,
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(self.helpbtn_x, self.helpbtn_y, self.helpbtn_w, self.helpbtn_h),
            outline_color,
            border_width=outline_thick
        )

        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.scorebtn_x, self.scorebtn_y, self.scorebtn_w, self.scorebtn_h),
            scorebtn_color,
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(self.scorebtn_x, self.scorebtn_y, self.scorebtn_w, self.scorebtn_h),
            outline_color,
            border_width=outline_thick
        )

        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.settingbtn_x, self.settingbtn_y, self.settingbtn_w, self.settingbtn_h),
            settingbtn_color,
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(self.settingbtn_x, self.settingbtn_y, self.settingbtn_w, self.settingbtn_h),
            outline_color,
            border_width=outline_thick
        )

        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.namebtn_x, self.namebtn_y, self.namebtn_w, self.namebtn_h),
            namebtn_color,
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(self.namebtn_x, self.namebtn_y, self.namebtn_w, self.namebtn_h),
            outline_color,
            border_width=outline_thick
        )





        arcade.draw_text(
            "START",
            x=self.btnstart_x,
            y=self.btnstart_y,
            color=(255, 255, 255),
            font_size=22,
            bold=True,
            anchor_x="center",
            anchor_y="center",
        )   


        arcade.draw_text(
            "QUIT",
            x=self.exitbtn_x,
            y=self.exitbtn_y,
            color=(255, 255, 255),
            font_size=22,
            bold=True,
            anchor_x="center",
            anchor_y="center",
        ) 


        arcade.draw_text(
            "HELP",
            x=self.helpbtn_x,
            y=self.helpbtn_y,
            color=(255, 255, 255),
            font_size=22,
            bold=True,
            anchor_x="center",
            anchor_y="center", 
        ) 


        arcade.draw_text(
            "HIGHSCORE",
            x=self.scorebtn_x,
            y=self.scorebtn_y,
            color=(255, 255, 255),
            font_size=22,
            bold=True,
            anchor_x="center",
            anchor_y="center", 
        )


        arcade.draw_text(
            "SETTING",
            x=self.settingbtn_x,
            y=self.settingbtn_y,
            color=(255, 255, 255),
            font_size=22,
            bold=True,
            anchor_x="center",
            anchor_y="center", 
        )

        arcade.draw_text(
            self.player_name,
            x=self.namebtn_x,
            y=self.namebtn_y,
            color=(255, 255, 255),
            font_size=22,
            bold=True,
            anchor_x="center",
            anchor_y="center", 
        )






    def _is_over_button(self, x, y):
        """Cek apakah koordinat (x, y) berada di dalam area tombol START."""
        half_w = self.btnstart_w / 2
        half_h = self.btnstart_h / 2
        return (
            self.btnstart_x - half_w <= x <= self.btnstart_x + half_w and
            self.btnstart_y - half_h <= y <= self.btnstart_y + half_h
        )
    
    def _is_over_help_button(self, x, y):
        """Cek apakah koordinat (x, y) berada di dalam area tombol START."""
        half_w = self.helpbtn_w / 2
        half_h = self.helpbtn_h / 2
        return (
            self.helpbtn_x - half_w <= x <= self.helpbtn_x + half_w and
            self.helpbtn_y - half_h <= y <= self.helpbtn_y + half_h
        )
    
    def _is_over_exit_button(self, x, y):
        """Cek apakah koordinat (x, y) berada di dalam area tombol START."""
        half_w = self.exitbtn_w / 2
        half_h = self.exitbtn_h / 2
        return (
            self.exitbtn_x - half_w <= x <= self.exitbtn_x + half_w and
            self.exitbtn_y - half_h <= y <= self.exitbtn_y + half_h
        )
    
    def _is_over_setting_button(self, x, y):
        """Cek apakah koordinat (x, y) berada di dalam area tombol START."""
        half_w = self.settingbtn_w / 2
        half_h = self.settingbtn_h / 2
        return (
            self.settingbtn_x - half_w <= x <= self.settingbtn_x + half_w and
            self.settingbtn_y - half_h <= y <= self.settingbtn_y + half_h
        )
    
    def _is_over_score_button(self, x, y):
        """Cek apakah koordinat (x, y) berada di dalam area tombol START."""
        half_w = self.scorebtn_w / 2
        half_h = self.scorebtn_h / 2
        return (
            self.scorebtn_x - half_w <= x <= self.scorebtn_x + half_w and
            self.scorebtn_y - half_h <= y <= self.scorebtn_y + half_h
        )
    
    def _is_over_name_button(self, x, y):
        """Cek apakah koordinat (x, y) berada di dalam area tombol START."""
        half_w = self.namebtn_w / 2
        half_h = self.namebtn_h / 2
        return (
            self.namebtn_x - half_w <= x <= self.namebtn_x + half_w and
            self.namebtn_y - half_h <= y <= self.namebtn_y + half_h
        )





    def on_mouse_motion(self, x, y, dx, dy):
        """Update status hover setiap kali mouse bergerak."""
        self.btnstart_hovered = self._is_over_button(x, y) 
        self.exitbtn_hovered = self._is_over_exit_button(x, y) 
        self.helpbtn_hovered = self._is_over_help_button(x, y) 
        self.settingbtn_hovered = self._is_over_setting_button(x, y) 
        self.scorebtn_hovered = self._is_over_score_button(x, y) 
        self.namebtn_hovered = self._is_over_name_button(x, y) 






    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT: 
            if self._is_over_button(x, y):
                self._play_click_sfx()
                from loading_screen import LoadingScreen
                self.window.show_view(LoadingScreen())
            
            elif self._is_over_exit_button(x, y):
                self._play_click_sfx()
                arcade.exit()

            elif self._is_over_help_button(x, y):
                self._play_click_sfx()
                from help import help
                help_view = help()
                self.window.show_view(help_view) 

            elif self._is_over_score_button(x, y):
                self._play_click_sfx()
                from highscore import score
                score_view = score()
                self.window.show_view(score_view) 

            elif self._is_over_setting_button(x, y):
                self._play_click_sfx()
                from setting import setting
                setting_view = setting()
                self.window.show_view(setting_view)

            elif self._is_over_name_button(x, y):
                self._play_click_sfx()
                from name import name
                name_view = name()
                self.window.show_view(name_view)






    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            arcade.exit()