import cv2
import time
import datetime
import os
import threading

"""
@author Phan Cong Doanh
"""

class VideoRecorder:

    def __init__(self, device=0, save_path="videos", width=640, height=480, fps=20.0):
        self.device = device
        self.save_path = save_path
        self.size = (width, height)
        self.fps = fps
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')

        # --- Trạng thái ---
        self.cap = None
        self.out = None
        self.is_recording = False
        self.current_filename = None

        # --- Threading ---
        self.worker_thread = None  # Luồng để chạy vòng lặp ghi
        self.lock = threading.Lock()  # Khóa để bảo vệ các biến (tránh race condition)

        # Đảm bảo thư mục
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
            print(f'Đã tạo thư mục: {self.save_path}')

        # Khởi động webcam
        self.cap = cv2.VideoCapture(self.device)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.size[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.size[1])

        if not self.cap.isOpened():
            raise IOError(f'Không thể mở webcam (device {self.device})')

    def generate_filename(self):
        now = datetime.datetime.now()
        filename = now.strftime("%Y_%m_%d_%H_%M_%S") + ".avi"
        full_path = os.path.join(self.save_path, filename)
        return full_path

    # --- HÀM MỚI (chạy ở luồng riêng) ---
    def _record_loop(self):
        """
        Vòng lặp ghi video, chạy trên một luồng riêng.
        Nó sẽ liên tục chạy cho đến khi self.is_recording = False.
        """
        try:
            while True:
                # Kiểm tra cờ hiệu
                with self.lock:
                    if not self.is_recording:
                        break  # Thoát vòng lặp

                # Đọc frame
                ret, frame = self.cap.read()
                if ret:
                    # Ghi frame
                    self.out.write(frame)

                    # Hiển thị (Phần này có thể gây lỗi trên một số OS
                    # khi chạy trong thread, nhưng thường là ổn)
                    cv2.imshow('Recording...', frame)

                    # Nhấn 'q' để dừng
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        # Nếu người dùng nhấn 'q', ta chủ động gọi stop
                        # (Nó sẽ set self.is_recording = False và thoát vòng lặp)
                        self.stop_recording()
                        break
                else:
                    print("Lỗi: Không nhận được khung hình.")
                    self.stop_recording()
                    break
        finally:
            # Đảm bảo file được đóng khi vòng lặp kết thúc
            if self.out:
                self.out.release()
            self.out = None
            print("...Luồng ghi đã dừng và giải phóng file.")

            # Đóng cửa sổ preview
            if cv2.getWindowProperty('Recording...', 0) >= 0:
                cv2.destroyWindow('Recording...')

    # --- HÀM ĐÃ SỬA ---
    def start_recording(self):
        """
        Bắt đầu ghi video (NON-BLOCKING).
        Hàm này chỉ khởi động luồng và kết thúc ngay lập tức.
        """
        with self.lock:
            if self.is_recording:
                print("Lỗi: Đã đang trong quá trình ghi!")
                return

            self.current_filename = self.generate_filename()
            self.out = cv2.VideoWriter(self.current_filename, self.fourcc, self.fps, self.size)

            if not self.out:
                print(f'Lỗi: Không thể tạo file VideoWriter.')
                return

            # Đặt cờ hiệu
            self.is_recording = True

            # Tạo và khởi động luồng worker
            self.worker_thread = threading.Thread(target=self._record_loop)
            self.worker_thread.start()

            print(f'Bắt đầu ghi. Sẽ lưu vào: {self.current_filename}')

    # --- HÀM ĐÃ SỬA ---
    def stop_recording(self):
        """
        Dừng việc ghi video.
        Hàm này chỉ set cờ hiệu, luồng worker sẽ tự dừng.
        """
        with self.lock:
            if not self.is_recording:
                return  # Chưa ghi thì không làm gì

            print("Nhận tín hiệu dừng ghi...")
            self.is_recording = False  # Set cờ hiệu

        # Chờ luồng worker kết thúc
        if self.worker_thread:
            self.worker_thread.join()  # Quan trọng: Chờ cho luồng kia chạy xong

        self.worker_thread = None
        print("...Đã dừng ghi hoàn toàn.")

    def release(self):
        """
        Giải phóng webcam và đóng tất cả cửa sổ.
        """
        # Nếu vẫn đang ghi, hãy dừng nó
        self.stop_recording()

        if self.cap.isOpened():
            self.cap.release()

        cv2.destroyAllWindows()
        print("Đã giải phóng tài nguyên.")



# CÁCH SỬ DỤNG VỚI threading.Timer

if __name__ == "__main__":

    # --- THIẾT LẬP TIMER ---
    SO_PHUT = 3
    SO_GIAY = SO_PHUT * 60

    recorder = None
    auto_stop_timer = None

    try:
        recorder = VideoRecorder(save_path="videos_3_phut")

        # 1. Tạo một Timer.
        # Nó sẽ gọi hàm `recorder.stop_recording` sau `SO_GIAY` giây.
        auto_stop_timer = threading.Timer(SO_GIAY, recorder.stop_recording)

        print(f"--- Sẽ tự động dừng sau {SO_PHUT} phút ---")

        # 2. Khởi động Timer (bắt đầu đếm ngược)
        auto_stop_timer.start()

        # 3. Bắt đầu ghi (hàm này chạy rất nhanh, không block)
        recorder.start_recording()

        # 4. Giữ chương trình chính "sống"
        # Chúng ta chờ cho đến khi luồng ghi kết thúc
        # (do timer gọi stop, hoặc do người dùng nhấn 'q')
        if recorder.worker_thread:
            recorder.worker_thread.join()  # Chờ ở đây

        print("--- Chương trình chính kết thúc ---")

    except IOError as e:
        print(e)
    except KeyboardInterrupt:
        print("\nNgười dùng ngắt chương trình (Ctrl+C).")

    finally:
        if 'recorder' in locals() and recorder:
            print("\nĐang dọn dẹp...")

            # Nếu chương trình kết thúc (ví dụ: Ctrl+C) trước khi timer chạy
            # chúng ta nên hủy timer
            if 'auto_stop_timer' in locals() and auto_stop_timer.is_alive():
                auto_stop_timer.cancel()

            # Giải phóng tất cả
            recorder.release()