import pygame
import time
import sys
import os


def resource_path(relative_path: str) -> str:
    """Lấy đường dẫn đúng cho file khi chạy .py hoặc .exe (PyInstaller)."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class AlertManager:
    def __init__(self, sound_file="alert.mp3"):
        self.status_level = 0
        self.state = "SAFE"
        self.danger_limit = 15.0
        self.cooldown_timer = 0
        self.cooldown_duration = 10.0
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        try:
            sound_path = resource_path(sound_file)
            self.sound = pygame.mixer.Sound(sound_path)
            self.sound.set_volume(1.0)
        except Exception as e:
            print("Error loading sound:", e)
            self.sound = None
        self.last_update = time.time()
    def set_danger_limit(self, seconds):
        self.danger_limit = float(seconds)
    def update(self, motion_detected):
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time
        if motion_detected:
            self.status_level += dt
            self.cooldown_timer = self.cooldown_duration
        else:
            if self.status_level >= self.danger_limit and self.cooldown_timer > 0:
                self.cooldown_timer -= dt
                self.status_level = self.danger_limit + 1
            else:
                self.status_level -= dt * 2
        self.status_level = max(0, min(self.status_level, self.danger_limit + 2))

        limit = self.danger_limit
        if self.status_level < (limit * 0.33):
            self.state = "SAFE"
            color_ui = "#28a745"
        elif self.status_level < (limit * 0.66):
            self.state = "WARNING"
            color_ui = "#ffc107"
        else:
            self.state = "DANGER"
            color_ui = "#dc3545"
        if self.state == "WARNING" or self.state == "DANGER":
            if self.sound and not pygame.mixer.get_busy():
                self.sound.play()
        else:
            if self.sound:
                self.sound.stop()

        return self.state, self.status_level, color_ui

    def reset(self):
        self.status_level = 0
        self.state = "SAFE"
        self.cooldown_timer = 0
        self.last_update = time.time()
        if self.sound: self.sound.stop()
def demo_warning_only():
    am = AlertManager("alert.mp3")
    am.set_danger_limit(9)
    print("=== DEMO WARNING ===")
    print("motion=True trong 4 giây để giữ WARNING\n")
    for i in range(20):
        state, level, ui = am.update(True)
        print(f"{i:02d} | motion=True  | state={state:<8} | level={level:5.2f}")
        time.sleep(0.2)
    for i in range(5):
        state, level, ui = am.update(False)
        print(f"{i+20:02d} | motion=False | state={state:<8} | level={level:5.2f}")
        time.sleep(0.2)

if __name__ == "__main__":
    demo_warning_only()