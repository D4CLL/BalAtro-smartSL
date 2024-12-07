import sys
import json
import os
from datetime import datetime
from PIL import ImageGrab, Image
import win32gui
import win32ui
import win32con
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import time

def window_screenshot(hwnd):
    """获取指定窗口的截图"""
    try:
        # 获取窗口完整区域（包括标题栏和边框）
        window_rect = win32gui.GetWindowRect(hwnd)
        # 获取客户区域
        client_rect = win32gui.GetClientRect(hwnd)
        # 获取客户区域在屏幕上的位置
        client_left, client_top = win32gui.ClientToScreen(hwnd, (0, 0))
        
        # 计算边框大小
        border_left = client_left - window_rect[0]
        border_top = client_top - window_rect[1]
        border_right = window_rect[2] - (client_left + client_rect[2])
        border_bottom = window_rect[3] - (client_top + client_rect[3])
        
        # 获取完整的窗口区域，包括边框
        left = window_rect[0]
        top = window_rect[1]
        right = window_rect[2] + border_right  # 添加右边框
        bottom = window_rect[3] + border_bottom  # 添加底部边框
        
        # 将窗口移到前台
        win32gui.SetForegroundWindow(hwnd)
        
        # 稍微延迟以确保窗口显示
        time.sleep(0.2)
        
        # 使用PIL直接截图整个窗口区域
        screenshot = ImageGrab.grab((left, top, right, bottom))
        
        return screenshot

    except Exception as e:
        raise Exception(f"截图失败: {str(e)}")

def list_windows():
    """列出所有可见窗口的标题"""
    result = []
    def enum_windows_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                result.append(title)
    win32gui.EnumWindows(enum_windows_callback, None)
    return sorted(result)

class SaveManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("存档管理器")
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 设置窗口大小
        window_width = 1000  # 固定宽度
        window_height = 600  # 固定高度
        
        # 计算窗口位置，使其居中
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # 设置窗口大小和位置
        self.root.geometry(f"{window_width}x{window_height}+{int(x)}+{int(y)}")
        
        # 禁止调整窗口大小
        self.root.resizable(False, False)
        
        # 固定存档记录在程序所在目录下
        self.saves_dir = os.path.join(os.path.dirname(__file__), "saves")
        self.screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
        
        # 默认游戏存档路径
        self.game_save_path = os.path.expandvars(r"%APPDATA%\Balatro\save.jdr")
        
        # 加载配置
        self.load_config()
        
        # 创建目录
        os.makedirs(self.saves_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # 创建主界面
        self.create_widgets()
        
        # 加载存档列表
        self.load_save_list()
        
    def create_widgets(self):
        # 左侧面板 - 固定宽度
        left_frame = ttk.Frame(self.root, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_frame.pack_propagate(False)  # 防止frame被子组件压缩
        
        # 存档列表
        self.save_listbox = tk.Listbox(left_frame, width=25)
        self.save_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.save_listbox.bind('<<ListboxSelect>>', self.on_select_save)
        
        # 按钮
        ttk.Button(left_frame, text="保存存档", command=self.create_save).pack(fill=tk.X, pady=2)
        ttk.Button(left_frame, text="读取存档", command=self.load_save).pack(fill=tk.X, pady=2)
        ttk.Button(left_frame, text="删除存档", command=self.delete_save).pack(fill=tk.X, pady=2)
        ttk.Button(left_frame, text="设置", command=self.show_settings).pack(fill=tk.X, pady=2)
        
        # 右侧预览 - 占据剩余空间
        self.preview_frame = ttk.Frame(self.root)
        self.preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建一个内部frame用于居中显示图片
        self.preview_inner_frame = ttk.Frame(self.preview_frame)
        self.preview_inner_frame.pack(expand=True)
        
        self.preview_label = ttk.Label(self.preview_inner_frame)
        self.preview_label.pack()
    
    def load_save_list(self):
        """加载存档列表"""
        self.save_listbox.delete(0, tk.END)
        saves = [f for f in os.listdir(self.saves_dir) if f.endswith('.json')]
        for save in saves:
            self.save_listbox.insert(tk.END, save.replace('.json', ''))
    
    def create_save(self):
        """创建新存档"""
        # 创建存档名称输入窗口
        dialog = tk.Toplevel(self.root)
        dialog.title("保存存档")
        dialog.geometry("300x100")
        dialog.transient(self.root)
        
        # 设置弹窗在主窗口中间
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # 阻止调整大小
        dialog.resizable(False, False)
        
        ttk.Label(dialog, text="存档名称:").pack(pady=5)
        name_var = tk.StringVar(value=datetime.now().strftime("%Y%m%d_%H%M%S"))
        entry = ttk.Entry(dialog, textvariable=name_var)
        entry.pack(pady=5)
        
        def save():
            save_name = name_var.get()
            if save_name:
                # 检查游戏存档是否存在
                if not os.path.exists(self.game_save_path):
                    messagebox.showerror("错误", "找不到游戏存档文件！")
                    return
                
                # 获取目标窗口截图
                hwnd = win32gui.FindWindow(None, self.window_title)
                if hwnd:
                    try:
                        # 使用新的截图方法
                        screenshot = window_screenshot(hwnd)
                        
                        screenshot_path = os.path.join(self.screenshots_dir, f"{save_name}.png")
                        save_path = os.path.join(self.saves_dir, f"{save_name}.json")
                        game_save_backup = os.path.join(self.saves_dir, f"{save_name}.jdr")
                        
                        # 检查是否存在
                        if os.path.exists(save_path):
                            if not messagebox.askyesno("确认", "存档已存在，是否覆盖？"):
                                return
                        
                        # 复制游戏存档文件
                        import shutil
                        shutil.copy2(self.game_save_path, game_save_backup)
                        
                        # 保存截图和存档信息
                        screenshot.save(screenshot_path)
                        save_data = {
                            "name": save_name,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "screenshot": screenshot_path,
                            "game_save": game_save_backup
                        }
                        
                        with open(save_path, 'w', encoding='utf-8') as f:
                            json.dump(save_data, f, indent=4)
                        
                        self.load_save_list()
                        dialog.destroy()
                    except Exception as e:
                        messagebox.showerror("错误", f"截图失败: {str(e)}")
                        return
                else:
                    messagebox.showerror("错误", f"找不到窗口: {self.window_title}")
        
        ttk.Button(dialog, text="保存", command=save).pack(pady=5)
    
    def load_save(self):
        """读取存档"""
        selection = self.save_listbox.curselection()
        if selection:
            save_name = self.save_listbox.get(selection[0])
            save_path = os.path.join(self.saves_dir, f"{save_name}.json")
            
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
                game_save = save_data.get('game_save')
                
                if os.path.exists(game_save):
                    # 备份当前存档
                    current_backup = os.path.join(self.saves_dir, "current_backup.txt")
                    import shutil
                    shutil.copy2(self.game_save_path, current_backup)
                    
                    try:
                        # 复制存档文件到游戏目录
                        shutil.copy2(game_save, self.game_save_path)
                        messagebox.showinfo("成功", "存档已恢复！")
                    except Exception as e:
                        # 如果失败，尝试恢复备份
                        shutil.copy2(current_backup, self.game_save_path)
                        messagebox.showerror("错误", f"恢复存档失败: {str(e)}")
                else:
                    messagebox.showerror("错误", "找不到存档文件！")
    
    def delete_save(self):
        """删除存档"""
        selection = self.save_listbox.curselection()
        if selection:
            save_name = self.save_listbox.get(selection[0])
            if messagebox.askyesno("确认", f"确定要删除存档 {save_name} 吗？"):
                # 所有相关文件路径
                save_path = os.path.join(self.saves_dir, f"{save_name}.json")  # 存档信息
                screenshot_path = os.path.join(self.screenshots_dir, f"{save_name}.png")  # 截图
                game_save_backup = os.path.join(self.saves_dir, f"{save_name}.jdr")  # 游戏存档备份
                
                # 删除所有相关文件
                if os.path.exists(save_path):
                    os.remove(save_path)
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
                if os.path.exists(game_save_backup):
                    os.remove(game_save_backup)
                
                # 刷新列表和预览
                self.load_save_list()
                self.preview_label.configure(image='')
    
    def on_select_save(self, event):
        """选择存档时显示预览"""
        selection = self.save_listbox.curselection()
        if selection:
            save_name = self.save_listbox.get(selection[0])
            screenshot_path = os.path.join(self.screenshots_dir, f"{save_name}.png")
            
            if os.path.exists(screenshot_path):
                # 加载原始图片
                img = Image.open(screenshot_path)
                img_width, img_height = img.size
                
                # 取预览区域大小
                self.preview_frame.update()
                frame_width = self.preview_frame.winfo_width() - 20  # 减去padding
                frame_height = self.preview_frame.winfo_height() - 20  # 减去padding
                
                # 计算缩放比例，确保图片完全显示
                scale = min(frame_width/img_width, frame_height/img_height)
                
                # 计算新尺寸
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                # 缩放图片
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 转换为PhotoImage
                photo = tk.PhotoImage(file=screenshot_path)
                
                # 根据新尺寸计算缩放因子
                scale_factor = max(1, max(img_width // new_width, img_height // new_height))
                if scale_factor > 1:
                    photo = photo.subsample(scale_factor)
                
                # 更新预览
                self.preview_label.configure(image=photo)
                self.preview_label.image = photo  # 保持引用
    
    def load_config(self):
        """加载配置"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.window_title = config.get('window_title', "目标窗口标题")
                self.game_save_path = config.get('game_save_path', 
                    os.path.expandvars(r"%APPDATA%\Balatro\save.jdr"))
        except FileNotFoundError:
            self.window_title = "目标窗口标题"
            self.game_save_path = os.path.expandvars(r"%APPDATA%\Balatro\save.jdr")
            self.save_config()
    
    def save_config(self):
        """保存配置"""
        config = {
            'window_title': self.window_title,
            'game_save_path': self.game_save_path
        }
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    
    def show_settings(self):
        """显示设置窗口"""
        dialog = tk.Toplevel(self.root)
        dialog.title("设置")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        
        # 创建表单
        form_frame = ttk.Frame(dialog)
        form_frame.pack(padx=10, pady=5, fill=tk.X)
        
        # 窗口标题设置
        ttk.Label(form_frame, text="目标窗口标题:").pack(fill=tk.X, pady=2)
        title_var = tk.StringVar(value=self.window_title)
        title_entry = ttk.Entry(form_frame, textvariable=title_var)
        title_entry.pack(fill=tk.X, pady=2)
        
        # 存档路径设置
        ttk.Label(form_frame, text="游戏存档路径:").pack(fill=tk.X, pady=2)
        path_var = tk.StringVar(value=self.game_save_path)
        path_entry = ttk.Entry(form_frame, textvariable=path_var)
        path_entry.pack(fill=tk.X, pady=2)
        
        # 添加窗口列表按钮
        def show_window_list():
            windows = list_windows()
            dialog = tk.Toplevel(self.root)
            dialog.title("选择窗口")
            dialog.geometry("300x400")
            
            listbox = tk.Listbox(dialog)
            listbox.pack(fill=tk.BOTH, expand=True)
            
            for window in windows:
                listbox.insert(tk.END, window)
            
            def select_window():
                selection = listbox.curselection()
                if selection:
                    title_var.set(listbox.get(selection[0]))
                    dialog.destroy()
            
            ttk.Button(dialog, text="选择", command=select_window).pack(pady=5)
        
        ttk.Button(form_frame, text="列出窗口", command=show_window_list).pack(fill=tk.X, pady=2)
        
        def save_settings():
            self.window_title = title_var.get()
            new_save_path = path_var.get()
            
            # 验证存档文件是否存在
            if not os.path.exists(new_save_path):
                if not messagebox.askyesno("警告", 
                    "指定的存档文件不存在，是否继续保存设置？"):
                    return
            
            self.game_save_path = new_save_path
            self.save_config()
            dialog.destroy()
        
        # 按钮区域
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="保存", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    app = SaveManager()
    app.run() 