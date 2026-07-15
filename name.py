import arcade
import os
import csv
from datetime import datetime
from ban_word import banword  

WIDTH = 800
HEIGHT = 560
FILE_NAME = "username.csv"

class name(arcade.View):
    def __init__(self):
        super().__init__() 

        self.state = "SELECT"
        self.user_list = []
        self.selected_index = 0
        self.player_name = ""

        self.raw_typing = ""

        self.row_height = 35
        self.start_y = 380  # akan diupdate di on_draw

        self.scroll_offset = 0

        self.load_users_from_csv()

        self.is_renaming = False
        self.old_name_to_rename = ""




        self.confirmbtn_x      = self.window.width  // 2 - 140      
        self.confirmbtn_y      = self.window.height // 2 - 140  
        self.confirmbtn_w      = 200               
        self.confirmbtn_h      = 55

        self.renamebtn_x      = self.window.width  // 2 - 140     
        self.renamebtn_y      = self.window.height // 2 - 200  
        self.renamebtn_w      = 200               
        self.renamebtn_h      = 55

        self.cancelbtn_x      = self.window.width  // 2 + 140      
        self.cancelbtn_y      = self.window.height // 2 - 140
        self.cancelbtn_w      = 200               
        self.cancelbtn_h      = 55

        self.deletebtn_x      = self.window.width  // 2 + 140
        self.deletebtn_y      = self.window.height // 2 - 200
        self.deletebtn_w      = 200               
        self.deletebtn_h      = 55 

        self.createbtn_x = self.window.width  // 2
        self.createbtn_y = -999
        self.createbtn_w = 300
        self.createbtn_h = 30
        
        self.pop_ok_x = self.window.width  // 2 - 80
        self.pop_ok_y = self.window.height // 2 - 30
        self.pop_ok_w = 100
        self.pop_ok_h = 40

        self.pop_cancel_x = self.window.width  // 2 + 80
        self.pop_cancel_y = self.window.height // 2 - 30
        self.pop_cancel_w = 100
        self.pop_cancel_h = 40

        self.alert_ok_x = self.window.width  // 2
        self.alert_ok_y = self.window.height // 2 - 30
        self.alert_ok_w = 100
        self.alert_ok_h = 40






        self.confirmbtn_hovered = False
        self.renamebtn_hovered = False
        self.cancelbtn_hovered = False
        self.deletebtn_hovered = False
        self.createbtn_hovered = False
        self.pop_ok_hovered = False
        self.pop_cancel_hovered = False
        self.alert_ok_hovered = False





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
    
    
    
    def load_users_from_csv(self):
        self.user_list = []
        if os.path.exists(FILE_NAME):
            with open(FILE_NAME, mode='r', newline='', encoding='utf-8') as file:
                reader = list(csv.reader(file))
                for row in reader[1:]:
                    if row and row[0].strip() != "":
                        raw_name = row[0].strip().upper()
                        # Jika di dalam file CSV ada kata terlarang, tampilkan sebagai pagar
                        for word in banword:
                            if word.upper() in raw_name:
                                raw_name = raw_name.replace(word.upper(), "#" * len(word))
                        self.user_list.append(raw_name)
        
        if not self.user_list:
            self.state = "TYPING"
        else:
            self.state = "SELECT"





    def save_active_user_to_top(self, active_name):
        existing_data = {}
        if os.path.exists(FILE_NAME):
            with open(FILE_NAME, mode='r', newline='', encoding='utf-8') as file:
                reader = list(csv.reader(file))
                for row in reader[1:]:
                    if row:
                        existing_data[row[0]] = row[1:] 

        
        current_time = datetime.now().strftime("%d/%m/%Y") 
        



        if self.is_renaming and self.old_name_to_rename in existing_data:
            old_details = existing_data.pop(self.old_name_to_rename)
            old_details[0] = current_time 
            
            existing_data[active_name] = old_details
            self.is_renaming = False
            self.old_name_to_rename = ""
        elif active_name not in existing_data:
            existing_data[active_name] = [current_time,"-","-"]   
        
        with open(FILE_NAME, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Date", "Time", "Freeplay Score"])
            writer.writerow([active_name]+existing_data[active_name])
            for name_key, details in existing_data.items():
                if name_key != active_name:
                    writer.writerow([name_key] + details)





    def delete_user_from_csv(self, name_to_delete):
        existing_data = {}
        if os.path.exists(FILE_NAME):
            with open(FILE_NAME, mode='r', newline='', encoding='utf-8') as file:
                reader = list(csv.reader(file))
                for row in reader[1:]:
                    if row:
                        existing_data[row[0]] = row[1:]
        if name_to_delete in existing_data:
            existing_data.pop(name_to_delete)
        
        with open(FILE_NAME, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Date", "Time", "Freeplay Score"])
            for name_key, details in existing_data.items():
                writer.writerow([name_key]+details)
        
        self.load_users_from_csv()
        if self.selected_index >= len(self.user_list) and self.user_list:
            self.selected_index = len(self.user_list) - 1
        if self.scroll_offset > 0 and len(self.user_list)+1 <= 4:
            self.scroll_offset = 0 





    def on_show_view(self):
        self.start_y = self.window.height // 2 + 100
        arcade.set_background_color((9, 26, 45))




    def on_draw(self):
        self.clear()
        # Reset ke kamera default supaya tidak mewarisi kamera custom
        # yang ditinggalkan aktif oleh GameView.
        self.window.default_camera.use()
        # Update posisi berdasarkan ukuran window saat ini
        self.start_y = self.window.height // 2 + 100

        if self.state == "SELECT" or self.state == "CONFIRM_DELETE":
            arcade.draw_text("WHO ARE YOU?", self.window.width  // 2, self.window.height // 2 + 180, (216, 178, 92), font_size=24, bold=True, anchor_x="center")
            arcade.draw_rect_filled(arcade.rect.XYWH(self.window.width  // 2, self.window.height // 2 + 50, 400, 160), (26, 24, 20))
            
            total_items = len(self.user_list) + 1
            self.createbtn_y = -999

            for i in range(4):
                actual_index = self.scroll_offset + i
                if actual_index < total_items:
                    current_row_y = self.start_y - (i * self.row_height)

                    if actual_index < len(self.user_list):
                        name_text = self.user_list[actual_index]
                        is_selected = (actual_index == self.selected_index)
                    
                        if is_selected:
                            arcade.draw_rect_filled(arcade.rect.XYWH(self.window.width  // 2, current_row_y, 380, 30), (78, 62, 38))
                            color = (216, 178, 92)
                        else:
                            color = arcade.color.WHITE
                    
                        arcade.draw_text(name_text, x=self.window.width  // 2, y=current_row_y, color=color, font_size=18, bold=True, anchor_x="center", anchor_y="center")
                
                    elif actual_index == len(self.user_list):
                        self.createbtn_y = current_row_y
                        create_color = (216, 178, 92) if self.createbtn_hovered else arcade.color.LIGHT_GRAY
                        arcade.draw_text("(Create a New User)", x=self.createbtn_x, y=self.createbtn_y, color=create_color, font_size=16, italic=True, anchor_x="center", anchor_y="center")

            self.confirmbtn_x = self.window.width  // 2 - 140
            self.confirmbtn_y = self.window.height // 2 - 140
            self.cancelbtn_x = self.window.width  // 2 + 140
            self.cancelbtn_y = self.window.height // 2 - 140

            outline_color = (255, 255, 255) # Warna outline: Putih
            outline_thick = 3

            confirmbtn_color = (78, 62, 38) if self.confirmbtn_hovered else (30, 28, 24)
            renamebtn_color  = (78, 62, 38) if self.renamebtn_hovered else (30, 28, 24)
            cancelbtn_color  = (78, 62, 38) if self.cancelbtn_hovered else (30, 28, 24)
            deletebtn_color  = (78, 62, 38) if self.deletebtn_hovered else (30, 28, 24)

            arcade.draw_rect_filled(arcade.rect.XYWH(self.confirmbtn_x, self.confirmbtn_y, self.confirmbtn_w, self.confirmbtn_h), confirmbtn_color)
            arcade.draw_rect_outline(arcade.rect.XYWH(self.confirmbtn_x, self.confirmbtn_y, self.confirmbtn_w, self.confirmbtn_h),outline_color,border_width=outline_thick)
            arcade.draw_rect_filled(arcade.rect.XYWH(self.renamebtn_x, self.renamebtn_y, self.renamebtn_w, self.renamebtn_h), renamebtn_color)
            arcade.draw_rect_outline(arcade.rect.XYWH(self.renamebtn_x, self.renamebtn_y, self.renamebtn_w, self.renamebtn_h),outline_color,border_width=outline_thick)
            arcade.draw_rect_filled(arcade.rect.XYWH(self.cancelbtn_x, self.cancelbtn_y, self.cancelbtn_w, self.cancelbtn_h), cancelbtn_color)
            arcade.draw_rect_outline(arcade.rect.XYWH(self.cancelbtn_x, self.cancelbtn_y, self.cancelbtn_w, self.cancelbtn_h),outline_color,border_width=outline_thick)
            arcade.draw_rect_filled(arcade.rect.XYWH(self.deletebtn_x, self.deletebtn_y, self.deletebtn_w, self.deletebtn_h), deletebtn_color)
            arcade.draw_rect_outline(arcade.rect.XYWH(self.deletebtn_x, self.deletebtn_y, self.deletebtn_w, self.deletebtn_h),outline_color,border_width=outline_thick)

            arcade.draw_text("OK", x=self.confirmbtn_x, y=self.confirmbtn_y, color=arcade.color.WHITE, font_size=20, bold=True, anchor_x="center", anchor_y="center")
            arcade.draw_text("Rename", x=self.renamebtn_x, y=self.renamebtn_y, color=arcade.color.WHITE, font_size=20, bold=True, anchor_x="center", anchor_y="center")
            arcade.draw_text("Cancel", x=self.cancelbtn_x, y=self.cancelbtn_y, color=arcade.color.WHITE, font_size=20, bold=True, anchor_x="center", anchor_y="center")
            arcade.draw_text("Delete", x=self.deletebtn_x, y=self.deletebtn_y, color=arcade.color.WHITE, font_size=20, bold=True, anchor_x="center", anchor_y="center")




        elif self.state == "TYPING" or self.state == "ALERT_BANNED":
            title_text = "Rename Your Name" if self.is_renaming else "Input Your Name"
            arcade.draw_text(title_text, self.window.width  // 2, self.window.height // 2 + 100, (216, 178, 92), font_size=22, bold=True, anchor_x="center")
            
            # PERBAIKAN: Lakukan sensor secara visual saat digambar ke layar
            display_text = self.raw_typing
            for word in banword:
                if word.upper() in display_text:
                    display_text = display_text.replace(word.upper(), "#" * len(word))

            if display_text == "":
                display_text = "[ Ketik di sini... ]"

            arcade.draw_text(display_text, x=self.window.width  // 2, y=self.window.height // 2, color=arcade.color.WHITE, font_size=28, bold=True, anchor_x="center", anchor_y="center")

            if not self.user_list:
                self.confirmbtn_x = self.window.width  // 2
                self.confirmbtn_y = self.window.height // 2 - 140
                confirmbtn_color = (78, 62, 38) if self.confirmbtn_hovered else (30, 28, 24)
                arcade.draw_rect_filled(arcade.rect.XYWH(self.confirmbtn_x, self.confirmbtn_y, self.confirmbtn_w, self.confirmbtn_h), confirmbtn_color)
                arcade.draw_rect_outline(arcade.rect.XYWH(self.confirmbtn_x, self.confirmbtn_y, self.confirmbtn_w, self.confirmbtn_h), (255, 255, 255), border_width=3)
                arcade.draw_text("OK", x=self.confirmbtn_x, y=self.confirmbtn_y, color=arcade.color.WHITE, font_size=20, bold=True, anchor_x="center", anchor_y="center")
            else:
                self.confirmbtn_x = self.window.width  // 2 - 110
                self.confirmbtn_y = self.window.height // 2 - 140
                self.cancelbtn_x = self.window.width  // 2 + 110
                self.cancelbtn_y = self.window.height // 2 - 140

                confirmbtn_color = (78, 62, 38) if self.confirmbtn_hovered else (30, 28, 24)
                cancelbtn_color  = (78, 62, 38) if self.cancelbtn_hovered else (30, 28, 24)

                arcade.draw_rect_filled(arcade.rect.XYWH(self.confirmbtn_x, self.confirmbtn_y, self.confirmbtn_w, self.confirmbtn_h), confirmbtn_color)
                arcade.draw_rect_filled(arcade.rect.XYWH(self.cancelbtn_x, self.cancelbtn_y, self.cancelbtn_w, self.cancelbtn_h), cancelbtn_color)
                arcade.draw_rect_outline(arcade.rect.XYWH(self.confirmbtn_x, self.confirmbtn_y, self.confirmbtn_w, self.confirmbtn_h), (255, 255, 255), border_width=3)
                arcade.draw_rect_outline(arcade.rect.XYWH(self.cancelbtn_x, self.cancelbtn_y, self.cancelbtn_w, self.cancelbtn_h), (255, 255, 255), border_width=3)

                arcade.draw_text("OK", x=self.confirmbtn_x, y=self.confirmbtn_y, color=arcade.color.WHITE, font_size=20, bold=True, anchor_x="center", anchor_y="center")
                arcade.draw_text("Cancel", x=self.cancelbtn_x, y=self.cancelbtn_y, color=arcade.color.WHITE, font_size=20, bold=True, anchor_x="center", anchor_y="center")
 


        if self.state == "CONFIRM_DELETE":
            arcade.draw_rect_filled(arcade.rect.XYWH(self.window.width  // 2, self.window.height // 2, WIDTH, HEIGHT), (0, 0, 0, 150))
            arcade.draw_rect_filled(arcade.rect.XYWH(self.window.width  // 2, self.window.height // 2, 420, 180), (30, 30, 45))
            
            arcade.draw_text("APAKAH KAMU INGIN", self.window.width  // 2, self.window.height // 2 + 45, arcade.color.WHITE, font_size=16, bold=True, anchor_x="center")
            arcade.draw_text("MENGHAPUS USERNAME INI?", self.window.width  // 2, self.window.height // 2 + 20, (216, 178, 92), font_size=16, bold=True, anchor_x="center")
            
            pk_color = (200, 50, 50) if self.pop_ok_hovered else (150, 30, 30)
            arcade.draw_rect_filled(arcade.rect.XYWH(self.pop_ok_x, self.pop_ok_y, self.pop_ok_w, self.pop_ok_h), pk_color)
            arcade.draw_text("OK", self.pop_ok_x, self.pop_ok_y, arcade.color.WHITE, font_size=16, bold=True, anchor_x="center", anchor_y="center")
            
            pc_color = (100, 100, 100) if self.pop_cancel_hovered else (70, 70, 70)
            arcade.draw_rect_filled(arcade.rect.XYWH(self.pop_cancel_x, self.pop_cancel_y, self.pop_cancel_w, self.pop_cancel_h), pc_color)
            arcade.draw_text("CANCEL", self.pop_cancel_x, self.pop_cancel_y, arcade.color.WHITE, font_size=16, bold=True, anchor_x="center", anchor_y="center")


        elif self.state == "ALERT_BANNED":
            arcade.draw_rect_filled(arcade.rect.XYWH(self.window.width  // 2, self.window.height // 2, WIDTH, HEIGHT), (0, 0, 0, 180))
            arcade.draw_rect_filled(arcade.rect.XYWH(self.window.width  // 2, self.window.height // 2, 420, 180), (35, 25, 25))            
            arcade.draw_text("NAMA TIDAK DIPERBOLEHKAN!", self.window.width  // 2, self.window.height // 2 + 30, arcade.color.RED, font_size=16, bold=True, anchor_x="center")
            
            a_ok_color = (200, 50, 50) if self.alert_ok_hovered else (140, 30, 30)
            arcade.draw_rect_filled(arcade.rect.XYWH(self.alert_ok_x, self.alert_ok_y, self.alert_ok_w, self.alert_ok_h), a_ok_color)
            arcade.draw_text("OK", self.alert_ok_x, self.alert_ok_y, arcade.color.WHITE, font_size=16, bold=True, anchor_x="center", anchor_y="center")







    def _confirm_button(self, x, y):
        return (self.confirmbtn_x - self.confirmbtn_w/2 <= x <= self.confirmbtn_x + self.confirmbtn_w/2 and self.confirmbtn_y - self.confirmbtn_h/2 <= y <= self.confirmbtn_y + self.confirmbtn_h/2)
    def _rename_button(self, x, y):
        return (self.renamebtn_x - self.renamebtn_w/2 <= x <= self.renamebtn_x + self.renamebtn_w/2 and self.renamebtn_y - self.renamebtn_h/2 <= y <= self.renamebtn_y + self.renamebtn_h/2)
    def _delete_button(self, x, y):
        return (self.deletebtn_x - self.deletebtn_w/2 <= x <= self.deletebtn_x + self.deletebtn_w/2 and self.deletebtn_y - self.deletebtn_h/2 <= y <= self.deletebtn_y + self.deletebtn_h/2)
    def _cancel_button(self, x, y):
        return (self.cancelbtn_x - self.cancelbtn_w/2 <= x <= self.cancelbtn_x + self.cancelbtn_w/2 and self.cancelbtn_y - self.cancelbtn_h/2 <= y <= self.cancelbtn_y + self.cancelbtn_h/2)
    def _create_button(self, x, y):
        if self.createbtn_y == -999: return False
        return (self.createbtn_x - self.createbtn_w/2 <= x <= self.createbtn_x + self.createbtn_w/2 and self.createbtn_y - self.createbtn_h/2 <= y <= self.createbtn_y + self.createbtn_h/2)

    def _pop_ok_button(self, x, y):
        return (self.pop_ok_x - self.pop_ok_w/2 <= x <= self.pop_ok_x + self.pop_ok_w/2 and self.pop_ok_y - self.pop_ok_h/2 <= y <= self.pop_ok_y + self.pop_ok_h/2)
    def _pop_cancel_button(self, x, y):
        return (self.pop_cancel_x - self.pop_cancel_w/2 <= x <= self.pop_cancel_x + self.pop_cancel_w/2 and self.pop_cancel_y - self.pop_cancel_h/2 <= y <= self.pop_cancel_y + self.pop_cancel_h/2)

    def _alert_ok_button(self, x, y):
        return (self.alert_ok_x - self.alert_ok_w/2 <= x <= self.alert_ok_x + self.alert_ok_w/2 and self.alert_ok_y - self.alert_ok_h/2 <= y <= self.alert_ok_y + self.alert_ok_h/2)







    def _check_name_row_hover(self, x, y):
        if self.state == "SELECT":
            box_left = self.window.width  // 2 - 190
            box_right = self.window.width  // 2 + 190
            for i in range(min(len(self.user_list), 4)):
                row_y = self.start_y - (i * self.row_height)
                if box_left <= x <= box_right and (row_y - 15) <= y <= (row_y + 15):
                    actual_idx = self.scroll_offset + i
                    if actual_idx < len(self.user_list):
                        return actual_idx
        return None
    





    def on_mouse_motion(self, x, y, dx, dy):
        if self.state == "CONFIRM_DELETE":
            self.pop_ok_hovered = self._pop_ok_button(x, y)
            self.pop_cancel_hovered = self._pop_cancel_button(x, y)
            return

        if self.state == "ALERT_BANNED":
            self.alert_ok_hovered = self._alert_ok_button(x, y)
            return

        self.confirmbtn_hovered = self._confirm_button(x, y) 
        self.cancelbtn_hovered = self._cancel_button(x, y)

        if self.state == "SELECT":
            self.renamebtn_hovered = self._rename_button(x, y)  
            self.deletebtn_hovered = self._delete_button(x, y)
            self.createbtn_hovered = self._create_button(x, y)






    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        total_items = len(self.user_list) + 1
        if self.state == "SELECT" and total_items > 4:
            if scroll_y > 0:
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif scroll_y < 0:
                self.scroll_offset = min(total_items - 4, self.scroll_offset + 1)





    def on_text(self, text):
        if self.state == "TYPING" and len(self.raw_typing) < 12:
            if text.isalnum() or text == " ":
                # PERBAIKAN: Masukkan karakter ke raw_typing (bukan player_name yang langsung disensor)
                self.raw_typing += text.upper()





    def on_key_press(self, key, modifiers):
        if self.state == "ALERT_BANNED":
            if key == arcade.key.ENTER:
                self.state = "TYPING"
                self.raw_typing = ""
            return




        if self.state == "TYPING":
            if key == arcade.key.BACKSPACE:
                # PERBAIKAN: Sekarang backspace akan menghapus huruf asli secara akurat!
                self.raw_typing = self.raw_typing[:-1]
                return 
            elif key == arcade.key.ENTER and self.raw_typing.strip() != "":
                
                # Cek apakah ketikan mengandung kata terlarang
                has_banned = False
                for word in banword:
                    if word.upper() in self.raw_typing:
                        has_banned = True
                        break

                if has_banned:
                    self.state = "ALERT_BANNED"
                    return
                
                self.player_name = self.raw_typing
                self.save_active_user_to_top(self.player_name)
                self.go_to_main_menu()
                return



        elif self.state == "SELECT" and self.user_list:
            if key == arcade.key.UP:
                self.selected_index = (self.selected_index - 1) % len(self.user_list)
                if self.selected_index < self.scroll_offset:
                    self.scroll_offset = self.selected_index
                elif self.selected_index >= self.scroll_offset + 4:
                    self.scroll_offset = len(self.user_list) - 3
            elif key == arcade.key.DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.user_list)
                if self.selected_index >= self.scroll_offset + 4:
                    self.scroll_offset = self.selected_index - 3
                elif self.selected_index < self.scroll_offset:
                    self.scroll_offset = 0
            elif key == arcade.key.ENTER:
                nama_terpilih = self.user_list[self.selected_index]
                if "#" in nama_terpilih:
                    return
                self.save_active_user_to_top(nama_terpilih)
                self.go_to_main_menu() 







    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:

            if self.state == "CONFIRM_DELETE":
                self._play_click_sfx()
                if self._pop_ok_button(x, y):
                    nama_mau_dihapus = self.user_list[self.selected_index]
                    self.delete_user_from_csv(nama_mau_dihapus)
                elif self._pop_cancel_button(x, y):
                    self.state = "SELECT"
                return

            if self.state == "ALERT_BANNED":
                self._play_click_sfx()
                if self._alert_ok_button(x, y):
                    self.state = "TYPING"
                    self.raw_typing = "" 
                return





            if self.state == "TYPING":
                if self._confirm_button(x, y) and self.raw_typing.strip() != "":
                    has_banned = False
                    self._play_click_sfx()
                    for word in banword:
                        if word.upper() in self.raw_typing:
                            has_banned = True
                            break

                    if has_banned:
                        self._play_click_sfx()
                        self.state = "ALERT_BANNED"
                        return
                    
                    self.player_name = self.raw_typing
                    self.save_active_user_to_top(self.player_name)
                    self.go_to_main_menu()
                
                elif self._cancel_button(x, y):
                    self._play_click_sfx()
                    if self.user_list:
                        self.state = "SELECT"
                        self.is_renaming = False
                    else:
                        self.go_to_main_menu()
                return





            if self.state == "SELECT":
                self._play_click_sfx()
                row_clicked = self._check_name_row_hover(x, y)
                if row_clicked is not None:
                    self.selected_index = row_clicked
                    return
                
                if self._confirm_button(x, y) and self.user_list:
                    self._play_click_sfx()
                    nama_terpilih = self.user_list[self.selected_index]
                    if "#" in nama_terpilih:
                        return
                    self.save_active_user_to_top(nama_terpilih)
                    self.go_to_main_menu()

                elif self._create_button(x, y):
                    self._play_click_sfx()
                    self.raw_typing = ""
                    self.state = "TYPING"
                    self.is_renaming = False

                elif self._rename_button(x, y) and self.user_list:
                    self._play_click_sfx()
                    self.is_renaming = True
                    self.old_name_to_rename = self.user_list[self.selected_index]
                    if "#" in self.old_name_to_rename:
                        self.raw_typing = ""
                    else:
                        self.raw_typing = self.old_name_to_rename
                    self.state = "TYPING"

                elif self._delete_button(x, y) and self.user_list:
                    self._play_click_sfx()
                    self.state = "CONFIRM_DELETE"

                elif self._cancel_button(x, y):
                    self._play_click_sfx()
                    self.go_to_main_menu()
    
    def go_to_main_menu(self):
        from menu import MenuView
        menu_view = MenuView()
        self.window.show_view(menu_view)