import time
import threading
import pygame
import os
from datetime import datetime


class AlertManager:
    def __init__(self):
        pygame.mixer.init()

        # Cấu hình file âm thanh và cooldown
        self.config = {
            "light": {"file": "light.mp3", "cooldown": 3},
            "medium": {"file": "medium.mp3", "cooldown": 3},
            "strong": {"file": "strong.mp3", "cooldown": 3}
        }

        # Tạo file giả để test (Xóa đoạn này khi chạy thật)
        for key, val in self.config.items():
            if not os.path.exists(val["file"]):
                with open(val["file"], 'w') as f: pass

        # Quản lý trạng thái
        self.last_play = {"light": 0, "medium": 0, "strong": 0}
        self.loop_flags = {"light": False, "medium": False, "strong": False}
        self.threads = {"light": None, "medium": None, "strong": None}

        # Cấu hình Log
        self.log_file = "alert_history.log"
        self.log_lock = threading.Lock()

    # ============================================================
    # KHU VỰC 1: 3 HÀM BÁO ĐỘNG RIÊNG (API CHÍNH)
    # ============================================================

    # --- LIGHT ---
    def alert_light(self, loop=True):
        """Kích hoạt báo động mức NHẸ. Mặc định là lặp (loop=True)."""
        self._trigger("light", loop)

    def stop_light(self):
        """Dừng báo động mức NHẸ."""
        self._stop("light")

    # --- MEDIUM ---
    def alert_medium(self, loop=True):
        """Kích hoạt báo động mức TRUNG BÌNH."""
        self._trigger("medium", loop)

    def stop_medium(self):
        """Dừng báo động mức TRUNG BÌNH."""
        self._stop("medium")

    # --- STRONG ---
    def alert_strong(self, loop=True):
        """Kích hoạt báo động mức MẠNH."""
        self._trigger("strong", loop)

    def stop_strong(self):
        """Dừng báo động mức MẠNH."""
        self._stop("strong")

    def stop_all(self):
        """Dừng toàn bộ các báo động đang kêu."""
        self.stop_light()
        self.stop_medium()
        self.stop_strong()

    # ============================================================
    # KHU VỰC 2: LOGIC XỬ LÝ CHUNG (INTERNAL)
    # ============================================================
    def _trigger(self, level, loop):
        """Hàm xử lý trung gian: quyết định chạy 1 lần hay lặp"""
        if loop:
            self._start_loop_internal(level)
        else:
            self._play_once_internal(level)

    def _stop(self, level):
        """Dừng cờ lặp"""
        if self.loop_flags[level]:
            self.loop_flags[level] = False
            self._write_log(level, "STOPPED (Đã dừng)")

    # --- Logic chạy 1 lần ---
    def _play_once_internal(self, level):
        now = time.time()
        cooldown = self.config[level]["cooldown"]

        if now - self.last_play[level] < cooldown:
            return  # Chưa hết cooldown

        self.last_play[level] = now
        self._write_log(level, "Triggered ONCE (1 lần)")
        threading.Thread(target=self._play_sound_thread, args=(level,)).start()

    # --- Logic chạy lặp (Loop) ---
    def _start_loop_internal(self, level):
        # Nếu đang chạy rồi thì thôi không chạy đè
        if self.threads[level] and self.threads[level].is_alive():
            return

        self.loop_flags[level] = True
        self._write_log(level, "Loop STARTED (Bắt đầu lặp)")

        t = threading.Thread(target=self._loop_thread_func, args=(level,))
        self.threads[level] = t
        t.start()

    # --- Thread function cho Loop ---
    def _loop_thread_func(self, level):
        sound_path = self.config[level]["file"]
        cooldown = self.config[level]["cooldown"]

        while self.loop_flags[level]:
            now = time.time()
            if now - self.last_play[level] >= cooldown:
                self.last_play[level] = now
                self._play_sound_file(sound_path)
            time.sleep(0.1)

    # --- Thread function cho One Shot ---
    def _play_sound_thread(self, level):
        self._play_sound_file(self.config[level]["file"])

    # --- Hàm phát nhạc thực tế ---
    def _play_sound_file(self, path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        except Exception as e:
            print(f"Audio Error: {e}")

    # --- Hàm Ghi Log ---
    def _write_log(self, level, msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] [{level.upper()}] {msg}\n"
        print(f"-> LOG: {line.strip()}")

        with self.log_lock:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(line)
            except Exception as e:
                print(f"Log Error: {e}")


# ============================================================
# CHẠY THỬ (USAGE EXAMPLE)
# ============================================================
if __name__ == "__main__":
    system = AlertManager()

    print("--- TEST: Gọi hàm riêng biệt ---")

    # 1. Gọi Light (chỉ 1 lần)
    print("\n>>> Test Light (1 lần)")
    system.alert_light(loop=False)
    time.sleep(2)

    # 2. Gọi Medium (Lặp)
    print("\n>>> Test Medium (Lặp 5s)")
    system.alert_medium()  # Mặc định loop=True
    time.sleep(5)
    system.stop_medium()

    # 3. Gọi Strong (Lặp)
    print("\n>>> Test Strong (Lặp 5s)")
    system.alert_strong(loop=True)
    time.sleep(5)
    # system.stop_strong() -> Thử dùng stop_all thay thế

    print("\n>>> Dừng tất cả")
    system.stop_all()