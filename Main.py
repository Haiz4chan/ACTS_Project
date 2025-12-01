import tkinter as tk
import cv2
import os
import time
from datetime import datetime

from app_gui import AppGUI
from MotionDetector import MotionDetector
from alert_manager import AlertManager
from videorecorder import VideoRecorder


class MainSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.detector = MotionDetector()
        self.alert_mgr = AlertManager(sound_file="alert.mp3")
        self.recorder = VideoRecorder(output_folder="recordings")

        self.gui = AppGUI(self.root, self.start, self.stop, self.open_history,
                          self.toggle_zoning_mode, self.manual_capture, self.manual_record_toggle)

        self.cap = None
        self.is_running = False
        self.is_manual_recording = False
        self.start_time = None

        self.is_zoning_mode = False;
        self.zone_rect = None
        self.drawing = False;
        self.start_point = (0, 0);
        self.end_point = (0, 0)
        self.gui_ratio = 1.0;
        self.gui_offset_x = 0;
        self.gui_offset_y = 0

        self.gui.lbl_video.bind("<ButtonPress-1>", self.on_mouse_down)
        self.gui.lbl_video.bind("<B1-Motion>", self.on_mouse_drag)
        self.gui.lbl_video.bind("<ButtonRelease-1>", self.on_mouse_up)

    def start(self):
        if not self.is_running:
            self.cap = cv2.VideoCapture(0)
            self.is_running = True
            self.start_time = time.time()
            self.process_loop()

    def stop(self):
        self.is_running = False
        self.is_manual_recording = False
        if self.cap: self.cap.release()
        self.recorder.stop_recording()
        self.alert_mgr.reset()
        self.gui.reset_dashboard()
        self.zone_rect = None

    def manual_capture(self):
        if self.is_running and self.cap:
            ret, frame = self.cap.read()
            if ret:
                now = datetime.now()
                path = os.path.abspath(os.path.join("recordings", now.strftime("CAP-%d%m%y-%H%M%S.jpg")))
                if not os.path.exists("recordings"): os.makedirs("recordings")
                cv2.imwrite(path, frame)
                self.gui.push_to_history_queue(path)

    def manual_record_toggle(self):
        if not self.is_running: return
        self.is_manual_recording = not self.is_manual_recording
        if self.is_manual_recording:
            self.gui.btn_record.config(text="■ STOP REC", bg="#dc3545", fg="white")
        else:
            self.gui.btn_record.config(text="● RECORD", bg="white", fg="#dc3545")
            if self.recorder.is_recording: self.recorder.stop_recording()

    def open_history(self):
        path = os.path.abspath("recordings")
        if not os.path.exists(path): os.makedirs(path)
        os.startfile(path)

    def toggle_zoning_mode(self):
        self.is_zoning_mode = not self.is_zoning_mode
        if self.is_zoning_mode:
            self.gui.btn_zoning.config(bg="#ffc107", text="✎ Drawing...")
            self.zone_rect = None
        else:
            self.gui.btn_zoning.config(bg="white", text="◬ ZONING")

    # --- SỬA LẠI LOGIC TÍNH TOẠ ĐỘ CHUỘT ---
    def gui_to_cam_coords(self, x_gui, y_gui):
        # Trừ đi phần viền trắng (Offset)
        x_real = x_gui - self.gui_offset_x
        y_real = y_gui - self.gui_offset_y

        if self.gui_ratio > 0:
            # Chia cho tỷ lệ (dùng float để chính xác hơn)
            x_cam = int(round(x_real / self.gui_ratio))
            y_cam = int(round(y_real / self.gui_ratio))
            return x_cam, y_cam
        return 0, 0

    def on_mouse_down(self, event):
        if self.is_zoning_mode:
            self.drawing = True
            self.start_point = self.gui_to_cam_coords(event.x, event.y)
            self.end_point = self.start_point

    def on_mouse_drag(self, event):
        if self.is_zoning_mode and self.drawing:
            self.end_point = self.gui_to_cam_coords(event.x, event.y)

    def on_mouse_up(self, event):
        if self.is_zoning_mode and self.drawing:
            self.drawing = False
            self.end_point = self.gui_to_cam_coords(event.x, event.y)
            x1, y1 = self.start_point;
            x2, y2 = self.end_point
            w = abs(x2 - x1);
            h = abs(y2 - y1)
            if w > 10 and h > 10: self.zone_rect = (min(x1, x2), min(y1, y2), w, h)
            self.toggle_zoning_mode()

    def process_loop(self):
        if self.is_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            frame = cv2.flip(frame, 1)
            if ret:
                # 1. Settings
                min_area_val = self.gui.scale_sens.get()
                self.detector.set_min_area(min_area_val)
                time_limit = self.gui.scale_time.get()
                self.alert_mgr.set_danger_limit(time_limit)

                # 2. Detect
                detected = False;
                detections = []
                if self.zone_rect:
                    zx, zy, zw, zh = self.zone_rect
                    h_img, w_img = frame.shape[:2]
                    # Clamping
                    zx = max(0, zx);
                    zy = max(0, zy);
                    zw = min(zw, w_img - zx);
                    zh = min(zh, h_img - zy)
                    if zw > 0 and zh > 0:
                        roi = frame[zy:zy + zh, zx:zx + zw]
                        detected, roi_detections = self.detector.detect(roi)
                        detections = [(rx + zx, ry + zy, rw, rh) for (rx, ry, rw, rh) in roi_detections]
                else:
                    detected, detections = self.detector.detect(frame)

                # 3. Alert
                state, level, color = "SAFE", 0, "#28a745"
                if self.zone_rect and detected:
                    state = "DANGER";
                    level = time_limit;
                    color = "#dc3545"
                    if self.alert_mgr.sound and not self.alert_mgr.sound.get_num_channels(): self.alert_mgr.sound.play()
                else:
                    state, level, color = self.alert_mgr.update(detected)

                # 4. Recording
                should_record = (state == "DANGER") or self.is_manual_recording
                if should_record:
                    if not self.recorder.is_recording:
                        path = self.recorder.start_recording((frame.shape[1], frame.shape[0]))
                        if path: self.gui.push_to_history_queue(path)
                    self.recorder.write_frame(frame)
                    if int(time.time() * 2) % 2 == 0: cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
                else:
                    if self.recorder.is_recording: self.recorder.stop_recording()

                # 5. Draw
                box_c = (0, 255, 0)
                if state == "WARNING":
                    box_c = (0, 255, 255)
                elif state == "DANGER":
                    box_c = (0, 0, 255)
                for (x, y, w, h) in detections: cv2.rectangle(frame, (x, y), (x + w, y + h), box_c, 2)
                if self.zone_rect:
                    zx, zy, zw, zh = self.zone_rect
                    cv2.rectangle(frame, (zx, zy), (zx + zw, zy + zh), (255, 0, 255), 2)
                    cv2.putText(frame, " ", (zx, zy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
                if self.is_zoning_mode and self.drawing:
                    cv2.rectangle(frame, self.start_point, self.end_point, (0, 165, 255), 2)

                # 6. Update GUI
                cv2.putText(frame, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), (frame.shape[1] - 220, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                self.gui_ratio, self.gui_offset_x, self.gui_offset_y = self.gui.update_image(frame)
                self.gui.update_dashboard(level, state, color, max_time=time_limit)

                # Update Stats
                runtime = int(time.time() - self.start_time)
                stats_text = (
                    f"Runtime: {runtime // 60:02d}:{runtime % 60:02d}\n"
                    f"Status: {state}\n"
                    f"Min Area Size: {min_area_val}\n"
                    f"Time Limit: {time_limit}s\n"
                    f"Detected Objs: {len(detections)}"
                )
                self.gui.update_stats_text(stats_text)

            self.root.after(10, self.process_loop)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MainSystem()
    app.run()