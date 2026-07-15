# audio_registry.py
#
# Registry pusat untuk semua sfx yang LOOPING/berkelanjutan (ambient
# 'outside', bubble sustained, jumpscare dangerous fish, suck sound
# player, dll) — supaya SEMUANYA bisa di-pause/resume/stop sekaligus
# dari satu tempat, terutama dipanggil dari pause menu (pause.py):
#
#   - Saat masuk Pause          -> pause_all()   (player TETAP terdaftar)
#   - Saat Resume dari Pause    -> resume_all()  (lanjutkan dari titik pause)
#   - Saat Exit/Restart dari Pause -> stop_all() (benar-benar berhenti & dibuang)
#
# Modul-modul lain (outside.py, dangerous_fish.py, main_fish.py, dst)
# WAJIB register() setiap kali mereka mulai sebuah loop sound, dan
# unregister() setiap kali mereka menghentikannya sendiri secara normal
# (supaya registry tidak menumpuk referensi ke player yang sudah mati).

import arcade

_active_players = []   # list of pyglet media.Player yang sedang looping


def register(player):
    """Daftarkan player looping baru. Panggil TEPAT SETELAH
    arcade.play_sound(..., loop=True) berhasil."""
    if player is not None and player not in _active_players:
        _active_players.append(player)


def unregister(player):
    """Lepas player dari registry — panggil SEBELUM/SESUDAH kamu
    menghentikan sound itu sendiri secara normal (misal ambient outside
    berhenti karena player menjauh dari permukaan)."""
    if player in _active_players:
        _active_players.remove(player)


def pause_all():
    """Pause SEMUA sfx looping yang terdaftar. Dipanggil saat masuk ke
    pause menu. Player TETAP ada di registry supaya resume_all() bisa
    melanjutkannya persis dari titik berhenti."""
    for p in list(_active_players):
        try:
            p.pause()
        except Exception:
            pass


def resume_all():
    """Lanjutkan lagi semua sfx looping yang sebelumnya di-pause_all().
    Dipanggil saat player klik RESUME di pause menu."""
    for p in list(_active_players):
        try:
            p.play()
        except Exception:
            pass


def stop_all():
    """Hentikan & buang SEMUA sfx looping sepenuhnya (bukan cuma pause).
    Dipanggil saat EXIT ke main menu atau RESTART dari pause menu, supaya
    tidak ada sfx ambient/loop yang nyangkut kebawa ke scene berikutnya."""
    for p in list(_active_players):
        try:
            arcade.stop_sound(p)
        except Exception:
            pass
    _active_players.clear()