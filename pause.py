import arcade

import audio_registry


WIDTH = 800
HEIGHT = 560

class pause(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        # Ukuran tombol tetap, posisi dihitung dinamis
        self.resume_btn_w = 140
        self.resume_btn_h = 44
        self.exit_btn_w   = 140
        self.exit_btn_h   = 44
        self.restart_btn_w = 140
        self.restart_btn_h = 44

    def _pos(self):
        CX = self.window.width  // 2
        CY = self.window.height // 2
        self.resume_btn_x  = CX - 160
        self.resume_btn_y  = CY - 70
        self.exit_btn_x    = CX
        self.exit_btn_y    = CY - 70
        self.restart_btn_x = CX + 160
        self.restart_btn_y = CY - 70

    def on_draw(self):
        self.clear()
        self.game_view.on_draw()
        # game_view.on_draw() meninggalkan kamera GUI game (gui_camera) aktif.
        # Reset ke kamera default supaya overlay pause menu ini digambar
        # dengan koordinat layar yang benar, bukan lewat proyeksi kamera game.
        self.window.default_camera.use()
        self._pos()
        CX = self.window.width  // 2
        CY = self.window.height // 2

        # Gambar Menu Pause
        arcade.draw_rect_filled(arcade.XYWH(CX, CY + 20, 340, 160), arcade.color.DARK_GRAY)
        arcade.draw_text("GAME PAUSED", CX, CY + 20, arcade.color.WHITE, font_size=20, anchor_x="center", anchor_y="center")

        # Tombol Resume
        arcade.draw_rect_filled(arcade.XYWH(self.resume_btn_x, self.resume_btn_y, self.resume_btn_w, self.resume_btn_h), arcade.color.GREEN)
        arcade.draw_text("RESUME", self.resume_btn_x, self.resume_btn_y, arcade.color.BLACK, font_size=14, anchor_x="center", anchor_y="center")

        # Tombol Exit
        arcade.draw_rect_filled(arcade.XYWH(self.exit_btn_x, self.exit_btn_y, self.exit_btn_w, self.exit_btn_h), arcade.color.RED)
        arcade.draw_text("EXIT", self.exit_btn_x, self.exit_btn_y, arcade.color.WHITE, font_size=14, anchor_x="center", anchor_y="center")

        # Tombol Restart
        arcade.draw_rect_filled(arcade.XYWH(self.restart_btn_x, self.restart_btn_y, self.restart_btn_w, self.restart_btn_h), arcade.color.RED)
        arcade.draw_text("RESTART", self.restart_btn_x, self.restart_btn_y, arcade.color.WHITE, font_size=14, anchor_x="center", anchor_y="center")
        
    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.resume_game()

    def on_mouse_press(self, x, y, button, modifiers):
        self._pos()
        if button == arcade.MOUSE_BUTTON_LEFT:
            left = self.resume_btn_x - (self.resume_btn_w / 2)
            right = self.resume_btn_x + (self.resume_btn_w / 2)
            bottom = self.resume_btn_y - (self.resume_btn_h / 2)
            top = self.resume_btn_y + (self.resume_btn_h / 2) 
            
            if left <= x <= right and bottom <= y <= top:
                self.resume_game()
            

            exit_left = self.exit_btn_x - (self.exit_btn_w / 2)
            exit_right = self.exit_btn_x + (self.exit_btn_w / 2)
            exit_bottom = self.exit_btn_y - (self.exit_btn_h / 2)
            exit_top = self.exit_btn_y + (self.exit_btn_h / 2) 
            
            if exit_left <= x <= exit_right and exit_bottom <= y <= exit_top:
                if hasattr(self.game_view, '_save_highscore_to_csv'):
                    self.game_view._save_highscore_to_csv()
                # Benar-benar hentikan SEMUA sfx looping (bukan cuma pause)
                # supaya tidak ada yang kebawa nyangkut ke menu.
                audio_registry.stop_all()
                from loading_screen import LoadingScreen
                from menu import MenuView
                self.window.show_view(LoadingScreen(on_ready=lambda: MenuView()))

            
            restart_left = self.restart_btn_x - (self.restart_btn_w / 2)
            restart_right = self.restart_btn_x + (self.restart_btn_w / 2)
            restart_bottom = self.restart_btn_y - (self.restart_btn_h / 2)
            restart_top = self.restart_btn_y + (self.restart_btn_h / 2) 
            
            if restart_left <= x <= restart_right and restart_bottom <= y <= restart_top:
                # Simpan Total Time & Total Point sesi ini dulu sebelum restart.
                if hasattr(self.game_view, '_save_highscore_to_csv'):
                    self.game_view._save_highscore_to_csv()
                # Benar-benar hentikan SEMUA sfx looping (bukan cuma pause)
                # supaya tidak ada yang kebawa nyangkut ke sesi game baru.
                audio_registry.stop_all()
                from loading_screen import LoadingScreen
                from game import GameView
                self.window.show_view(LoadingScreen(on_ready=lambda: GameView()))

    # Fungsi pembantu untuk meresume game sekaligus mengunci mouse kembali
    def resume_game(self):
        self.window.set_mouse_visible(False)   # Sembunyikan kursor kembali
        self.game_view._confine_mouse()         # Kunci koordinat mouse lagi lewat Win32API
        # Lanjutkan semua sfx looping/ambient yang di-pause_all() tadi
        # (outside, bubble, suck, jumpscare dangerous fish, dll).
        audio_registry.resume_all()
        self.window.show_view(self.game_view)   # Kembali ke game