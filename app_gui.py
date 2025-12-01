import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import os
import sys

def resource_path(relative_path):
    """ Lấy đường dẫn đúng cho file khi chạy EXE hoặc chạy Python """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# --- CẤU HÌNH MÀU SẮC ---
COLOR_BG = "#F8F8FF"
COLOR_SIDEBAR = "#F8F8FF"
COLOR_PANEL_BG = "white"
COLOR_TEXT_PANEL = "black"
COLOR_VIDEO_BORDER = "#778899"

# Màu Viền Nút
BORDER_GREEN = "#28a745"
BORDER_RED = "#dc3545"
BORDER_BLUE = "#0056b3"


class AppGUI:
    def __init__(self, root, start_cb, stop_cb, history_cb, zoning_cb, capture_cb, record_cb):
        self.root = root
        self.root.title("Advanced Camera Tracking System")
        self.root.configure(bg=COLOR_BG)

        self.start_cb = start_cb
        self.stop_cb = stop_cb
        self.history_cb = history_cb
        self.zoning_cb = zoning_cb
        self.capture_cb = capture_cb
        self.record_cb = record_cb

        self.history_paths = [None, None, None, None]

        self.build_ui()

    def build_ui(self):
        self.root.columnconfigure(0, weight=0, minsize=280)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        sidebar = tk.Frame(self.root, bg=COLOR_SIDEBAR, padx=10, pady=10)
        sidebar.grid(row=0, column=0, sticky="nsew")

        # LOGO (CÓ VIỀN XANH)
        # Tạo Frame viền ngoài (Màu xanh dương)
        logo_border_frame = tk.Frame(sidebar, bg=BORDER_BLUE, padx=2, pady=2)
        logo_border_frame.pack(side="bottom", pady=20)

        # Tạo Frame nền trong (Màu trắng)
        logo_inner_frame = tk.Frame(logo_border_frame, bg="white")
        logo_inner_frame.pack(fill="both", expand=True)

        lbl_logo = tk.Label(logo_inner_frame, text="[LOGO]", font=("Arial", 16, "bold"), fg="#ccc", bg="white")
        lbl_logo.pack(padx=5, pady=5)  # Padding để logo không dính sát viền

        try:
            img = Image.open(resource_path("logo.png"))
            # Resize nhỏ lại xíu để lọt lòng khung viền
            img.thumbnail((210, 210), Image.Resampling.LANCZOS)
            self.logo_tk = ImageTk.PhotoImage(img)
            lbl_logo.config(image=self.logo_tk, text="")
        except:
            pass

        # CỤM NÚT ĐIỀU KHIỂN
        btn_container = tk.Frame(sidebar, bg=COLOR_SIDEBAR)
        btn_container.pack(side="top", fill="x", pady=(0, 10))

        def create_bordered_btn(parent, text, text_color, border_color, cmd, icon_char=""):
            border_frame = tk.Frame(parent, bg=border_color, padx=2, pady=2)
            border_frame.pack(fill="x", expand=False, pady=6)

            btn = tk.Button(border_frame, text=f"{icon_char} {text}",
                            bg="white", fg=text_color,
                            font=("Arial", 10, "bold"), bd=0,
                            activebackground="#f0f0f0", cursor="hand2", command=cmd)
            btn.pack(fill="both", expand=True, ipady=8)
            return btn, border_frame

        self.btn_start, _ = create_bordered_btn(btn_container, "START", "#000", BORDER_GREEN, self.start_cb, "▶")
        self.btn_stop, _ = create_bordered_btn(btn_container, "STOP", "#000", BORDER_RED, self.stop_cb, "■")
        self.btn_zoning, _ = create_bordered_btn(btn_container, "ZONING", "#000", BORDER_BLUE, self.zoning_cb, "⚠")
        self.btn_capture, _ = create_bordered_btn(btn_container, "CAPTURE", "#000", BORDER_BLUE, self.capture_cb, "📷")
        self.btn_record, self.frm_record = create_bordered_btn(btn_container, "RECORD", "#dc3545", BORDER_BLUE,
                                                               self.record_cb, "●")
        # Spacer 1
        tk.Frame(sidebar, bg=COLOR_SIDEBAR).pack(side="top", fill="y", expand=True)

        # BẢNG SETTINGS
        panel_frame = tk.LabelFrame(sidebar, text=" Settings ", bg=COLOR_PANEL_BG, fg="black",
                                    font=("Arial", 11, "bold"), bd=1, relief="solid")
        panel_frame.pack(side="top", fill="x", ipady=10)

        tk.Label(panel_frame, text="Ignore Small Objects (Size):", bg=COLOR_PANEL_BG, fg=COLOR_TEXT_PANEL,
                 font=("Arial", 9)).pack(anchor="w", padx=5)
        self.scale_sens = tk.Scale(panel_frame, from_=100, to=5000, orient="horizontal", bg=COLOR_PANEL_BG, fg="black",
                                   troughcolor="#ddd", highlightthickness=0)
        self.scale_sens.set(1000)
        self.scale_sens.pack(fill="x", padx=5, pady=(0, 10))

        tk.Label(panel_frame, text="Time to Record (Seconds):", bg=COLOR_PANEL_BG, fg=COLOR_TEXT_PANEL,
                 font=("Arial", 9)).pack(anchor="w", padx=5)
        self.scale_time = tk.Scale(panel_frame, from_=5, to=60, orient="horizontal", bg=COLOR_PANEL_BG, fg="black",
                                   troughcolor="#ddd", highlightthickness=0)
        self.scale_time.set(15)
        self.scale_time.pack(fill="x", padx=5)

        tk.Label(panel_frame, text="System Monitor", bg=COLOR_PANEL_BG, fg="#555", font=("Arial", 9, "bold")).pack(
            anchor="w", padx=5, pady=(10, 0))
        self.lbl_stats = tk.Label(panel_frame, text="Ready...", bg="white", fg="black", font=("Consolas", 9),
                                  justify="left", anchor="nw", height=5, bd=1, relief="sunken")
        self.lbl_stats.pack(fill="x", padx=5, pady=5)

        # Spacer 2
        tk.Frame(sidebar, bg=COLOR_SIDEBAR).pack(side="top", fill="y", expand=True)

        # --- MAIN AREA ---
        main_container = tk.Frame(self.root, bg=COLOR_BG, padx=5, pady=5)
        main_container.grid(row=0, column=1, sticky="nsew")

        content_area = tk.Frame(main_container, bg=COLOR_BG)
        content_area.pack(fill="both", expand=True)

        # VIDEO FRAME
        video_container_border = tk.Frame(content_area, bg=COLOR_VIDEO_BORDER, padx=2, pady=2)
        video_container_border.place(relx=0, rely=0, relwidth=1, relheight=0.75)

        video_container_bg = tk.Frame(video_container_border, bg="white")
        video_container_bg.pack(fill="both", expand=True)

        self.video_frame = tk.Frame(video_container_bg, bg="white", bd=0)
        self.video_frame.pack(fill="both", expand=True)

        self.lbl_video = tk.Label(self.video_frame, bg="white", cursor="cross")
        self.lbl_video.pack(fill="both", expand=True)

        # BOTTOM INFO
        bottom_frame = tk.Frame(content_area, bg=COLOR_BG)
        bottom_frame.place(relx=0, rely=0.75, relwidth=1, relheight=0.25)

        controls_row = tk.Frame(bottom_frame, bg=COLOR_BG)
        controls_row.pack(fill="x", padx=0, pady=10)

        tk.Button(controls_row, text="📂 History Folder", bg="#0056b3", fg="white", bd=0, font=("Arial", 10, "bold"),
                  command=self.history_cb, width=16, height=1).pack(side="left")
        self.lbl_status = tk.Label(controls_row, text="SAFE", bg="#28a745", fg="white", width=12,
                                   font=("Arial", 9, "bold"))
        self.lbl_status.pack(side="left", padx=5)

        timeline_container = tk.Frame(controls_row, bg=COLOR_BG)
        timeline_container.pack(side="left", fill="x", expand=True)

        self.lights = []
        for i in range(15):
            l = tk.Label(timeline_container, bg="#ddd", relief="flat", bd=0)
            l.pack(side="left", fill="both", expand=True, padx=1, ipady=4)
            self.lights.append(l)

        self.progress = ttk.Progressbar(bottom_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=0, pady=2)

        # HISTORY SLOTS
        thumbs_row = tk.Frame(bottom_frame, bg=COLOR_BG)
        thumbs_row.pack(fill="both", expand=True, padx=0, pady=5)

        self.history_slots = []
        for i in range(4):
            f = tk.Frame(thumbs_row, bg="#ccc", padx=1, pady=1)
            f.pack(side="left", fill="both", expand=True, padx=2)
            lbl = tk.Label(f, bg=COLOR_BG, text=f"Trống", fg="#999", font=("Arial", 10), cursor="hand2", wraplength=150)
            lbl.pack(fill="both", expand=True)
            lbl.bind("<Button-1>", lambda event, idx=i: self.on_history_click(idx))
            self.history_slots.append(lbl)

    def on_history_click(self, index):
        path = self.history_paths[index]
        if path and os.path.exists(path): os.startfile(path)

    def update_image(self, cv2_frame):
        w_cont = self.video_frame.winfo_width()
        h_cont = self.video_frame.winfo_height()
        if w_cont > 10 and h_cont > 10:
            color_correct_frame = cv2.cvtColor(cv2_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(color_correct_frame)
            img_w, img_h = img.size
            ratio = min(w_cont / img_w, h_cont / img_h)
            new_w = int(img_w * ratio)
            new_h = int(img_h * ratio)
            img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            bg_img = Image.new('RGB', (w_cont, h_cont), (255, 255, 255))
            bg_img.paste(img_resized, ((w_cont - new_w) // 2, (h_cont - new_h) // 2))
            imgtk = ImageTk.PhotoImage(image=bg_img)
            self.lbl_video.imgtk = imgtk
            self.lbl_video.configure(image=imgtk)
            return ratio, (w_cont - new_w) // 2, (h_cont - new_h) // 2
        return 1, 0, 0

    def update_dashboard(self, level, state, color, max_time=15.0):
        self.lbl_status.config(text=state, bg=color)
        pct = (level / max_time) * 100
        self.progress["value"] = pct
        active_lights = int((level / max_time) * 15)
        active_lights = min(active_lights, 15)
        for i, light in enumerate(self.lights):
            if i < active_lights:
                if i < 5:
                    light.config(bg="#28a745")
                elif i < 10:
                    light.config(bg="#ffc107")
                else:
                    light.config(bg="#dc3545")
            else:
                light.config(bg="#ddd")

    def reset_dashboard(self):
        self.lbl_status.config(text="SAFE", bg="#28a745")
        self.progress["value"] = 0
        for light in self.lights: light.config(bg="#ddd")
        self.lbl_video.configure(image='')
        self.btn_zoning.config(bg="white", fg="#0056b3")
        self.btn_record.config(bg="white", text="● RECORD")

    def push_to_history_queue(self, file_path):
        self.history_paths.insert(0, file_path)
        self.history_paths.pop()
        for i in range(4):
            path = self.history_paths[i]
            lbl = self.history_slots[i]
            if path:
                filename = os.path.basename(path)
                lbl.config(text=f"🎥 REC:\n{filename}", bg="#778899", fg="white", font=("Arial", 9, "bold"))
                lbl.master.config(bg="#778899")
            else:
                lbl.config(text="Trống", bg=COLOR_BG, fg="#999")
                lbl.master.config(bg="#ccc")

    def update_stats_text(self, text):
        self.lbl_stats.config(text=text)


# MAIN TEST
if __name__ == "__main__":
    import time


    # Các callback functions để test
    def on_start():
        print("[TEST] Nút START được nhấn")
        app.update_stats_text("System Started\nCamera: Active\nStatus: Monitoring...")


    def on_stop():
        print("[TEST] Nút STOP được nhấn")
        app.reset_dashboard()
        app.update_stats_text("System Stopped\nCamera: Inactive\nStatus: Ready...")


    def on_history():
        print("[TEST] Nút History Folder được nhấn")
        test_dir = "test_history"
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
        print(f"[TEST] Thư mục test: {os.path.abspath(test_dir)}")
        try:
            os.startfile(test_dir)
        except:
            print(f"[TEST] Không thể mở thư mục")


    def on_zoning():
        print("[TEST] Nút ZONING được nhấn")
        app.btn_zoning.config(bg="#ffc107", fg="black")
        app.update_stats_text("Zoning Mode: Active\nClick on video to set zones...")


    def on_capture():
        print("[TEST] Nút CAPTURE được nhấn")
        test_dir = "test_captures"
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
        filename = f"capture_{int(time.time())}.jpg"
        filepath = os.path.join(test_dir, filename)
        print(f"[TEST] Capture: {filepath}")
        app.push_to_history_queue(filepath)


    def on_record():
        print("[TEST] Nút RECORD được nhấn")
        if app.btn_record.cget("text") == "● RECORD":
            app.btn_record.config(bg="#dc3545", text="● RECORDING", fg="white")
            app.update_stats_text("Recording: ON\nSaving video...")
        else:
            app.btn_record.config(bg="white", text="● RECORD", fg="#dc3545")
            test_dir = "test_records"
            if not os.path.exists(test_dir):
                os.makedirs(test_dir)
            filename = f"record_{int(time.time())}.mp4"
            filepath = os.path.join(test_dir, filename)
            print(f"[TEST] Record: {filepath}")
            app.push_to_history_queue(filepath)
            app.update_stats_text("Recording: OFF\nVideo saved successfully")


    # Tạo root window và khởi tạo AppGUI
    root = tk.Tk()
    root.geometry("1200x700")
    root.minsize(800, 600)

    app = AppGUI(
        root=root,
        start_cb=on_start,
        stop_cb=on_stop,
        history_cb=on_history,
        zoning_cb=on_zoning,
        capture_cb=on_capture,
        record_cb=on_record
    )

    # Hiển thị thông báo ban đầu
    app.update_stats_text("System Ready\nWaiting for commands...\n\nTest Mode Active")

    print("=" * 50)
    print("APP GUI TEST - Đã khởi động!")
    print("=" * 50)
    print("Nhấn các nút để test các chức năng")
    print("=" * 50)

    # Chạy ứng dụng
    root.mainloop()