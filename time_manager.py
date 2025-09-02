import tkinter as tk
from tkinter import messagebox
import time
import json

# --- 应用配置 (App Configuration) ---
BG_COLOR = "#282c34"
TEXT_COLOR = "#abb2bf"
ACCENT_COLOR = "#61afef"
WARN_COLOR = "#e06c75"
ACTIVE_COLOR = "#98c379"
FONT_NORMAL = ("Arial", 11)
FONT_MINI_TIMER = ("Arial", 10)
FONT_LARGE = ("Consolas", 36, "bold")
CONFIG_FILE = "config.json"
SAVE_FILE = "tasks.txt"
WINDOW_WIDTH_NORMAL = 320
WINDOW_HEIGHT_NORMAL = 480
WINDOW_WIDTH_MINI = 230
WINDOW_HEIGHT_MINI = 120


class TimeManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.stopwatch_running = False;
        self.stopwatch_time = 0
        self.countdown_running = False;
        self.initial_countdown_seconds = 0;
        self.countdown_seconds = 0
        self.is_mini_mode = False

        self.load_config()
        self.title("Time Manager");
        self.config(bg=BG_COLOR)
        self.geometry(f"{WINDOW_WIDTH_NORMAL}x{WINDOW_HEIGHT_NORMAL}+{self.window_x}+{self.window_y}")
        self.attributes('-topmost', True);
        self.attributes('-alpha', self.window_alpha);
        self.overrideredirect(True)

        self._offset_x = 0;
        self._offset_y = 0
        self.bind('<Button-1>', self.click_window);
        self.bind('<B1-Motion>', self.drag_window)

        self.create_widgets()
        self.load_tasks()
        self.update_clock();
        self.update_timers()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        if self.last_mini_mode_state: self.toggle_mini_mode()

    def create_widgets(self):
        # --- 创建主框架和迷你框架 ---
        self.main_frame = tk.Frame(self, bg=BG_COLOR)
        self.mini_frame = tk.Frame(self, bg=BG_COLOR)  # 先创建好，而不是在切换时创建

        # --- 创建控件框架 (始终置顶) ---
        self.control_frame = tk.Frame(self, bg=BG_COLOR)
        self.mini_mode_button = tk.Button(self.control_frame, text="─", bg=BG_COLOR, fg=TEXT_COLOR,
                                          font=("Arial", 12, "bold"), relief="flat", command=self.toggle_mini_mode)
        self.mini_mode_button.pack(side="left")
        quit_button = tk.Button(self.control_frame, text="✕", bg=BG_COLOR, fg=WARN_COLOR, font=("Arial", 12, "bold"),
                                relief="flat", activebackground=WARN_COLOR, activeforeground=BG_COLOR,
                                command=self.on_closing)
        quit_button.pack(side="right")
        self.control_frame.place(x=0, y=0, relwidth=1.0, height=30)

        # --- 填充主框架 (Normal Mode UI) ---
        self.clock_label = tk.Label(self.main_frame, text="", font=FONT_LARGE, fg=ACCENT_COLOR, bg=BG_COLOR)
        self.clock_label.pack(pady=(20, 10))
        # ... (此处省略了主框架内其他控件的创建，完整代码见下方)
        sw_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        self.stopwatch_label = tk.Label(sw_frame, text="00:00:00", font=FONT_NORMAL, fg=TEXT_COLOR, bg=BG_COLOR,
                                        width=10);
        self.stopwatch_label.pack(side="left", padx=5)
        self.sw_toggle_button = tk.Button(sw_frame, text="▶", command=self.toggle_stopwatch, fg=TEXT_COLOR, bg=BG_COLOR,
                                          relief="flat");
        self.sw_toggle_button.pack(side="left")
        tk.Button(sw_frame, text="■", command=self.stop_stopwatch, fg=TEXT_COLOR, bg=BG_COLOR, relief="flat").pack(
            side="left")
        tk.Button(sw_frame, text="R", command=self.reset_stopwatch, fg=TEXT_COLOR, bg=BG_COLOR, relief="flat").pack(
            side="left")
        sw_frame.pack(pady=5)
        cd_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        self.countdown_label = tk.Label(cd_frame, text="00:00", font=FONT_NORMAL, fg=TEXT_COLOR, bg=BG_COLOR, width=10);
        self.countdown_label.pack(side="left", padx=5)
        self.countdown_entry = tk.Entry(cd_frame, width=4, bg=TEXT_COLOR, fg=BG_COLOR, relief="flat", justify="center");
        self.countdown_entry.insert(0, "25");
        self.countdown_entry.pack(side="left")
        tk.Button(cd_frame, text="Set", command=self.set_countdown, fg=TEXT_COLOR, bg=BG_COLOR, relief="flat").pack(
            side="left")
        self.cd_toggle_button = tk.Button(cd_frame, text="▶", command=self.toggle_countdown, fg=TEXT_COLOR, bg=BG_COLOR,
                                          relief="flat");
        self.cd_toggle_button.pack(side="left")
        tk.Button(cd_frame, text="R", command=self.reset_countdown, fg=TEXT_COLOR, bg=BG_COLOR, relief="flat").pack(
            side="left")
        cd_frame.pack(pady=5)
        alpha_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        tk.Label(alpha_frame, text="T:", font=FONT_NORMAL, fg=TEXT_COLOR, bg=BG_COLOR).pack(side="left", padx=(10, 0))
        self.alpha_slider = tk.Scale(alpha_frame, from_=0.2, to=1.0, resolution=0.05, orient="horizontal", bg=BG_COLOR,
                                     fg=TEXT_COLOR, troughcolor=TEXT_COLOR, highlightthickness=0,
                                     command=self.set_alpha)
        self.alpha_slider.set(self.window_alpha);
        self.alpha_slider.pack(side="left", fill="x", expand=True, padx=10)
        alpha_frame.pack(fill="x", pady=5)
        self.task_text = tk.Text(self.main_frame, height=10, bg="#3b4048", fg=TEXT_COLOR, insertbackground=TEXT_COLOR,
                                 relief="flat", font=FONT_NORMAL, wrap="word")
        self.task_text.pack(pady=10, padx=10, fill="both", expand=True)

        # --- 填充迷你框架 (Mini Mode UI) ---
        self.clock_label_mini = tk.Label(self.mini_frame, text="", font=FONT_LARGE, fg=ACCENT_COLOR, bg=BG_COLOR)
        self.clock_label_mini.pack(pady=(10, 0))
        self.mini_stopwatch_label = tk.Label(self.mini_frame, text="", font=FONT_MINI_TIMER, fg=ACTIVE_COLOR,
                                             bg=BG_COLOR)
        self.mini_stopwatch_label.pack(pady=0, ipady=0)
        self.mini_countdown_label = tk.Label(self.mini_frame, text="", font=FONT_MINI_TIMER, fg=ACTIVE_COLOR,
                                             bg=BG_COLOR)
        self.mini_countdown_label.pack(pady=0, ipady=0)

        # 默认显示主框架
        self.main_frame.pack(fill="both", expand=True, pady=(30, 0))

    # <--- BUG FIX: 全新、更稳定的模式切换逻辑 ---
    def toggle_mini_mode(self):
        self.is_mini_mode = not self.is_mini_mode
        if self.is_mini_mode:
            # 切换到迷你模式
            self.main_frame.pack_forget()  # 隐藏主框架
            self.mini_frame.pack(fill="both", expand=True)  # 显示迷你框架
            self.geometry(f"{WINDOW_WIDTH_MINI}x{WINDOW_HEIGHT_MINI}")
            self.mini_mode_button.config(text="□")
        else:
            # 恢复到正常模式
            self.mini_frame.pack_forget()  # 隐藏迷你框架
            self.main_frame.pack(fill="both", expand=True, pady=(30, 0))  # 显示主框架
            self.geometry(f"{WINDOW_WIDTH_NORMAL}x{WINDOW_HEIGHT_NORMAL}")
            self.mini_mode_button.config(text="─")

        # 无论在哪种模式，都确保控制栏在最顶层，防止被覆盖
        self.control_frame.lift()

    def click_window(self, event):
        draggable_widgets = (tk.Tk, tk.Frame, tk.Label)
        if isinstance(event.widget, draggable_widgets):
            self._offset_x = event.x;
            self._offset_y = event.y
        else:
            self._offset_x = None;
            self._offset_y = None

    def drag_window(self, event):
        if self._offset_x is not None and self._offset_y is not None:
            x = self.winfo_pointerx() - self._offset_x;
            y = self.winfo_pointery() - self._offset_y
            self.geometry(f"+{x}+{y}")

    # ... 其他所有函数保持不变，但为了保证你可以直接复制运行，下面提供完整代码 ...


# =======================================================================
# ======================== 完整代码 START ===============================
# =======================================================================

import tkinter as tk
from tkinter import messagebox
import time
import json

# --- 应用配置 (App Configuration) ---
BG_COLOR = "#282c34"
TEXT_COLOR = "#abb2bf"
ACCENT_COLOR = "#61afef"
WARN_COLOR = "#e06c75"
ACTIVE_COLOR = "#98c379"
FONT_NORMAL = ("Arial", 11)
FONT_MINI_TIMER = ("Arial", 10)
FONT_LARGE = ("Consolas", 36, "bold")
CONFIG_FILE = "config.json"
SAVE_FILE = "tasks.txt"
WINDOW_WIDTH_NORMAL = 320
WINDOW_HEIGHT_NORMAL = 480
WINDOW_WIDTH_MINI = 230
WINDOW_HEIGHT_MINI = 120


class TimeManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.stopwatch_running = False;
        self.stopwatch_time = 0
        self.countdown_running = False;
        self.initial_countdown_seconds = 0;
        self.countdown_seconds = 0
        self.is_mini_mode = False

        self.load_config()
        self.title("Time Manager");
        self.config(bg=BG_COLOR)
        self.geometry(f"{WINDOW_WIDTH_NORMAL}x{WINDOW_HEIGHT_NORMAL}+{self.window_x}+{self.window_y}")
        self.attributes('-topmost', True);
        self.attributes('-alpha', self.window_alpha);
        self.overrideredirect(True)

        self._offset_x = 0;
        self._offset_y = 0
        self.bind('<Button-1>', self.click_window);
        self.bind('<B1-Motion>', self.drag_window)

        self.create_widgets()
        self.load_tasks()
        self.update_clock();
        self.update_timers()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        if self.last_mini_mode_state: self.toggle_mini_mode()

    def create_widgets(self):
        self.main_frame = tk.Frame(self, bg=BG_COLOR)
        self.mini_frame = tk.Frame(self, bg=BG_COLOR)

        self.control_frame = tk.Frame(self, bg=BG_COLOR)
        self.mini_mode_button = tk.Button(self.control_frame, text="─", bg=BG_COLOR, fg=TEXT_COLOR,
                                          font=("Arial", 12, "bold"), relief="flat", command=self.toggle_mini_mode)
        self.mini_mode_button.pack(side="left")
        quit_button = tk.Button(self.control_frame, text="✕", bg=BG_COLOR, fg=WARN_COLOR, font=("Arial", 12, "bold"),
                                relief="flat", activebackground=WARN_COLOR, activeforeground=BG_COLOR,
                                command=self.on_closing)
        quit_button.pack(side="right")
        self.control_frame.place(x=0, y=0, relwidth=1.0, height=30)

        # --- 填充主框架 (Normal Mode UI) ---
        self.clock_label = tk.Label(self.main_frame, text="", font=FONT_LARGE, fg=ACCENT_COLOR, bg=BG_COLOR)
        self.clock_label.pack(pady=(20, 10))
        sw_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        self.stopwatch_label = tk.Label(sw_frame, text="00:00:00", font=FONT_NORMAL, fg=TEXT_COLOR, bg=BG_COLOR,
                                        width=10);
        self.stopwatch_label.pack(side="left", padx=5)
        self.sw_toggle_button = tk.Button(sw_frame, text="▶", command=self.toggle_stopwatch, fg=TEXT_COLOR, bg=BG_COLOR,
                                          relief="flat");
        self.sw_toggle_button.pack(side="left")
        tk.Button(sw_frame, text="■", command=self.stop_stopwatch, fg=TEXT_COLOR, bg=BG_COLOR, relief="flat").pack(
            side="left")
        tk.Button(sw_frame, text="R", command=self.reset_stopwatch, fg=TEXT_COLOR, bg=BG_COLOR, relief="flat").pack(
            side="left")
        sw_frame.pack(pady=5)
        cd_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        self.countdown_label = tk.Label(cd_frame, text="00:00", font=FONT_NORMAL, fg=TEXT_COLOR, bg=BG_COLOR, width=10);
        self.countdown_label.pack(side="left", padx=5)
        self.countdown_entry = tk.Entry(cd_frame, width=4, bg=TEXT_COLOR, fg=BG_COLOR, relief="flat", justify="center");
        self.countdown_entry.insert(0, "25");
        self.countdown_entry.pack(side="left")
        tk.Button(cd_frame, text="Set", command=self.set_countdown, fg=TEXT_COLOR, bg=BG_COLOR, relief="flat").pack(
            side="left")
        self.cd_toggle_button = tk.Button(cd_frame, text="▶", command=self.toggle_countdown, fg=TEXT_COLOR, bg=BG_COLOR,
                                          relief="flat");
        self.cd_toggle_button.pack(side="left")
        tk.Button(cd_frame, text="R", command=self.reset_countdown, fg=TEXT_COLOR, bg=BG_COLOR, relief="flat").pack(
            side="left")
        cd_frame.pack(pady=5)
        alpha_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        tk.Label(alpha_frame, text="T:", font=FONT_NORMAL, fg=TEXT_COLOR, bg=BG_COLOR).pack(side="left", padx=(10, 0))
        self.alpha_slider = tk.Scale(alpha_frame, from_=0.2, to=1.0, resolution=0.05, orient="horizontal", bg=BG_COLOR,
                                     fg=TEXT_COLOR, troughcolor=TEXT_COLOR, highlightthickness=0,
                                     command=self.set_alpha)
        self.alpha_slider.set(self.window_alpha);
        self.alpha_slider.pack(side="left", fill="x", expand=True, padx=10)
        alpha_frame.pack(fill="x", pady=5)
        self.task_text = tk.Text(self.main_frame, height=10, bg="#3b4048", fg=TEXT_COLOR, insertbackground=TEXT_COLOR,
                                 relief="flat", font=FONT_NORMAL, wrap="word")
        self.task_text.pack(pady=10, padx=10, fill="both", expand=True)

        # --- 填充迷你框架 (Mini Mode UI) ---
        self.clock_label_mini = tk.Label(self.mini_frame, text="", font=FONT_LARGE, fg=ACCENT_COLOR, bg=BG_COLOR)
        self.clock_label_mini.pack(pady=(10, 0))
        self.mini_stopwatch_label = tk.Label(self.mini_frame, text="", font=FONT_MINI_TIMER, fg=ACTIVE_COLOR,
                                             bg=BG_COLOR)
        self.mini_stopwatch_label.pack(pady=0, ipady=0)
        self.mini_countdown_label = tk.Label(self.mini_frame, text="", font=FONT_MINI_TIMER, fg=ACTIVE_COLOR,
                                             bg=BG_COLOR)
        self.mini_countdown_label.pack(pady=0, ipady=0)

        # 默认显示主框架
        self.main_frame.pack(fill="both", expand=True, pady=(30, 0))

    def toggle_mini_mode(self):
        self.is_mini_mode = not self.is_mini_mode
        if self.is_mini_mode:
            self.main_frame.pack_forget()
            self.mini_frame.pack(fill="both", expand=True)
            self.geometry(f"{WINDOW_WIDTH_MINI}x{WINDOW_HEIGHT_MINI}")
            self.mini_mode_button.config(text="□")
        else:
            self.mini_frame.pack_forget()
            self.main_frame.pack(fill="both", expand=True, pady=(30, 0))
            self.geometry(f"{WINDOW_WIDTH_NORMAL}x{WINDOW_HEIGHT_NORMAL}")
            self.mini_mode_button.config(text="─")
        self.control_frame.lift()

    def click_window(self, event):
        draggable_widgets = (tk.Tk, tk.Frame, tk.Label)
        if isinstance(event.widget, draggable_widgets):
            self._offset_x = event.x;
            self._offset_y = event.y
        else:
            self._offset_x = None;
            self._offset_y = None

    def drag_window(self, event):
        if self._offset_x is not None and self._offset_y is not None:
            x = self.winfo_pointerx() - self._offset_x;
            y = self.winfo_pointery() - self._offset_y
            self.geometry(f"+{x}+{y}")

    def set_alpha(self, value):
        self.attributes('-alpha', float(value))

    def update_clock(self):
        current_time = time.strftime('%H:%M:%S')
        self.clock_label.config(text=current_time)
        if hasattr(self, 'clock_label_mini'): self.clock_label_mini.config(text=current_time)  # 检查是否存在
        self.after(1000, self.update_clock)

    def save_config(self):
        config_data = {"x": self.winfo_x(), "y": self.winfo_y(), "alpha": self.attributes('-alpha'),
                       "mini_mode": self.is_mini_mode}
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f)
        except Exception as e:
            print(f"保存配置时出错: {e}")

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
            self.window_x = config_data.get("x", 100);
            self.window_y = config_data.get("y", 100)
            self.window_alpha = config_data.get("alpha", 0.95);
            self.last_mini_mode_state = config_data.get("mini_mode", False)
        except (FileNotFoundError, json.JSONDecodeError):
            self.window_x, self.window_y, self.window_alpha, self.last_mini_mode_state = 100, 100, 0.95, False

    def on_closing(self):
        self.save_config(); self.save_tasks(); self.destroy()

    def save_tasks(self):
        try:
            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                f.write(self.task_text.get("1.0", tk.END))
        except Exception as e:
            print(f"保存任务时出错: {e}")

    def load_tasks(self):
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            if content.strip(): self.task_text.insert(tk.END, content)
        except FileNotFoundError:
            self.task_text.insert(tk.END, "- 在这里记录你的待办事项 -")
        except Exception as e:
            print(f"加载任务时出错: {e}")

    def _format_time(self, seconds, show_hours=True):
        if seconds < 0: seconds = 0
        m, s = divmod(int(seconds), 60);
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if show_hours else f"{m:02d}:{s:02d}"

    def update_timers(self):
        if self.stopwatch_running:
            self.stopwatch_time += 1;
            formatted_time = self._format_time(self.stopwatch_time)
            self.stopwatch_label.config(text=formatted_time)
            if self.is_mini_mode and hasattr(self, 'mini_stopwatch_label'): self.mini_stopwatch_label.config(
                text=f"⏱️ {formatted_time}")
        elif self.is_mini_mode and hasattr(self, 'mini_stopwatch_label'):
            self.mini_stopwatch_label.config(text="")
        if self.countdown_running:
            if self.countdown_seconds > 0:
                self.countdown_seconds -= 1;
                formatted_time = self._format_time(self.countdown_seconds, show_hours=False)
                self.countdown_label.config(text=formatted_time)
                if self.is_mini_mode and hasattr(self, 'mini_countdown_label'): self.mini_countdown_label.config(
                    text=f"⏳ {formatted_time}")
            else:
                self.countdown_running = False;
                self.flash_window(3);
                self.cd_toggle_button.config(text="▶");
                self.countdown_label.config(fg=TEXT_COLOR)
                if self.is_mini_mode and hasattr(self, 'mini_countdown_label'): self.mini_countdown_label.config(
                    text="")
        elif self.is_mini_mode and hasattr(self, 'mini_countdown_label'):
            self.mini_countdown_label.config(text="")
        self.after(1000, self.update_timers)

    def toggle_stopwatch(self):
        self.stopwatch_running = not self.stopwatch_running
        if self.stopwatch_running:
            self.stopwatch_label.config(fg=ACTIVE_COLOR); self.sw_toggle_button.config(text="⏸")
        else:
            self.stopwatch_label.config(fg=TEXT_COLOR); self.sw_toggle_button.config(text="▶")

    def stop_stopwatch(self):
        self.stopwatch_running = False;
        self.stopwatch_label.config(fg=TEXT_COLOR);
        self.sw_toggle_button.config(text="▶")

    def reset_stopwatch(self):
        self.stopwatch_running = False;
        self.stopwatch_time = 0;
        self.stopwatch_label.config(text=self._format_time(0), fg=TEXT_COLOR);
        self.sw_toggle_button.config(text="▶")

    def set_countdown(self):
        try:
            self.initial_countdown_seconds = int(self.countdown_entry.get()) * 60; self.reset_countdown()
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的分钟数（整数）。")

    def toggle_countdown(self):
        if self.initial_countdown_seconds > 0:
            self.countdown_running = not self.countdown_running
            if self.countdown_running:
                self.countdown_label.config(fg=ACTIVE_COLOR); self.cd_toggle_button.config(text="⏸")
            else:
                self.countdown_label.config(fg=TEXT_COLOR); self.cd_toggle_button.config(text="▶")

    def reset_countdown(self):
        self.countdown_running = False;
        self.countdown_seconds = self.initial_countdown_seconds
        self.countdown_label.config(text=self._format_time(self.countdown_seconds, show_hours=False), fg=TEXT_COLOR);
        self.cd_toggle_button.config(text="▶")

    def flash_window(self, count):
        if count <= 0 or self.is_mini_mode: return
        current_color = self.cget("bg");
        new_color = WARN_COLOR if current_color == BG_COLOR else BG_COLOR
        self.config(bg=new_color)
        self.after(300, lambda: self.flash_window(count - 1))


if __name__ == "__main__":
    app = TimeManagerApp()
    app.mainloop()

# =======================================================================
# ========================= 完整代码 END ================================
# =======================================================================