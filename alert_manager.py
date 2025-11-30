import pygame
import time


class AlertManager:
    def __init__(self, sound_file="alert.mp3"):
        self.status_level = 0
        self.state = "SAFE"
        self.danger_limit = 15.0

        # Biến đếm ngược ghi hình thêm 10s
        self.cooldown_timer = 0
        self.cooldown_duration = 10.0

        if not pygame.mixer.get_init(): pygame.mixer.init()
        try:
            self.sound = pygame.mixer.Sound(sound_file)
            self.sound.set_volume(1.0)
        except:
            self.sound = None
        self.last_update = time.time()

    def set_danger_limit(self, seconds):
        self.danger_limit = float(seconds)

    def update(self, motion_detected):
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time

        if motion_detected:
            # Có chuyển động -> Tăng mức độ
            self.status_level += dt
            # Reset đếm ngược
            self.cooldown_timer = self.cooldown_duration
        else:
            # Không có chuyển động
            # Logic Cool-down: Chỉ kích hoạt nếu ĐANG Ở MỨC ĐỎ (Đang ghi hình)
            if self.status_level >= self.danger_limit and self.cooldown_timer > 0:
                self.cooldown_timer -= dt
                # Giữ status_level ở đỉnh để duy trì ghi hình
                self.status_level = self.danger_limit + 1
            else:
                # Nếu chưa tới mức đỏ hoặc đã hết giờ cool-down -> Giảm dần
                self.status_level -= dt * 2

                # Kẹp giá trị
        self.status_level = max(0, min(self.status_level, self.danger_limit + 2))

        # --- PHÂN LOẠI TRẠNG THÁI (5-5-5) ---
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

        # --- SỬA ĐỔI: PHÁT TIẾNG NGAY TỪ LÚC VÀNG (WARNING) ---
        # Điều kiện: Là WARNING hoặc DANGER đều hú còi
        if self.state == "WARNING" or self.state == "DANGER":
            if self.sound and not pygame.mixer.get_busy():
                self.sound.play()
        else:
            # Chỉ tắt tiếng khi về SAFE (Xanh)
            if self.sound:
                self.sound.stop()

        return self.state, self.status_level, color_ui

    def reset(self):
        self.status_level = 0
        self.state = "SAFE"
        self.cooldown_timer = 0
        self.last_update = time.time()
        if self.sound: self.sound.stop()