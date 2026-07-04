import arcade

WIDTH = 800
HEIGHT = 560
TITLE = "Feeding Frenzy"

class score(arcade.View):
    def __init__(self):
        super().__init__()



        self.menubtn_w      = 200
        self.menubtn_h      = 55

        self.menubtn_hovered = False








    def on_show_view(self):
        arcade.set_background_color((10, 10, 15))
        self.menubtn_x = self.window.width  // 2
        self.menubtn_y = self.window.height // 2 - 140





    def on_draw(self):
        self.clear()
        # Reset ke kamera default supaya tidak mewarisi kamera custom
        # yang ditinggalkan aktif oleh GameView.
        self.window.default_camera.use()
        self.menubtn_x = self.window.width  // 2
        self.menubtn_y = self.window.height // 2 - 140

        if self.menubtn_hovered:
            menubtn_color    = (60, 180, 100)   # Hijau terang saat hover
        else:
            menubtn_color    = (40, 130, 70)    # Hijau normal
        
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.menubtn_x, self.menubtn_y, self.menubtn_w, self.menubtn_h),
            menubtn_color,
        )

        arcade.draw_text(
            "MAIN MENU",
            x=self.menubtn_x,
            y=self.menubtn_y,
            color=arcade.color.WHITE,
            font_size=22,
            bold=True,
            anchor_x="center",
            anchor_y="center",
        ) 
    
    def _help_button(self, x, y):
        half_w = self.menubtn_w / 2
        half_h = self.menubtn_h / 2
        return (
            self.menubtn_x - half_w <= x <= self.menubtn_x + half_w and
            self.menubtn_y - half_h <= y <= self.menubtn_y + half_h
        )
    
    def on_mouse_motion(self, x, y, dx, dy):
        self.menubtn_hovered = self._help_button(x, y) 









    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            from menu import MenuView
            menu_view = MenuView()
            self.window.show_view(menu_view)
        
        


    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self._help_button(x, y):
                from menu import MenuView
                menu_view = MenuView()
                self.window.show_view(menu_view) 




def main():
    game = help()
    arcade.run()

if __name__ == "__main__":
    main()