import tkinter as tk
from tkinter import messagebox
from tkinter import font as tkfont
import random
import time
import threading
import os
import json

class PersonalizedTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Calla番茄钟")
        # window size
        self.root.geometry("700x500")
            
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
        
        # load data
        self.data = None
        if os.path.exists("data.json"):
            try:
                with open("data.json", "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                pass    
        
        # 记录专注历史：[{'duration': 分钟, 'rating': 1-5}]
        self.focus_history = []
        # harass times
        self.harass_count = 0
        
        self.base_font = tkfont.Font(family="微软雅黑", size=12)
        
        self.setup_initial_rounds_ui()

    # --- 辅助功能：读取文件 ---
    def get_random_line(self, pattern, default_list):
        """尝试从JSON文件中读取列表，如果文件不存在或解析失败则使用默认列表"""
        data = None
        if self.data is not None and pattern in self.data:
            data = self.data[pattern]
            if isinstance(data, list) and data:
                return random.choice(data)
        
        # 如果文件不存在、JSON格式错误或列表为空，使用默认列表
        return random.choice(default_list)

    # --- 界面 1：初始设置 ---
    def setup_initial_rounds_ui(self):
        self.clear_window()
        tk.Label(self.root, text="🍅\n📬👀📓🦜\n🌀🦊👗🛀", font=("微软雅黑", 24, "bold"), fg="#FF7043").pack(pady=40)
        tk.Label(self.root, text="叽叽喳喳的笨鸟难得耐下心来做事，我会好好监督的。\n说吧，要专注几轮？", font=("微软雅黑", 14)).pack(pady=10)
        
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10)
        self.rounds_var = tk.IntVar(value=4)
        entry = tk.Entry(input_frame, textvariable=self.rounds_var, width=5, font=("微软雅黑", 14), justify='center')
        entry.pack()
        
        tk.Button(self.root, text="确定", command=self.confirm_rounds, 
                  bg="#FFAB91", fg="white", font=("微软雅黑", 12, "bold"), width=10).pack(pady=30)

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

    # --- 界面 2：配置界面（准备开始） ---
    def setup_config_ui(self):
        self.clear_window()
        
        # === 一天结束后的统计 ===
        if self.current_round > self.total_rounds:
             self.show_daily_report()
             return

        # 顶部信息
        mode_text = f"第 {self.current_round} / {self.total_rounds} 轮"
        tk.Label(self.root, text=mode_text, font=("微软雅黑", 16, "bold"), fg="#555").pack(pady=20)
        
        state_text = "💪 准备好了就开始吧" if self.is_focusing else "☕ 去休息一会吧"
        color = "#e64a19" if self.is_focusing else "#00897b"
        tk.Label(self.root, text=state_text, font=("微软雅黑", 20, "bold"), fg=color).pack(pady=5)

        # 时间设置
        tk.Label(self.root, text="本轮时长 (分钟):", font=("微软雅黑", 12)).pack(pady=5)
        default_val = self.last_focus_min if self.is_focusing else self.last_break_min
        self.time_var = tk.IntVar(value=default_val)
        entry = tk.Entry(self.root, textvariable=self.time_var, width=8, font=("Arial", 16), justify='center')
        entry.pack(pady=5)
        
        # === 休息结束/专注开始前的语录 ===
        tip_text = ""
        quote_fg = "#757575"
        
        if self.is_focusing:
            tip_text =  "🦊：" + self.get_random_line("begin_focus", [
                "新一轮的专注开始了。心无旁骛地投入就好。",
                "专注的时间到了。先把任务完成再想奖励的事吧"
            ])
        else:
            tip_text =  "🦊：" + self.get_random_line("begin_rest", [
                "包里给你装了点心和零食，可以去吃一点。",
                "要是有尾巴抱就好了？可惜现在没有，就先玩玩那两个毛绒球吧。"
            ])
        
        tk.Label(self.root, text=tip_text, fg=quote_fg, font=("微软雅黑", 12, "italic"), wraplength=600).pack(pady=20)

        tk.Button(self.root, text="开始计时", command=self.start_timer, 
                  bg=color, fg="white", font=("微软雅黑", 14, "bold"), width=15).pack(pady=20)

    # --- 统计报告界面 ---
    def show_daily_report(self):
        self.clear_window()
        tk.Label(self.root, text="🎉 📓🦜总结", font=("微软雅黑", 30, "bold"), fg="#FF7043").pack(pady=30)
        
        total_time = 0
        effective_time = 0
        
        # 2. 核心：遍历历史记录进行计算
        for record in self.focus_history:
            duration = record['duration']
            rating = record['rating']
            # 计算权重：5分=1.0, 1分=0.2
            weight = rating * 0.2  
            
            total_time += duration
            effective_time += duration * weight
            
        report_text = (
            f"计划轮数：{self.total_rounds}\n"
            f"物理专注时长：{total_time} 分钟\n\n"
            f"🌟 有效专注时长：{effective_time:.1f} 分钟"
        )
        
        tk.Label(self.root, text=report_text, font=("微软雅黑", 14), justify="center").pack(pady=20)
        tk.Label(self.root, text="(有效时长 = 时长 × 专注度权重)", fg="#999").pack()
        
        end_quote = "🦊：" + self.get_random_line("complete", [
            "今天确实做得不错。好了，去休息吧。嘴角都要飞到天上去了。",
            "任务完成了，那些压力也该像尘埃一样拍掉了。去洗个澡，好梦。"
        ])

        # 展示齐司礼的夸奖
        # 使用 wraplength=500 防止句子太长超出屏幕
        tk.Label(self.root, text=end_quote, font=("楷体", 14, "bold"), fg="#5D4037", 
                 wraplength=550, justify="center").pack(pady=20)
        
        # 3. 核心：展示完后由你决定是否退出
        tk.Button(self.root, text="明天见 (退出)", command=self.root.quit, bg="#E0E0E0", width=15).pack(pady=40)
        tk.Button(self.root, text="开始下一轮专注", command=self.reset_app, relief="flat", fg="blue").pack()

    # --- 界面 3：计时中 ---
    def setup_timer_ui(self):
        self.clear_window()
        
        # 根据状态加载不同的布局
        if self.is_focusing:
            self.setup_focus_layout()
        else:
            self.setup_rest_layout()
            
        # 计时器显示（通用）
        # 如果是休息模式，计时器稍微小一点放在顶部；专注模式放在中间
        font_size = 50 if self.is_focusing else 40
        bg_color = None if self.is_focusing else "#f9fbe7" # 休息背景色
        
        if not self.is_focusing:
             self.root.configure(bg="#f9fbe7") # 改变整个窗口背景
        else:
             self.root.configure(bg="#f0f0f0")

        self.timer_label = tk.Label(self.root, text="00:00", font=("Helvetica", font_size, "bold"), bg=bg_color or "#f0f0f0")
        
        if self.is_focusing:
            self.timer_label.pack(pady=30)
        else:
            self.timer_label.pack(pady=10) # 休息时放在最上面

        # 控制按钮
        control_frame = tk.Frame(self.root, bg=bg_color or "#f0f0f0")
        control_frame.pack(side=tk.BOTTOM, pady=30)
        
        tk.Button(control_frame, text="暂停/继续", command=self.toggle_pause, width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(control_frame, text="提前结束", command=self.finish_early, width=10).pack(side=tk.LEFT, padx=10)

    # --- 专注模式布局 ---
    def setup_focus_layout(self):
        tk.Label(self.root, text="🌳 专注进行中...", font=("微软雅黑", 14), fg="#e64a19").pack(pady=20)
        
        # === 骚扰小狐狸 ===
        self.fox_feedback_label = tk.Label(self.root, text="", font=("楷体", 12), fg="#5D4037", wraplength=500)
        self.fox_feedback_label.pack(pady=10)
        
        tk.Button(self.root, text="👉 骚扰小狐狸", command=self.harass_fox, 
                  bg="#FFCCBC", fg="#D84315", relief="groove").pack(pady=10)

    def harass_fox(self):
        self.harass_count += 1
        if self.harass_count <= 5:
            pattern = "during_focus_reminder"
        else:
            pattern = "during_focus_encouragement"
        msg = self.get_random_line(pattern, [
            "我是说过抬头就能看到我，但也不用抬这么多次。",
            "我怎么不知道，你把要做的事情写到了我的脸上？",
            "再被我抓到一次走神，今天的点心就没有了。"
        ])
        self.fox_feedback_label.config(text=f"🦊：{msg}")

    # --- 休息模式布局 ---
    def setup_rest_layout(self):
        # === 三列布局展示语录 ===
        content_frame = tk.Frame(self.root, bg="#f9fbe7")
        content_frame.pack(expand=True, fill="both", padx=20, pady=10)

        # 定义三列的数据源
        columns = [
            {
                "title": "🦊", 
                "pattern": "qsl_quote", 
                "count": 2,
                "default": ["你是我藏在密林的春天。", "窗户没关好，飞进来一只笨鸟。"], 
                "color": "#5D4037"
            },
            {
                "title": "📜", 
                "pattern": "tagore_list", 
                "count": 1,
                "default": ["生如夏花之绚烂。", "天空没有翅膀的痕迹。"], 
                "color": "#00695C"
            },
            {
                "title": "🧘", 
                "pattern": "rest_activities", 
                "count": 3, 
                "default": ["👀 滴个眼药水吧", "🍵 泡杯热茶", "🪜 爬楼梯动一动"], 
                "color": "#EF6C00"
            }
        ]

        for col_data in columns:
            frame = tk.Frame(content_frame, bg="white", relief="ridge", bd=2)
            frame.pack(side=tk.LEFT, expand=True, fill="both", padx=5)
            
            # 标题
            tk.Label(frame, text=col_data["title"], bg="#E0E0E0", font=("微软雅黑", 12, "bold")).pack(fill="x", ipady=5)
            
            if col_data["count"] > 1:
                # 获取列表
                items = []
                for i in range(col_data["count"]):
                    items.append(self.get_random_line(col_data["pattern"], col_data["default"]))
                # 拼接成字符串，中间用换行符分隔
                # 这里加了 "• " 让它看起来像个列表
                text_content = "\n\n".join([f"• {item}" for item in items])
            else:
                text_content = self.get_random_line(col_data["pattern"], col_data["default"])
            
            # 处理可能的换行符
            text_content = text_content.replace("\\n", "\n") 
            
            lbl = tk.Label(frame, text=text_content, bg="white", fg=col_data["color"], 
                           font=("微软雅黑", 11), wraplength=180, justify="left" if col_data["count"] > 1 else "center")
            lbl.pack(expand=True, fill="both", padx=5)

    # --- 计时器逻辑 ---
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
                # 使用 after 确保线程安全地更新 UI
                self.root.after(0, lambda: self.timer_label.config(text=time_str))
                time.sleep(1)
                self.remaining_seconds -= 1
            else:
                time.sleep(0.1)
        self.root.after(0, self.on_time_up)

    def flash_screen(self):
        """全屏闪烁提醒"""
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
        self.root.configure(bg="#f0f0f0") # 恢复背景色

        # === 核心逻辑分流 ===
        if self.is_focusing:
            # 专注结束 -> 进入评分流程
            self.show_rating_ui()
        else:
            # 休息结束 -> 准备下一轮
            # seems useless
            # self.setup_config_ui()
            # self.show_custom_notification("begin_focus")
            self.is_focusing = True
            self.current_round += 1
            self.setup_config_ui()

    # --- 专注评分界面 ---
    def show_rating_ui(self):
        self.clear_window()
        tk.Label(self.root, text="🍅 专注结束了，去喝点茶，吃点点心吧", font=("微软雅黑", 20, "bold"), fg="#e64a19").pack(pady=30)
        tk.Label(self.root, text="你觉得自己刚刚做得怎么样 (1-5)", font=("微软雅黑", 14)).pack(pady=10)
        tk.Label(self.root, text="1=心不在焉 ... 5=极度专注", font=("微软雅黑", 10), fg="#888").pack(pady=5)
        
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        
        for i in range(1, 6):
            tk.Button(btn_frame, text=str(i), font=("Arial", 14, "bold"), width=4, height=2,
                      bg="#FFCCBC", command=lambda r=i: self.submit_rating(r)).pack(side=tk.LEFT, padx=10)

    def submit_rating(self, rating):
        # 1. 核心：在这里累计你的每一次专注
        self.focus_history.append({
            'duration': self.last_focus_min,
            'rating': rating
        })
        
        # 记录完后进入休息状态
        self.is_focusing = False
        self.harass_count = 0
        self.setup_config_ui()
        pattern = None
        if rating >= 4: # qsl gives encouragement based on rating
            pattern = "high_quality"
        else:
            pattern = "low_quality"
        self.show_custom_notification(pattern)

    def show_custom_notification(self, pattern):
        popup = tk.Toplevel(self.root)
        popup.title("🦊")
        popup.attributes("-topmost", True)
        
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = 320, 160
        x = sw - w - 20
        y = sh - h - 80 
        popup.geometry(f"{w}x{h}+{x}+{y}")
        
        bg_color = "#e8f5e9" if not self.is_focusing else "#fff3e0"
        popup.configure(bg=bg_color)
        msg = self.get_random_line(pattern, 
            ["难得没有偷懒，表现得还不错。", 
            "我看得出来，你是真的在努力。", 
            "允许自己有笨拙的时候。", 
            "你这点小小的失误，没什么大不了的。", 
            "你不是一台只允许盈利的机器。"])
        
        tk.Label(popup, text=msg, wraplength=280, font=("微软雅黑", 12), bg=bg_color, justify="center").pack(expand=True, pady=10)
        tk.Button(popup, text="🦜：好的狐狐", command=popup.destroy, bg="white", relief="groove").pack(pady=10)

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