import tkinter as tk
from tkinter import ttk
from typing import Optional, Protocol
from datetime import datetime

import numpy as np
from PIL import Image, ImageTk


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

        self._setup_widgets()

    def _setup_widgets(self) -> None:
        style = ttk.Style()
        style.configure("Main.TFrame", background="#f5f0ea")
        style.configure("Sidebar.TFrame", background="#ffffff")
        style.configure("Video.TFrame", background="#3e4a61")
        style.configure("Start.TButton", font=("Arial", 14, "bold"))
        style.configure("Stop.TButton", font=("Arial", 14, "bold"))

        self.main_frame = ttk.Frame(self.root, style="Main.TFrame", padding=12)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=0)

        # Sidebar
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

        # Video panel
        video_frame = ttk.Frame(self.main_frame, style="Video.TFrame")
        video_frame.grid(row=0, column=1, sticky="nsew")
        video_frame.rowconfigure(0, weight=1)
        video_frame.columnconfigure(0, weight=1)

        self.video_label = tk.Label(
            video_frame,
            text="Video feed preview",
            anchor=tk.CENTER,
            bg="#3e4a61",
            fg="white",
            font=("Consolas", 16),
        )
        self.video_label.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # Bottom section
        bottom_frame = ttk.Frame(self.main_frame, padding=(0, 12, 0, 0))
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        bottom_frame.columnconfigure(0, weight=1)

        style.configure("Green.Horizontal.TProgressbar", troughcolor="#f1ebe4", background="#6fbf73")
        style.configure("Yellow.Horizontal.TProgressbar", troughcolor="#f1ebe4", background="#f2c94c")
        style.configure("Red.Horizontal.TProgressbar", troughcolor="#f1ebe4", background="#e57373")

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

    def attach_motion_detector(self, module: MotionDetector) -> None:
        self.motion_detector = module

    def attach_alert_manager(self, module: AlertManager) -> None:
        self.alert_manager = module

    def start_system(self) -> None:
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self._set_status("green", "System is running. Monitoring movement.")

        if self.video_recorder:
            self.video_recorder.start_recording()
        if self.motion_detector:
            self.motion_detector.start_detection()
        if self.alert_manager:
            self.alert_manager.notify_start()

    def stop_system(self) -> None:
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self._cancel_alarm()
        self._set_status("idle", "System stopped.")

        if self.video_recorder:
            self.video_recorder.stop_recording()
        if self.motion_detector:
            self.motion_detector.stop_detection()
        if self.alert_manager:
            self.alert_manager.notify_stop()

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

    def update_frame(self, frame: np.ndarray) -> None:
        if frame is None:
            return

        if len(frame.shape) == 3 and frame.shape[2] == 3:
            image = Image.fromarray(frame[:, :, ::-1])
        else:
            image = Image.fromarray(frame)

        width = max(self.video_label.winfo_width(), 1)
        height = max(self.video_label.winfo_height(), 1)
        image = image.resize((width, height))

        self._photo_image = ImageTk.PhotoImage(image=image)
        self.video_label.configure(image=self._photo_image)

    def append_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}\n"
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, entry)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

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


if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.state("zoomed")
    except tk.TclError:
        root.attributes("-zoomed", True)
    gui = AppGUI(root)
    root.mainloop()

