import tkinter as tk
from tkinter import ttk
from typing import Optional, Protocol, Tuple
from datetime import datetime
from pathlib import Path
import threading

import numpy as np
from PIL import Image, ImageTk
import MotionDetector as motion_detector_module


class VideoRecorder(Protocol):
    def start_recording(self) -> None: ...

    def stop_recording(self) -> None: ...


class MotionDetector(Protocol):
    def start_detection(self) -> None: ...

    def stop_detection(self) -> None: ...


class AlertManager(Protocol):
    def notify_start(self) -> None: ...

    def notify_stop(self) -> None: ...

    def play_alarm(self) -> None: ...

    def send_continuous_alert(self) -> None: ...


class AppGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Advanced Camera Tracking System")
        self.root.configure(bg="#f5f0ea")

        self.video_recorder: Optional[VideoRecorder] = None
        self.motion_detector: Optional[MotionDetector] = None
        self.alert_manager: Optional[AlertManager] = None

        self._current_status = "idle"
        self._alarm_job: Optional[str] = None
        self._is_system_running = False
        self._is_recording = False
        self._alert_log_path = Path("alert_history.log")
        self._alert_log_job: Optional[str] = None
        self._alert_log_position = 0
        self._detector_thread: Optional[threading.Thread] = None

        self._setup_widgets()

    def _setup_widgets(self) -> None:
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.style.configure("Main.TFrame", background="#f5f0ea")
        self.style.configure("Sidebar.TFrame", background="#ffffff")
        self.style.configure("Video.TFrame", background="#3e4a61")
        self.style.configure("Start.TButton", font=("Arial", 14, "bold"))
        self.style.configure("Stop.TButton", font=("Arial", 14, "bold"))

        self.main_frame = ttk.Frame(self.root, style="Main.TFrame", padding=12)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=0)

        # Khu vực sidebar (nút điều khiển)
        sidebar = ttk.Frame(self.main_frame, style="Sidebar.TFrame", padding=8)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        self.start_button = tk.Button(
            sidebar,
            text="START",
            command=self.start_system,
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#2e7d32",
            activebackground="#2e7d32",
            relief=tk.FLAT,
            height=2,
        )
        self.start_button.pack(fill=tk.X, pady=(0, 10))

        self.stop_button = tk.Button(
            sidebar,
            text="STOP",
            command=self.stop_system,
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#8b1c13",
            activebackground="#8b1c13",
            relief=tk.FLAT,
            height=2,
            state=tk.DISABLED,
        )
        self.stop_button.pack(fill=tk.X)

        self.record_button = tk.Button(
            sidebar,
            text="RECORD",
            command=self.toggle_recording,
            font=("Arial", 14, "bold"),
            fg="white",
            bg="#1d3557",
            activebackground="#1d3557",
            relief=tk.FLAT,
            height=2,
            state=tk.DISABLED,
        )
        self.record_button.pack(fill=tk.X, pady=(10, 0))

        note_text = (
            "Ghi chú:\n"
            "- Start bật giám sát & MotionDetector.\n"
            "- Nhấn RECORD để ghi hình ngay.\n"
            "- Vẽ ROI trực tiếp trong khung video."
        )
        self.note_label = tk.Label(
            sidebar,
            text=note_text,
            justify=tk.LEFT,
            anchor="w",
            bg="#ffffff",
            fg="#4b4b4b",
            font=("Arial", 10),
            wraplength=180,
        )
        self.note_label.pack(fill=tk.X, pady=(16, 0))

        # Khu vực hiển thị video chính
        video_frame = ttk.Frame(self.main_frame, style="Video.TFrame")
        video_frame.grid(row=0, column=1, sticky="nsew")
        video_frame.rowconfigure(0, weight=1)
        video_frame.columnconfigure(0, weight=1)

        self.video_container = tk.Frame(
            video_frame,
            bg="#3e4a61",
            bd=2,
            relief=tk.SUNKEN,
        )
        self.video_container.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        self.video_placeholder = tk.Label(
            self.video_container,
            text="Video feed preview",
            anchor=tk.CENTER,
            bg="#3e4a61",
            fg="white",
            font=("Consolas", 16),
        )
        self.video_placeholder.pack(fill=tk.BOTH, expand=True)

        # Khu vực đáy (status, log)
        bottom_frame = ttk.Frame(self.main_frame, padding=(0, 12, 0, 0))
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        bottom_frame.columnconfigure(0, weight=1)

        self.style.configure("Green.Horizontal.TProgressbar", troughcolor="#f1ebe4", background="#6fbf73")
        self.style.configure("Yellow.Horizontal.TProgressbar", troughcolor="#f1ebe4", background="#f2c94c")
        self.style.configure("Red.Horizontal.TProgressbar", troughcolor="#f1ebe4", background="#e57373")

        self.status_progress = ttk.Progressbar(
            bottom_frame,
            maximum=100,
            value=0,
            style="Green.Horizontal.TProgressbar",
            mode="determinate",
        )
        self.status_progress.pack(fill=tk.X, pady=(0, 8), ipady=6)

        status_row = tk.Frame(bottom_frame, bg="#f5f0ea")
        status_row.pack(fill=tk.X, pady=(0, 8))

        history_label = tk.Label(
            status_row, text="Log", bg="#c87f4f", fg="white", width=12, font=("Arial", 12, "bold")
        )
        history_label.pack(side=tk.LEFT, padx=(0, 6))

        status_prefix = tk.Label(
            status_row, text="Status:", bg="#f5f0ea", fg="#1f1f1f", font=("Arial", 12, "bold")
        )
        status_prefix.pack(side=tk.LEFT, padx=(0, 6))

        self.status_var = tk.StringVar(value="System ready.")
        self.status_message_label = tk.Label(
            status_row,
            textvariable=self.status_var,
            bg="#1f2a44",
            fg="white",
            font=("Arial", 12),
            anchor="w",
        )
        self.status_message_label.pack(fill=tk.X, expand=True)

        log_frame = tk.Frame(bottom_frame, bg="#3b4468", bd=2, relief=tk.GROOVE)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_frame,
            height=6,
            bg="#1f2437",
            fg="#dfe6f0",
            font=("Consolas", 11),
            state=tk.DISABLED,
            wrap=tk.WORD,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self._photo_image: Optional[ImageTk.PhotoImage] = None

    def attach_video_recorder(self, module: VideoRecorder) -> None:
        self.video_recorder = module
        self._update_record_button_state()

    def attach_motion_detector(self, module: MotionDetector) -> None:
        self.motion_detector = module

    def attach_alert_manager(self, module: AlertManager) -> None:
        self.alert_manager = module

    # Hàm bắt đầu chu trình giám sát (không tự động ghi hình)
    def start_system(self) -> None:
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self._set_status("green", "System is running. Monitoring movement.")

        if self.motion_detector and hasattr(self.motion_detector, "start_detection"):
            self.motion_detector.start_detection()
        if self.alert_manager:
            self.alert_manager.notify_start()

        self._is_system_running = True
        self._update_record_button_state()
        self._start_alert_history_feed()
        self._start_motion_detector_embed()

    # Hàm dừng toàn bộ hoạt động và trả UI về trạng thái chờ
    def stop_system(self) -> None:
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self._cancel_alarm()
        self._set_status("idle", "System stopped.")

        if self._is_recording:
            self._stop_recording()
        if self.motion_detector and hasattr(self.motion_detector, "stop_detection"):
            self.motion_detector.stop_detection()
        if self.alert_manager:
            self.alert_manager.notify_stop()

        self._is_system_running = False
        self._update_record_button_state()
        self.reset_roi()
        self._stop_alert_history_feed()
        self._stop_motion_detector_embed()
        self.update_frame(None)

    # Hàm nhận thời lượng chuyển động để cập nhật trạng thái cảnh báo
    def handle_motion_activity(self, duration_seconds: float) -> None:
        """Called by MotionDetector to adjust status based on motion duration."""
        if duration_seconds <= 60:
            self._set_status("green", "Movement < 1 minute. Tracking target.")
            self._cancel_alarm()
            self._log("Motion detected: safe zone.")
        elif 60 < duration_seconds <= 180:
            self._set_status("yellow", "Movement 1-3 minutes. Periodic alarm enabled.")
            self._schedule_alarm(interval_ms=10_000)
            self._log("Warning zone. Alarm scheduled every 10s.")
        else:
            self._set_status("red", "Movement > 3 minutes! Continuous alert.")
            self._cancel_alarm()
            if self.alert_manager:
                self.alert_manager.send_continuous_alert()
            self._log("Alert zone. Continuous notifications dispatched.")

    # Hàm vẽ frame OpenCV mới (giữ nguyên tỷ lệ gốc) lên label hiển thị
    def update_frame(self, frame: Optional[np.ndarray]) -> None:
        if frame is None:
            self._show_placeholder("Video feed preview")
            self._photo_image = None
            return

        if len(frame.shape) == 3 and frame.shape[2] == 3:
            image = Image.fromarray(frame[:, :, ::-1])
        else:
            image = Image.fromarray(frame)

        self._photo_image = ImageTk.PhotoImage(image=image)
        self._hide_placeholder()
        self.video_placeholder.configure(image=self._photo_image, text="")

    # Hàm thêm log nội bộ (không ảnh hưởng file alert_history.log)
    def append_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}\n"
        self._write_log_text(entry)

    def _log(self, message: str) -> None:
        self.append_log(message)

    def _set_status(self, level: str, message: str) -> None:
        self.status_var.set(message)
        self._current_status = level

        if level == "green":
            self.status_message_label.configure(bg="#2d6a4f")
            self.status_progress.configure(style="Green.Horizontal.TProgressbar")
            self.status_progress["value"] = 33
        elif level == "yellow":
            self.status_message_label.configure(bg="#cc9a06")
            self.status_progress.configure(style="Yellow.Horizontal.TProgressbar")
            self.status_progress["value"] = 66
        elif level == "red":
            self.status_message_label.configure(bg="#8b1c13")
            self.status_progress.configure(style="Red.Horizontal.TProgressbar")
            self.status_progress["value"] = 100
        else:
            self.status_message_label.configure(bg="#394867")
            self.status_progress.configure(style="Green.Horizontal.TProgressbar")
            self.status_progress["value"] = 0

    def _schedule_alarm(self, interval_ms: int) -> None:
        self._cancel_alarm()

        if not self.alert_manager:
            return

        def _alarm_tick() -> None:
            if self.alert_manager:
                self.alert_manager.play_alarm()
            self._alarm_job = self.root.after(interval_ms, _alarm_tick)

        self._alarm_job = self.root.after(interval_ms, _alarm_tick)

    def _cancel_alarm(self) -> None:
        if self._alarm_job:
            self.root.after_cancel(self._alarm_job)
            self._alarm_job = None

    # Hàm xử lý nút RECORD để bật/tắt ghi hình thủ công
    def toggle_recording(self) -> None:
        if not self.video_recorder:
            self._log("Record button pressed but no VideoRecorder attached.")
            return

        if not self._is_system_running:
            self._log("Cannot record while system is stopped. Start the system first.")
            return

        if not self._is_recording:
            self._start_recording()
        else:
            self._stop_recording()

    # Hàm gọi module VideoRecorder để bắt đầu ghi hình
    def _start_recording(self) -> None:
        if not self.video_recorder or self._is_recording:
            return
        self.video_recorder.start_recording()
        self._is_recording = True
        self.record_button.configure(text="STOP RECORD")
        self._log("Manual recording started.")

    # Hàm gọi module VideoRecorder để dừng ghi hình
    def _stop_recording(self) -> None:
        if not self.video_recorder or not self._is_recording:
            return
        self.video_recorder.stop_recording()
        self._is_recording = False
        self.record_button.configure(text="RECORD")
        self._log("Recording stopped.")

    # Hàm bật/tắt nút RECORD dựa trên trạng thái hệ thống và module recorder
    def _update_record_button_state(self) -> None:
        if self.video_recorder and self._is_system_running:
            self.record_button.configure(state=tk.NORMAL)
        else:
            self.record_button.configure(state=tk.DISABLED)
            if self._is_recording:
                self._stop_recording()

    def get_roi_rect(self, frame_width: int, frame_height: int) -> Tuple[int, int, int, int]:
        """Lấy ROI hiện tại từ MotionDetector, mặc định là toàn khung."""
        roi = motion_detector_module.roi
        if roi is None:
            return (0, 0, frame_width, frame_height)
        x, y, w, h = roi
        return (x, y, w, h)

    def reset_roi(self) -> None:
        motion_detector_module.roi = None
        self._log("ROI đã được đặt lại về toàn khung.")

    def _hide_placeholder(self) -> None:
        if self.video_placeholder.winfo_manager():
            self.video_placeholder.pack_forget()

    def _show_placeholder(self, text: str = "Video feed preview") -> None:
        if not self.video_placeholder.winfo_manager():
            self.video_placeholder.pack(fill=tk.BOTH, expand=True)
        self.video_placeholder.configure(text=text, image="")

    def _start_motion_detector_embed(self) -> None:
        if not hasattr(motion_detector_module, "main"):
            self._log("Không tìm thấy MotionDetector.main().")
            return
        if self._detector_thread and self._detector_thread.is_alive():
            return

        self.video_container.update_idletasks()
        width = max(self.video_container.winfo_width(), 320)
        height = max(self.video_container.winfo_height(), 240)

        if hasattr(motion_detector_module, "set_embed_target"):
            motion_detector_module.set_embed_target(
                self.video_container.winfo_id(), width, height
            )

        self._hide_placeholder()

        def _runner() -> None:
            try:
                motion_detector_module.main()
            except Exception as exc:  # pragma: no cover
                self._log(f"MotionDetector dừng: {exc}")
            finally:
                if hasattr(motion_detector_module, "set_embed_target"):
                    motion_detector_module.set_embed_target(None, 0, 0)
                self.root.after(0, self._show_placeholder)

        self._detector_thread = threading.Thread(target=_runner, daemon=True)
        self._detector_thread.start()

    def _stop_motion_detector_embed(self) -> None:
        if hasattr(motion_detector_module, "request_stop"):
            motion_detector_module.request_stop()
        if self._detector_thread:
            self._detector_thread.join(timeout=2.0)
            self._detector_thread = None
        if hasattr(motion_detector_module, "set_embed_target"):
            motion_detector_module.set_embed_target(None, 0, 0)
        self._show_placeholder()

    def _write_log_text(self, content: str, replace: bool = False) -> None:
        self.log_text.configure(state=tk.NORMAL)
        if replace:
            self.log_text.delete("1.0", tk.END)
        self.log_text.insert(tk.END, content)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _start_alert_history_feed(self) -> None:
        self._alert_log_position = 0
        self._stop_alert_history_feed()
        self._poll_alert_history(initial=True)

    def _poll_alert_history(self, initial: bool = False) -> None:
        path = self._alert_log_path
        try:
            if not path.exists():
                if initial:
                    self._write_log_text("Waiting for alert_history.log...\n", replace=True)
            else:
                with path.open("rb") as handle:
                    if initial:
                        data = handle.read()
                    else:
                        handle.seek(self._alert_log_position)
                        data = handle.read()
                    self._alert_log_position = handle.tell()
                if data:
                    text = data.decode("utf-8", errors="replace")
                    self._write_log_text(text, replace=initial)
        except OSError as err:
            self._write_log_text(f"Failed to read alert_history.log: {err}\n", replace=initial)

        self._alert_log_job = self.root.after(2000, self._poll_alert_history)

    def _stop_alert_history_feed(self) -> None:
        if self._alert_log_job:
            self.root.after_cancel(self._alert_log_job)
            self._alert_log_job = None



if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.state("zoomed")
    except tk.TclError:
        root.attributes("-zoomed", True)
    gui = AppGUI(root)
    root.mainloop()
