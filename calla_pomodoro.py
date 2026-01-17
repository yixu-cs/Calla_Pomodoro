import tkinter as tk
from tkinter import messagebox
from tkinter import font as tkfont
import random
import time
import threading
import os
import json
import platform

class PersonalizedTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Calla番茄钟")
        # window size
        self.root.geometry("700x550")

        # --- 系统检测 ---
        self.system = platform.system()
        self.is_mac = self.system == "Darwin"
        
        # === 1. 核心修改：字体放大策略 ===
        # Windows保持1.0，Mac放大1.3倍 (你可以改为 1.4 或 1.5 试试更大)
        self.scale_factor = 1.35 if self.is_mac else 1.0
        
        # 字体家族
        self.main_font_family = "PingFang SC" if self.is_mac else "微软雅黑"
        self.icon_font_family = "Apple Color Emoji" if self.is_mac else "Segoe UI Emoji"
        
        # 颜色配置 (Mac加深策略)
        self.colors = {
            "bg_window": "#F5F5F5" if self.is_mac else "#f0f0f0",
            "bg_rest": "#F1F8E9" if self.is_mac else "#f9fbe7",
            "text_primary": "#1C1C1C" if self.is_mac else "#333333",
            "text_secondary": "#424242" if self.is_mac else "#555555",
            "text_quote": "#424242" if self.is_mac else "#757575", # 语录再加深一点
            "text_hint": "#616161" if self.is_mac else "#999999",
            "accent_focus": "#E64A19",
            "accent_rest": "#00897B",
            "highlight": "#FF7043"
        }

        self.root.configure(bg=self.colors["bg_window"])

        try:
            self.root.iconbitmap("fox.ico") 
        except Exception as e:
            print(f"图标加载失败: {e}")
        
        self.total_rounds = 4 
        self.current_round = 1
        self.is_focusing = True 
        self.is_running = False
        self.remaining_seconds = 0
        self.last_focus_min = 45 
        self.last_break_min = 10 
        
        self.data = None
        if os.path.exists("data.json"):
            try:
                with open("data.json", "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                pass    
        
        self.focus_history = []
        self.harass_count = 0
        
        self.setup_initial_rounds_ui()

    # === 2. 核心修改：字体大小计算助手 ===
    def s(self, size):
        """Scale size: 根据系统自动计算字体大小"""
        return int(size * self.scale_factor)

    def get_random_line(self, pattern, default_list, count=1):
        data = None
        if self.data is not None and pattern in self.data:
            data = self.data[pattern]
            if isinstance(data, list) and data:
                return random.sample(data, count)
        return random.sample(default_list, count)

    # --- 界面 1：初始设置 ---
    def setup_initial_rounds_ui(self):
        self.clear_window()
        
        # 使用 self.s() 包裹字号
        tk.Label(self.root, text="🍅\n📬👀📓🦜\n🌀🦊👗🛀", 
                 font=(self.icon_font_family if self.is_mac else "微软雅黑", self.s(24)), 
                 fg=self.colors["highlight"], bg=self.colors["bg_window"]).pack(pady=self.s(40))
        
        tk.Label(self.root, text="叽叽喳喳的笨鸟难得耐下心来做事，我会好好监督的。\n说吧，要专注几轮？", 
                 font=(self.main_font_family, self.s(14)), 
                 fg=self.colors["text_primary"], bg=self.colors["bg_window"]).pack(pady=10)
        
        input_frame = tk.Frame(self.root, bg=self.colors["bg_window"])
        input_frame.pack(pady=10)
        
        self.rounds_var = tk.IntVar(value=4)
        entry = tk.Entry(input_frame, textvariable=self.rounds_var, width=5, 
                         font=(self.main_font_family, self.s(14)), justify='center',
                         fg=self.colors["text_primary"])
        entry.pack()
        
        tk.Button(self.root, text="确定", command=self.confirm_rounds, 
                  bg="#FFAB91", fg="black" if self.is_mac else "white", 
                  font=(self.main_font_family, self.s(12), "bold"), width=10).pack(pady=self.s(30))

    def confirm_rounds(self):
        try:
            r = self.rounds_var.get()
            if r > 0:
                self.total_rounds = r
                self.setup_config_ui()
            else:
                messagebox.showwarning("提示", "轮数至少为1哦")
        except:
            messagebox.showerror("错误", "请输入数字")

    # --- 界面 2：配置界面 ---
    def setup_config_ui(self):
        self.clear_window()
        self.root.configure(bg=self.colors["bg_window"])
        
        if self.current_round > self.total_rounds:
             self.show_daily_report()
             return

        mode_text = f"第 {self.current_round} / {self.total_rounds} 轮"
        tk.Label(self.root, text=mode_text, font=(self.main_font_family, self.s(16), "bold"), 
                 fg=self.colors["text_secondary"], bg=self.colors["bg_window"]).pack(pady=self.s(20))
        
        state_text = "💪 准备好了就开始吧" if self.is_focusing else "☕ 去休息一会吧"
        color = self.colors["accent_focus"] if self.is_focusing else self.colors["accent_rest"]
        
        tk.Label(self.root, text=state_text, font=(self.main_font_family, self.s(20), "bold"), 
                 fg=color, bg=self.colors["bg_window"]).pack(pady=5)

        tk.Label(self.root, text="本轮时长 (分钟):", font=(self.main_font_family, self.s(12)),
                 fg=self.colors["text_primary"], bg=self.colors["bg_window"]).pack(pady=5)
        
        default_val = self.last_focus_min if self.is_focusing else self.last_break_min
        self.time_var = tk.IntVar(value=default_val)
        entry = tk.Entry(self.root, textvariable=self.time_var, width=8, 
                         font=("Arial", self.s(16)), justify='center', fg=self.colors["text_primary"])
        entry.pack(pady=5)
        
        tip_text = ""
        if self.is_focusing:
            tip_text =  "🦊：" + self.get_random_line("begin_focus", [
                "新一轮的专注开始了。心无旁骛地投入就好。",
                "专注的时间到了。先把任务完成再想奖励的事吧"
            ])[0]
        else:
            tip_text =  "🦊：" + self.get_random_line("begin_rest", [
                "包里给你装了点心和零食，可以去吃一点。",
                "要是有尾巴抱就好了？可惜现在没有，就先玩玩那两个毛绒球吧。"
            ])[0]
        
        tk.Label(self.root, text=tip_text, fg=self.colors["text_quote"], bg=self.colors["bg_window"],
                 font=(self.main_font_family, self.s(12), "italic"), wraplength=self.s(600)).pack(pady=self.s(20))

        btn_bg = color
        btn_fg = "white"
        if self.is_mac:
            btn_bg = "systemTransparent"
            btn_fg = "black"

        tk.Button(self.root, text="开始计时", command=self.start_timer, 
                  bg=btn_bg, fg=btn_fg, 
                  font=(self.main_font_family, self.s(14), "bold"), width=15).pack(pady=self.s(20))

    # --- 统计报告界面 ---
    def show_daily_report(self):
        self.clear_window()
        tk.Label(self.root, text="🎉 📓🦜总结", font=(self.main_font_family, self.s(30), "bold"), 
                 fg=self.colors["highlight"], bg=self.colors["bg_window"]).pack(pady=self.s(30))
        
        total_time = 0
        effective_time = 0
        for record in self.focus_history:
            duration = record['duration']
            rating = record['rating']
            weight = rating * 0.2  
            total_time += duration
            effective_time += duration * weight
            
        report_text = (
            f"计划轮数：{self.total_rounds}\n"
            f"物理专注时长：{total_time} 分钟\n\n"
            f"🌟 有效专注时长：{effective_time:.1f} 分钟"
        )
        
        tk.Label(self.root, text=report_text, font=(self.main_font_family, self.s(14)), 
                 fg=self.colors["text_primary"], bg=self.colors["bg_window"], justify="center").pack(pady=self.s(20))
        
        tk.Label(self.root, text="(有效时长 = 时长 × 专注度权重)", 
                 fg=self.colors["text_hint"], bg=self.colors["bg_window"], font=(self.main_font_family, self.s(10))).pack()
        
        end_quote = "🦊：" + self.get_random_line("complete", [
            "今天确实做得不错。好了，去休息吧。嘴角都要飞到天上去了。",
            "任务完成了，那些压力也该像尘埃一样拍掉了。去洗个澡，好梦。"
        ])[0]

        quote_font = ("楷体", self.s(14), "bold") if not self.is_mac else (self.main_font_family, self.s(14), "bold")
        
        tk.Label(self.root, text=end_quote, font=quote_font, fg="#5D4037", bg=self.colors["bg_window"],
                 wraplength=self.s(550), justify="center").pack(pady=self.s(20))
        
        tk.Button(self.root, text="明天见 (退出)", command=self.root.quit, 
                  bg="#E0E0E0", fg="black", width=15).pack(pady=self.s(40))
        
        tk.Button(self.root, text="开始下一轮专注", command=self.reset_app, 
                  relief="flat", fg="blue", bg=self.colors["bg_window"]).pack()

    # --- 界面 3：计时中 ---
    def setup_timer_ui(self):
        self.clear_window()
        
        bg_color = self.colors["bg_rest"] if not self.is_focusing else self.colors["bg_window"]
        self.root.configure(bg=bg_color)

        if self.is_focusing:
            self.setup_focus_layout(bg_color)
        else:
            self.setup_rest_layout(bg_color)
            
        # 计时器字体要特别大
        font_size = self.s(50) if self.is_focusing else self.s(40)
        
        self.timer_label = tk.Label(self.root, text="00:00", font=("Helvetica", font_size, "bold"), 
                                    bg=bg_color, fg=self.colors["text_primary"])
        
        if self.is_focusing:
            self.timer_label.pack(pady=self.s(30))
        else:
            self.timer_label.pack(pady=self.s(10)) 

        control_frame = tk.Frame(self.root, bg=bg_color)
        control_frame.pack(side=tk.BOTTOM, pady=self.s(30))
        
        tk.Button(control_frame, text="暂停/继续", command=self.toggle_pause, width=10, fg="black").pack(side=tk.LEFT, padx=10)
        tk.Button(control_frame, text="提前结束", command=self.finish_early, width=10, fg="black").pack(side=tk.LEFT, padx=10)

    # --- 专注模式布局 ---
    def setup_focus_layout(self, bg_color):
        tk.Label(self.root, text="🌳 专注进行中...", font=(self.main_font_family, self.s(14)), 
                 fg=self.colors["accent_focus"], bg=bg_color).pack(pady=self.s(20))
        
        quote_font = ("楷体", self.s(12)) if not self.is_mac else (self.main_font_family, self.s(12))
        self.fox_feedback_label = tk.Label(self.root, text="", font=quote_font, 
                                           fg="#5D4037", bg=bg_color, wraplength=self.s(500))
        self.fox_feedback_label.pack(pady=10)
        
        tk.Button(self.root, text="👉 骚扰小狐狸", command=self.harass_fox, 
                  bg="#FFCCBC", fg="black", relief="groove").pack(pady=10)

    def harass_fox(self):
        self.harass_count += 1
        pattern = "during_focus_reminder" if self.harass_count <= 5 else "during_focus_encouragement"
        msg = self.get_random_line(pattern, [
            "我是说过抬头就能看到我，但也不用抬这么多次。",
            "我怎么不知道，你把要做的事情写到了我的脸上？",
            "再被我抓到一次走神，今天的点心就没有了。"
        ])[0]
        self.fox_feedback_label.config(text=f"🦊：{msg}")

    # --- 休息模式布局 ---
    def setup_rest_layout(self, bg_color):
        content_frame = tk.Frame(self.root, bg=bg_color)
        content_frame.pack(expand=True, fill="both", padx=20, pady=10)

        columns = [
            {"title": "🦊", "pattern": "qsl_quote", "count": 2, "default": ["你是我藏在密林的春天。", "窗户没关好，飞进来一只笨鸟。"], "color": "#5D4037"},
            {"title": "📜", "pattern": "tagore_list", "count": 1, "default": ["生如夏花之绚烂。", "天空没有翅膀的痕迹。"], "color": "#00695C"},
            {"title": "🧘", "pattern": "rest_activities", "count": 3, "default": ["👀 滴个眼药水吧", "🍵 泡杯热茶", "🪜 爬楼梯动一动"], "color": "#EF6C00"}
        ]

        for col_data in columns:
            frame = tk.Frame(content_frame, bg="white", relief="ridge", bd=2)
            frame.pack(side=tk.LEFT, expand=True, fill="both", padx=5)
            
            tk.Label(frame, text=col_data["title"], bg="#E0E0E0", 
                     font=(self.icon_font_family if self.is_mac else "微软雅黑", self.s(12), "bold")).pack(fill="x", ipady=5)
            
            items = self.get_random_line(col_data["pattern"], col_data["default"], col_data["count"])
            text_content = "\n\n".join([f"• {item}" for item in items])
            text_content = text_content.replace("\\n", "\n") 
            
            lbl = tk.Label(frame, text=text_content, bg="white", fg=col_data["color"], 
                           font=(self.main_font_family, self.s(11)), wraplength=self.s(180), 
                           justify="left" if col_data["count"] > 1 else "center")
            lbl.pack(expand=True, fill="both", padx=5)

    def start_timer(self):
        try:
            minutes = self.time_var.get()
        except:
            return 
        
        if self.is_focusing:
            self.last_focus_min = minutes
        else:
            self.last_break_min = minutes
            
        self.remaining_seconds = minutes * 60
        self.is_running = True
        self.setup_timer_ui()
        
        self.timer_thread = threading.Thread(target=self.run_countdown)
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def run_countdown(self):
        while self.remaining_seconds > 0:
            if self.is_running:
                mins, secs = divmod(self.remaining_seconds, 60)
                time_str = f"{mins:02}:{secs:02}"
                self.root.after(0, lambda: self.timer_label.config(text=time_str))
                time.sleep(1)
                self.remaining_seconds -= 1
            else:
                time.sleep(0.1)
        self.root.after(0, self.on_time_up)

    def flash_screen(self):
        try:
            flash_win = tk.Toplevel(self.root)
            flash_win.overrideredirect(True)
            flash_win.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
            flash_win.attributes("-topmost", True)
            flash_win.attributes("-alpha", 0.3)
            color = "#A5D6A7" if not self.is_focusing else "#FFCC80"
            flash_win.configure(bg=color)
            flash_win.after(600, flash_win.destroy)
        except Exception:
            pass

    def on_time_up(self):
        self.is_running = False
        self.flash_screen()
        self.root.deiconify()
        self.root.attributes('-topmost', True)
        self.root.update()
        self.root.after(1000, lambda: self.root.attributes('-topmost', False))
        self.root.configure(bg=self.colors["bg_window"]) 

        if self.is_focusing:
            self.show_rating_ui()
        else:
            self.is_focusing = True
            self.current_round += 1
            self.setup_config_ui()

    # --- 专注评分界面 ---
    def show_rating_ui(self):
        self.clear_window()
        tk.Label(self.root, text="🍅 专注结束了，去喝点茶，吃点点心吧", 
                 font=(self.main_font_family, self.s(20), "bold"), 
                 fg=self.colors["accent_focus"], bg=self.colors["bg_window"]).pack(pady=self.s(30))
        
        tk.Label(self.root, text="你觉得自己刚刚做得怎么样 (1-5)", 
                 font=(self.main_font_family, self.s(14)), 
                 fg=self.colors["text_primary"], bg=self.colors["bg_window"]).pack(pady=10)
        
        tk.Label(self.root, text="1=心不在焉 ... 5=极度专注", 
                 font=(self.main_font_family, self.s(10)), 
                 fg=self.colors["text_hint"], bg=self.colors["bg_window"]).pack(pady=5)
        
        btn_frame = tk.Frame(self.root, bg=self.colors["bg_window"])
        btn_frame.pack(pady=20)
        
        for i in range(1, 6):
            tk.Button(btn_frame, text=str(i), font=("Arial", self.s(14), "bold"), width=4, height=2,
                      bg="#FFCCBC", fg="black", 
                      command=lambda r=i: self.submit_rating(r)).pack(side=tk.LEFT, padx=10)

    def submit_rating(self, rating):
        self.focus_history.append({'duration': self.last_focus_min, 'rating': rating})
        self.is_focusing = False
        self.harass_count = 0
        self.setup_config_ui()
        pattern = "high_quality" if rating >= 4 else "low_quality"
        self.show_custom_notification(pattern)

    def show_custom_notification(self, pattern):
        popup = tk.Toplevel(self.root)
        popup.title("🦊")
        popup.attributes("-topmost", True)
        
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = self.s(320), self.s(160)
        x = sw - w - 20
        y = sh - h - 80 
        popup.geometry(f"{w}x{h}+{x}+{y}")
        
        bg_color = "#e8f5e9" if not self.is_focusing else "#fff3e0"
        popup.configure(bg=bg_color)
        
        msg = self.get_random_line(pattern, 
            ["难得没有偷懒，表现得还不错。", "我看得出来，你是真的在努力。", "允许自己有笨拙的时候。", "你这点小小的失误，没什么大不了的。", "你不是一台只允许盈利的机器。"])[0]
        
        tk.Label(popup, text=msg, wraplength=self.s(280), font=(self.main_font_family, self.s(12)), 
                 bg=bg_color, fg=self.colors["text_primary"], justify="center").pack(expand=True, pady=10)
        
        tk.Button(popup, text="🦜：好的狐狐", command=popup.destroy, bg="white", fg="black", relief="groove").pack(pady=10)

    def toggle_pause(self):
        self.is_running = not self.is_running

    def finish_early(self):
        self.remaining_seconds = 0

    def reset_app(self):
        self.current_round = 1
        self.is_focusing = True
        self.setup_initial_rounds_ui()
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PersonalizedTimer(root)
    root.mainloop()