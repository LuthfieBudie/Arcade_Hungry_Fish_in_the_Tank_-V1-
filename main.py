import arcade
import os
import csv 
from name import name
from menu import MenuView

WIDTH  = 800
HEIGHT = 560
TITLE  = "Feeding Frenzy"
FILE_NAME = "username.csv"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_PATH = os.path.join(BASE_DIR, "assets", "audio", "songs", "menu", "Kelp Panic.mp3")


def main():
    try:
        from setting import load_settings
        _cfg = load_settings()
        _mode = _cfg.get("display_mode", "windowed")  
    except Exception:
        _mode = "windowed"

    if _mode == "fixed":
        _init_w, _init_h = 1280, 720 
    else:
        _init_w, _init_h = 800, 560  

    window = arcade.Window(_init_w, _init_h, TITLE) 

    window.current_music  = None
    window.current_player = None

    if _mode == "fullscreen":
        try:
            window.set_fullscreen(True)
        except Exception as e:
            print(f"Gagal set fullscreen: {e}")
     

    has_name = False
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, mode='r', newline='', encoding='utf-8') as file:
            reader = list(csv.reader(file))
            if len(reader) > 1 and reader [1][0].strip() != "":
                has_name = True

    if has_name:
        first_view = MenuView()  
    else:
        first_view = name()
    
    window.show_view(first_view)
    arcade.run()


if __name__ == "__main__":
    main()