import cv2
import time
import datetime
import os
import threading
import atexit

"""
@author Phan Cong Doanh
"""

class VideoRecorder:

    def __init__(self, device=0, save_path="videos", width=640, height=480, fps=20.0, show_preview=True):
        self.device = device
        self.save_path = save_path
        self.size = (width, height)
        self.fps = fps
        self.show_preview = show_preview
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

        # Check camera lúc khởi tạo
        if not self.cap.isOpened():
            raise IOError(f'Không thể mở webcam (device {self.device})')

        # --- ĐĂNG KÝ BẢO HIỂM ---
        # Khi chương trình Python tắt (bất kể lý do gì), hàm self.release sẽ được gọi
        atexit.register(self.release)

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
        window_name = 'Recording...'
        frames_written = 0 # Biến đếm số khung hình đã ghi được

        self.out = cv2.VideoWriter(self.current_filename, self.fourcc, self.fps, self.size)

        if not self.out.isOpened():
            print("Lô: Không thể khởi tạo file video")
            self.is_recording = False
            return

        print(f'Bắt đầu ghi dữ liệu vào file: {self.current_filename}')

        try:
            while True:
                # Kiểm tra cờ hiệu
                with self.lock:
                    if not self.is_recording:
                        break

                # Đọc frame
                ret, frame = self.cap.read()
                if ret:
                    # Ghi frame
                    self.out.write(frame)
                    frames_written += 1

                    if self.show_preview:
                        # Hiển thị (Phần này có thể gây lỗi trên một số OS
                        # khi chạy trong thread, nhưng thường là ổn)
                        cv2.imshow(window_name, frame)

                        # Nhấn 'q' để dừng
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            self.stop_recording()
                            break

                        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                            self.stop_recording()
                            break
                    # Nếu không show_preview, ta không cần waitKey(1)
                    # Nhưng nên sleep cực ngắn để tránh ngốn 100% CPU
                    else:
                        time.sleep(0.001)
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
            if self.show_preview:
                try:
                    cv2.destroyWindow(window_name)
                except:
                    pass

            # Logic dọn rác khi số frame ghi được = 0, tưc file rỗng hoặc lỗi => Xóa file
            if frames_written == 0 and self.current_filename and os.path.exists(self.current_filename):
                print(f'Không ghi được khung hình nào. Đang xóa file rác: {self.current_filename}')
                try:
                    os.remove(self.current_filename)
                    print("Đã xóa file")
                except OSError as e:
                    print(f'Không thể xóa file: {e}')

    # --- HÀM ĐÃ SỬA ---
    def start_recording(self):
        """
        Bắt đầu ghi video (NON-BLOCKING).
        Hàm này chỉ khởi động luồng và kết thúc ngay lập tức.
        """
        with self.lock:
            if self.is_recording:
                print("Lỗi: Đang trong quá trình ghi!")
                return

            # 1.Tạo file
            self.current_filename = self.generate_filename()

            # 2.Đặt cờ hiệu
            self.is_recording = True

            # 3.Tạo và khởi động luồng worker
            self.worker_thread = threading.Thread(target=self._record_loop)
            self.worker_thread.start()

            print(f'Bắt đầu ghi. Sẽ lưu vào: {self.current_filename}')

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