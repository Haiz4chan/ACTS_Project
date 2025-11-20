import time
import threading
import pygame
import os
from datetime import datetime


class AlertManager:
    def __init__(self):
        pygame.mixer.init()

        # ============================
        # CẤU HÌNH ÂM THANH
        # ============================
        self.config = {
            "light": {"file": "light.mp3"},
            "strong": {"file": "strong.mp3"}
        }

        # Tạo file rỗng nếu chưa có
        for key, val in self.config.items():
            if not os.path.exists(val["file"]):
                with open(val["file"], 'w') as f:
                    pass

        # ============================
        # TRẠNG THÁI HỆ THỐNG
        # ============================
        self.loop_flags = {
            "light": False,
            "strong": False
        }

        self.log_file = "alert_history.log"
        self.log_lock = threading.Lock()

    # =====================================================
    #                       LIGHT ALERT
    # =====================================================
    def alert_light(self):
        """Phát 1 lần"""
        self.loop_flags["light"] = True
        self._write_log("light", "PLAY ONCE")

        try:
            pygame.mixer.music.load(self.config["light"]["file"])
            pygame.mixer.music.play()
        except Exception as e:
            print("[LIGHT ERROR]", e)

    def stop_light(self):
        self.loop_flags["light"] = False
        self._stop_audio()
        self._write_log("light", "STOP")

    # =====================================================
    #                    STRONG ALERT (PHÁT 1 LẦN)
    # =====================================================
    def alert_strong(self):
        """Báo động mạnh – phát 1 lần giống light"""
        self.loop_flags["strong"] = True
        self._write_log("strong", "PLAY ONCE")

        try:
            pygame.mixer.music.load(self.config["strong"]["file"])
            pygame.mixer.music.play()
        except Exception as e:
            print("[STRONG ERROR]", e)

    def stop_strong(self):
        self.loop_flags["strong"] = False
        try:
            pygame.mixer.music.stop()
        except:
            pass
        self._write_log("strong", "STOP")

    # =====================================================
    #                       STOP ALL
    # =====================================================
    def stop_all(self):
        self.loop_flags["light"] = False
        self.loop_flags["strong"] = False

        pygame.mixer.stop()

        self._write_log("ALL", "STOP ALL")

    # =====================================================
    #                        UTILITY
    # =====================================================
    def _stop_audio(self):
        try:
            pygame.mixer.music.stop()
        except:
            pass

    def _write_log(self, level, msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] [{level.upper()}] {msg}\n"
        print(line.strip())

        with self.log_lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line)


# =====================================================
#                     DEMO CHẠY THỬ
# =====================================================
if __name__ == "__main__":
    system = AlertManager()

    print("\n>>> LIGHT (1 lần)")
    system.alert_light()
    time.sleep(2)

    print("\n>>> STRONG (1 lần)")
    system.alert_strong()
    time.sleep(5)

    print("\n>>> STOP ALL")
    system.stop_all()
