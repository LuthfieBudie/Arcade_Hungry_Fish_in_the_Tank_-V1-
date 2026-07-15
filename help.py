import arcade
import random
import os

WIDTH = 800
HEIGHT = 560
TITLE = "Feeding Frenzy"


class help(arcade.View):
    def __init__(self):
        super().__init__()



        self.paper_w = 0
        self.paper_h = 0

        self.paper_points = []



        self.menubtn_x = 0
        self.menubtn_y = 0
        self.menubtn_w = 200               
        self.menubtn_h = 55

        self.menubtn_hovered = False
    


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


    def on_resize(self, width, height):
        """Otomatis dipanggil oleh arcade saat ukuran window berubah (termasuk fullscreen)"""
        # Panggil on_resize bawaan parent agar kamera internal arcade menyesuaikan diri
        super().on_resize(width, height)
        
        # Hitung titik tengah window yang baru
        self.paper_w = int(width * 0.575)  # 57.5% dari lebar window
        self.paper_h = int(height * 0.642)
        
        self.paper_x = width // 2
        self.paper_y = height // 2 + int(height * 0.05)

        self.menubtn_x = width // 2
        self.menubtn_y = self.paper_y - (self.paper_h // 2) - 60

        # Hitung ulang koordinat kertas koyak berdasarkan posisi tengah yang baru
        self.paper_points = self._generate_torn_paper_points()
    
    
    
    
    
    def _generate_torn_paper_points(self):
        points = []
        half_w = self.paper_w / 2
        half_h = self.paper_h / 2

        left = self.paper_x - half_w
        right = self.paper_x + half_w
        bottom = self.paper_y - half_h
        top = self.paper_y + half_h

        # Mengatur seberapa kasar robekannya (semakin besar roughness, semakin koyak)
        roughness = 4.5
        # Jarak antar robekan (semakin kecil step, robekan semakin detail)
        step = max(6, int(self.paper_w / 60)) 

        # 1. Sisi Atas (dari Kiri ke Kanan)
        for x in range(int(left), int(right), step):
            y = top + random.uniform(-roughness, roughness)
            points.append((x, y))

        # 2. Sisi Kanan (dari Atas ke Bawah)
        for y in range(int(top), int(bottom), -step):
            x = right + random.uniform(-roughness, roughness)
            points.append((x, y))

        # 3. Sisi Bawah (dari Kanan ke Kiri)
        for x in range(int(right), int(left), -step):
            y = bottom + random.uniform(-roughness, roughness)
            points.append((x, y))

        # 4. Sisi Kiri (dari Bawah ke Atas)
        for y in range(int(bottom), int(top), step):
            x = left + random.uniform(-roughness, roughness)
            points.append((x, y))

        return points








    def on_show_view(self):
        arcade.set_background_color((9, 26, 45))
        self.on_resize(self.window.width, self.window.height)





    def on_draw(self):
        self.clear()
        # Reset ke kamera default supaya tidak mewarisi kamera custom
        # yang ditinggalkan aktif oleh GameView.
        self.window.default_camera.use()
        paper_color = (235, 215, 185)
        if self.paper_points:
            arcade.draw_polygon_filled(self.paper_points, paper_color)

        # 2. ✍️ TAMBAHKAN TEKS DI ATAS KERTAS KOYAK DI SINI
        # Kita sesuaikan font_size secara dinamis juga agar teks ikut membesar saat fullscreen!
        title_font_size = max(20, int(self.paper_h * 0.08))
        text_font_size = max(12, int(self.paper_h * 0.05))

        # --- Judul Halaman Help ---
        arcade.draw_text(
            "CARA BERMAIN",
            x=self.paper_x,
            y=self.paper_y + (self.paper_h // 2) - 50, # Posisi di bagian atas dalam kertas
            color=(50, 40, 30), # Warna cokelat gelap biar kontras dengan kertas krem
            font_size=title_font_size,
            bold=True,
            anchor_x="center",
            anchor_y="center"
        )

        # --- Isi Teks Bantuan / Panduan ---
        # Gunakan '\n' untuk membuat baris baru, dan pastikan tentukan 'multiline=True' serta 'width'
        help_text = (
            "1. Gerakkan mouse untuk mengendalikan arah berenang ikanmu.\n\n"
            "2. Mangsa ikan yang berukuran lebih kecil untuk tumbuh besar.\n\n"
            "3. Hati-hati! Hindari ikan yang berukuran lebih besar darimu.\n\n"
            "4. Klik Kanan untuk menggunakan DASH (Membutuhkan Energi)."
        )

        arcade.draw_text(
            help_text,
            x=self.paper_x,
            y=self.paper_y - 20, # Posisi di tengah agak ke bawah sedikit
            color=(70, 55, 45),
            font_size=text_font_size,
            width=int(self.paper_w * 0.8), # Batasi lebar teks agar tidak keluar dari pinggiran kertas
            multiline=True,
            anchor_x="center",
            anchor_y="center"
        )

        if self.menubtn_hovered:
            menubtn_color    = (78, 62, 38)     # Perunggu hangat saat hover
        else:
            menubtn_color    = (30, 28, 24)     # Charcoal gelap
        
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.menubtn_x, self.menubtn_y, self.menubtn_w, self.menubtn_h),
            menubtn_color,
        )

        arcade.draw_text(
            "MAIN MENU",
            x=self.menubtn_x,
            y=self.menubtn_y,
            color=(255, 255, 255),
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
                self._play_click_sfx()
                from menu import MenuView
                menu_view = MenuView()
                self.window.show_view(menu_view) 




def main():
    game = help()
    arcade.run()

if __name__ == "__main__":
    main()