import tkinter as tk
import time


class SecurityApp:
    def __init__(self, root):
        print("Khởi tạo SecurityApp...")
        self.root = root
        self.root.title("Dự án Camera An ninh (Nhóm 5)")

        self.running = False

        self.test_label = tk.Label(root, text="Chào mừng! Nhấn Start để bắt đầu.", font=("Arial", 18))
        self.test_label.pack(pady=20, padx=20)

        self.start_button = tk.Button(root, text="Start", command=self.start_app)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(root, text="Stop", command=self.stop_app, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

    def start_app(self):
        if self.running:
            return

        print("Ứng dụng Bắt đầu")
        self.running = True

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.test_label.config(text="Đang chạy...")

    def stop_app(self):
        if not self.running:
            return

        print("Ứng dụng Dừng")
        self.running = False

        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.test_label.config(text="Đã dừng. Nhấn Start để chạy lại.")


if __name__ == "__main__":
    print("Bắt đầu chương trình")

    root = tk.Tk()
    app = SecurityApp(root)

    root.mainloop()

    print("Kết thúc chương trình")