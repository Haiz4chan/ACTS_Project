import tkinter as tk
import cv2
import time
import threading

# --- IMPORT CÁC MODULE CỦA NHÓM ---
# 1. Giao diện (Sơn) - File: app_gui.py
from app_gui import AppGUI

# 2. Phát hiện chuyển động (Huy) - File: MotionDetector.py
# Lưu ý: Tên file của Huy viết hoa chữ cái đầu
from MotionDetector import MotionDetector

# 3. Cảnh báo (Tuấn) - File: alert_manager.py
from alert_manager import AlertManager

# 4. Ghi hình (Doanh) - File: videorecorder.py
from videorecorder import VideoRecorder


class SecurityApp:
    def __init__(self, root):
        self.root = root
        self.running = False

        # --- KHỞI TẠO CÁC MODULE ---

        # 1. CORE: Phát hiện chuyển động
        # (Huy thiết lập min_area mặc định là 1500, ta có thể giữ nguyên hoặc chỉnh)
        self.detector = MotionDetector(min_area=2000)

        # Lấy kích thước camera để cấu hình cho Recorder
        # Chúng ta mở thử camera 1 lần để lấy thông số
        temp_cap = cv2.VideoCapture(0)
        if temp_cap.isOpened():
            w = int(temp_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(temp_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            temp_cap.release()
        else:
            w, h = 640, 480  # Giá trị dự phòng

        # 2. RECORDER: Ghi hình
        self.recorder = VideoRecorder(width=w, height=h)

        # 3. ALERT: Cảnh báo
        self.alert_manager = AlertManager()

        # 4. GUI: Giao diện
        self.gui = AppGUI(root)

        # GHI ĐÈ (Override) hành động cho nút bấm của Sơn
        # Để khi bấm nút trên giao diện Sơn, nó chạy logic của Main
        self.gui.start_button.config(command=self.start_app)
        self.gui.stop_button.config(command=self.stop_app)

        # Khởi tạo camera chính cho Main dùng
        self.cap = None

    def start_app(self):
        if self.running:
            return
        print("--- HỆ THỐNG BẮT ĐẦU ---")
        self.running = True

        # Mở camera
        self.cap = cv2.VideoCapture(0)

        # Gọi hàm start của giao diện Sơn (để đổi màu nút, update trạng thái)
        self.gui.start_system()

        # Bắt đầu vòng lặp xử lý chính
        self.process_loop()

    def stop_app(self):
        if not self.running:
            return
        print("--- HỆ THỐNG DỪNG ---")
        self.running = False

        # Dừng camera
        if self.cap:
            self.cap.release()

        # Gọi hàm stop của các module con
        self.gui.stop_system()
        self.recorder.stop_recording()
        self.alert_manager.stop_all()

    def process_loop(self):
        """Vòng lặp chính: Chạy liên tục để xử lý từng khung hình"""
        if not self.running:
            return

        # 1. Đọc hình ảnh từ Camera
        ret, frame = self.cap.read()
        if not ret:
            # Nếu lỗi camera, thử lại sau 10ms
            self.root.after(10, self.process_loop)
            return

        frame = cv2.flip(frame, 1)  # Lật gương cho tự nhiên

        # 2. Phát hiện chuyển động (Dùng code của Huy)
        # Hàm detect của Huy cần 2 tham số: frame và roi_rect.
        # Ta tạo roi_rect full màn hình
        h, w, _ = frame.shape
        full_screen_roi = (0, 0, w, h)

        # Gọi hàm của Huy -> Trả về True/False
        is_motion = self.detector.detect(frame, full_screen_roi)

        # 3. Xử lý Logic hệ thống
        if is_motion:
            # A. Có chuyển động!

            # -> Kêu tít tít (Code Tuấn)
            # (Dùng medium alert, không lặp để tránh ồn liên tục)
            self.alert_manager.alert_medium(loop=False)

            # -> Ghi hình (Code Doanh)
            self.recorder.start_recording()

            # -> Cập nhật GUI màu đỏ (Code Sơn)
            self.gui._set_status("red", "PHÁT HIỆN CHUYỂN ĐỘNG!")

        elif self.recorder.is_recording:
            # B. Không có chuyển động, nhưng đang trong 3 phút ghi hình
            self.gui._set_status("yellow", "Đang ghi hình sự kiện (3 phút)...")

        else:
            # C. Bình thường
            self.gui._set_status("green", "Hệ thống an toàn.")

        # 4. Vẽ khung chữ nhật lên hình (Lấy tọa độ từ Huy)
        for gx1, gy1, gx2, gy2 in self.detector.last_boxes:
            cv2.rectangle(frame, (gx1, gy1), (gx2, gy2), (0, 0, 255), 2)
            cv2.putText(frame, "MOTION", (gx1, gy1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # 5. Cập nhật hình ảnh lên giao diện (Dùng code Sơn)
        self.gui.update_frame(frame)

        # 6. Lặp lại (Gọi lại hàm này sau 15ms -> ~60 FPS)
        self.root.after(15, self.process_loop)

    def __del__(self):
        """Dọn dẹp khi tắt hẳn ứng dụng"""
        if self.cap and self.cap.isOpened():
            self.cap.release()


if __name__ == "__main__":
    # Khởi tạo cửa sổ chính
    root = tk.Tk()
    # Khởi tạo ứng dụng
    app = SecurityApp(root)
    # Chạy
    root.mainloop()