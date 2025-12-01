import cv2
import os
from datetime import datetime


class VideoRecorder:
    def __init__(self, output_folder="recordings"):
        self.output_folder = output_folder
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        self.is_recording = False
        self.out = None

    def start_recording(self, frame_size):
        """
        frame_size: tuple (width, height)
        """
        if not self.is_recording:
            now = datetime.now()
            # Định dạng tên file: Ngay-Thang-Nam-Gio.mp4
            filename = now.strftime("%d-%m-%Y-%H-%M-%S.mp4")
            path = os.path.join(self.output_folder, filename)

            # Codec mp4v tương thích tốt với Windows
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.out = cv2.VideoWriter(path, fourcc, 20.0, frame_size)
            self.is_recording = True
            return path
        return None

    def write_frame(self, frame):
        if self.is_recording and self.out:
            self.out.write(frame)

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            if self.out:
                self.out.release()
                self.out = None