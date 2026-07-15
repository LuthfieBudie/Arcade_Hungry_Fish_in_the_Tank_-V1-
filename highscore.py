import arcade
import os
import csv

WIDTH = 800
HEIGHT = 560
TITLE = "Feeding Frenzy"
FILE_NAME = "username.csv"

# Warna ranking 1/2/3 (emas, perak, perunggu) — pakai RGB manual karena
# tidak semua nama warna ini tersedia di arcade.color
GOLD_COLOR   = (255, 215, 0)
SILVER_COLOR = (200, 200, 200)
BRONZE_COLOR = (205, 127, 50)


class score(arcade.View):
    def __init__(self):
        super().__init__()

        self.menubtn_w      = 200
        self.menubtn_h      = 55

        self.menubtn_hovered = False

        self.entries = self._load_highscores()
    

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

    # ── BACA DATA DARI username.csv ─────────────────────────────────────
    def _load_highscores(self):
        """Baca username.csv dan susun daftar highscore (nama, waktu, poin),
        diurutkan dari poin (Freeplay Score) tertinggi ke terendah.

        Format tiap baris CSV: [Name, Date, Time, Freeplay Score]
        Data Time & Freeplay Score ini diisi oleh GameView setiap kali
        sesi permainan berakhir (lihat game.py -> _save_highscore_to_csv).
        """
        entries = []
        if os.path.exists(FILE_NAME):
            try:
                with open(FILE_NAME, mode='r', newline='', encoding='utf-8') as file:
                    reader = list(csv.reader(file))
                for row in reader[1:]:
                    if not row or not row[0].strip():
                        continue
                    nama = row[0].strip()
                    waktu = row[2].strip() if len(row) > 2 and row[2].strip() else "-"
                    poin_raw = row[3].strip() if len(row) > 3 else ""
                    try:
                        poin = int(poin_raw) if poin_raw not in ("", "-") else 0
                    except ValueError:
                        poin = 0
                    entries.append({"name": nama, "time": waktu, "points": poin})
            except Exception as e:
                print(f"Gagal membaca highscore dari CSV: {e}")

        entries.sort(key=lambda e: e["points"], reverse=True)
        return entries[:10]   # tampilkan 10 besar saja

    def on_show_view(self):
        arcade.set_background_color((9, 26, 45))
        self.menubtn_x = self.window.width  // 2
        self.menubtn_y = self.window.height // 2 - 140
        # Muat ulang tiap kali layar ini dibuka supaya datanya selalu terbaru
        self.entries = self._load_highscores()

    def on_draw(self):
        self.clear()
        # Reset ke kamera default supaya tidak mewarisi kamera custom
        # yang ditinggalkan aktif oleh GameView.
        self.window.default_camera.use()
        self.menubtn_x = self.window.width  // 2
        self.menubtn_y = self.window.height // 2 - 140

        cx = self.window.width // 2

        arcade.draw_text(
            "HIGHSCORE",
            x=cx, y=self.window.height - 60,
            color=(216, 178, 92), font_size=28, bold=True,
            anchor_x="center", anchor_y="center",
        )

        if not self.entries:
            arcade.draw_text(
                "Belum ada rekor. Main dulu, yuk!",
                x=cx, y=self.window.height // 2 + 40,
                color=arcade.color.LIGHT_GRAY, font_size=16,
                anchor_x="center", anchor_y="center",
            )
        else:
            header_y = self.window.height - 110

            arcade.draw_text("NAMA", x=cx - 230, y=header_y,
                             color=arcade.color.LIGHT_GRAY, font_size=13, bold=True,
                             anchor_x="left", anchor_y="center")
            arcade.draw_text("POINTS", x=cx + 30, y=header_y,
                             color=arcade.color.LIGHT_GRAY, font_size=13, bold=True,
                             anchor_x="left", anchor_y="center")
            arcade.draw_text("TIME", x=cx + 150, y=header_y,
                             color=arcade.color.LIGHT_GRAY, font_size=13, bold=True,
                             anchor_x="left", anchor_y="center")

            row_h = 32
            start_y = header_y - 32
            batas_bawah = self.menubtn_y + 60   # jangan sampai menabrak tombol

            for i, entry in enumerate(self.entries):
                row_y = start_y - i * row_h
                if row_y < batas_bawah:
                    break

                if i == 0:
                    rank_color = GOLD_COLOR
                elif i == 1:
                    rank_color = SILVER_COLOR
                elif i == 2:
                    rank_color = BRONZE_COLOR
                else:
                    rank_color = arcade.color.WHITE

                arcade.draw_text(f"{i + 1}.", x=cx - 270, y=row_y,
                                 color=rank_color, font_size=14, bold=True,
                                 anchor_x="left", anchor_y="center")
                arcade.draw_text(entry["name"], x=cx - 230, y=row_y,
                                 color=rank_color, font_size=14, bold=True,
                                 anchor_x="left", anchor_y="center")
                arcade.draw_text(str(entry["points"]), x=cx + 30, y=row_y,
                                 color=arcade.color.WHITE, font_size=14,
                                 anchor_x="left", anchor_y="center")
                arcade.draw_text(entry["time"], x=cx + 150, y=row_y,
                                 color=arcade.color.WHITE, font_size=14,
                                 anchor_x="left", anchor_y="center")

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
            self._play_click_sfx()
            from menu import MenuView
            menu_view = MenuView()
            self.window.show_view(menu_view)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._play_click_sfx()
            if self._help_button(x, y):
                from menu import MenuView
                menu_view = MenuView()
                self.window.show_view(menu_view)


def main():
    game = score()
    arcade.run()

if __name__ == "__main__":
    main()