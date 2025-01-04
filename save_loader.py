import sys
import json
import os
from datetime import datetime
from PIL import Image, ImageTk
from ctypes import windll, byref, create_unicode_buffer, create_string_buffer, Structure, sizeof, WINFUNCTYPE
from ctypes.wintypes import (BOOL, HWND, RECT, DWORD, LPARAM, WCHAR, UINT, POINT, WORD, LONG, ATOM)
import tkinter as tk
from tkinter import ttk, messagebox

HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_SHOWWINDOW = 0x0040
DIB_RGB_COLORS = 0
BI_RGB = 0

class BITMAPINFOHEADER(Structure):
    _fields_ = [
        ("biSize", DWORD),
        ("biWidth", LONG),
        ("biHeight", LONG),
        ("biPlanes", WORD),
        ("biBitCount", WORD),
        ("biCompression", DWORD),
        ("biSizeImage", DWORD),
        ("biXPelsPerMeter", LONG),
        ("biYPelsPerMeter", LONG),
        ("biClrUsed", DWORD),
        ("biClrImportant", DWORD)
    ]

class BITMAPINFO(Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", DWORD * 3)
    ]

class WINDOWPLACEMENT(Structure):
    _fields_ = [
        ("length", UINT),
        ("flags", UINT),
        ("showCmd", UINT),
        ("ptMinPosition", POINT),
        ("ptMaxPosition", POINT),
        ("rcNormalPosition", RECT)
    ]

class WINDOWINFO(Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("rcWindow", RECT),
        ("rcClient", RECT),
        ("dwStyle", DWORD),
        ("dwExStyle", DWORD),
        ("dwWindowStatus", DWORD),
        ("cxWindowBorders", WORD),
        ("cyWindowBorders", WORD),
        ("atomWindowType", ATOM),
        ("wCreatorVersion", WORD)
    ]

def window_screenshot(hwnd):
    """使用 ctypes 实现的窗口截图功能"""
    try:
        # 获取窗口位置和大小
        rect = RECT()
        windll.user32.GetWindowRect(hwnd, byref(rect))
        
        # 计算尺寸增加
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        width_increase = int(width * 0.25)
        height_increase = int(height * 0.25)
        
        # 保存当前窗口位置
        placement = WINDOWPLACEMENT()
        placement.length = sizeof(WINDOWPLACEMENT)
        windll.user32.GetWindowPlacement(hwnd, byref(placement))
        
        # 设置窗口位置
        windll.user32.SetWindowPos(
            hwnd, 
            HWND_TOPMOST,
            rect.left, rect.top,
            width + width_increase,
            height + height_increase,
            SWP_SHOWWINDOW
        )
        
        #time.sleep(0.2)
        
        # 创建DC和位图
        hwnd_dc = windll.user32.GetWindowDC(hwnd)
        mf_dc = windll.gdi32.CreateCompatibleDC(hwnd_dc)
        bitmap = windll.gdi32.CreateCompatibleBitmap(
            hwnd_dc,
            width + width_increase,
            height + height_increase
        )
        windll.gdi32.SelectObject(mf_dc, bitmap)
        
        # 截图
        result = windll.user32.PrintWindow(hwnd, mf_dc, 3)
        if result == 0:
            raise Exception("PrintWindow failed")
            
        # 转换为PIL图像
        bmp_info = BITMAPINFO()
        bmp_info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER)
        bmp_info.bmiHeader.biWidth = width + width_increase
        bmp_info.bmiHeader.biHeight = -(height + height_increase)
        bmp_info.bmiHeader.biPlanes = 1
        bmp_info.bmiHeader.biBitCount = 32
        bmp_info.bmiHeader.biCompression = BI_RGB
        
        buffer_size = (width + width_increase) * (height + height_increase) * 4
        buffer = create_string_buffer(buffer_size)
        
        windll.gdi32.GetDIBits(
            mf_dc, bitmap, 0,
            height + height_increase,
            buffer,
            byref(bmp_info),
            DIB_RGB_COLORS
        )
        
        # 创建PIL图像
        img = Image.frombuffer(
            'RGBA',
            (width + width_increase, height + height_increase),
            buffer,
            'raw',
            'BGRA',
            0,
            1
        )
        
        # 清理资源
        windll.gdi32.DeleteObject(bitmap)
        windll.gdi32.DeleteDC(mf_dc)
        windll.user32.ReleaseDC(hwnd, hwnd_dc)
        
        # 恢复窗口位置
        windll.user32.SetWindowPos(
            hwnd,
            HWND_NOTOPMOST,
            rect.left, rect.top,
            width, height,
            SWP_SHOWWINDOW
        )
        windll.user32.SetWindowPlacement(hwnd, byref(placement))
        
        return img
        
    except Exception as e:
        # 确保恢复窗口状态
        try:
            windll.user32.SetWindowPos(
                hwnd,
                HWND_NOTOPMOST,
                rect.left, rect.top,
                width, height,
                SWP_SHOWWINDOW
            )
            windll.user32.SetWindowPlacement(hwnd, byref(placement))
        except:
            pass
        raise Exception(f"截图失败: {str(e)}")

def list_windows():
    """使用 ctypes 实现的窗口列表获取功能"""
    result = []
    
    def enum_windows_proc(hwnd, lParam):
        if windll.user32.IsWindowVisible(hwnd):
            length = windll.user32.GetWindowTextLengthW(hwnd)
            if length:
                buff = create_unicode_buffer(length + 1)
                windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                result.append(buff.value)
        return True
    
    WNDENUMPROC = WINFUNCTYPE(BOOL, HWND, LPARAM)
    enum_proc = WNDENUMPROC(enum_windows_proc)
    windll.user32.EnumWindows(enum_proc, 0)
    
    return sorted(result)

class SaveManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("存档管理器")
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 设置窗口大小
        window_width = 1000
        window_height = 600
        
        # 计算窗口位置，使其居中
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # 设置窗口大小和位置
        self.root.geometry(f"{window_width}x{window_height}+{int(x)}+{int(y)}")
        self.root.resizable(False, False)
        
        # 获取当前目录
        if getattr(sys, 'frozen', False):
            # 如果是通过 PyInstaller 打包后的 .exe 文件
            current_directory = os.path.dirname(sys.executable)
        else:
            # 如果是源代码环境下
            current_directory = os.path.dirname(__file__)
        # 固定存档记录在程序所在目录下
        self.saves_dir = os.path.join(current_directory, "saves")
        self.screenshots_dir = os.path.join(current_directory, "screenshots")
        
        # 默认游戏存档路径
        self.game_save_path = os.path.expandvars(r"%APPDATA%\Balatro\1\save.jkr")
        
        # 自动存档相关属性
        self.auto_save_enabled = False
        self.auto_save_interval = 5  # 默认5分钟
        self.auto_save_job = None
        
        # 加载配置
        self.load_config()
        
        # 创建目录
        os.makedirs(self.saves_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # 创建主界面
        self.create_widgets()
        
        # 加载存档列表
        self.load_save_list()
        
        # 如果启用了自动存档，启动定时任务
        if self.auto_save_enabled:
            self.start_auto_save()
        
        # 添加一个变量来记录上一次的选择集
        self.previous_selections = ()

    def create_widgets(self):
        # 左侧面板 - 固定宽度
        left_frame = ttk.Frame(self.root, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_frame.pack_propagate(False)  # 防止frame被子组件压缩
        
        # 存档列表 - 保留多选功能，但移除右键菜单
        self.save_listbox = tk.Listbox(left_frame, width=25, selectmode=tk.EXTENDED)
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
    
    def create_save(self, auto = False):
        """创建新存档"""
        # 如果是自动保存模式
        if auto:
            save_name = datetime.now().strftime("auto_%Y%m%d_%H%M%S")
            # 检查游戏存档是否存在
            if not os.path.exists(self.game_save_path):
                messagebox.showerror("错误", "找不到游戏存档文件！")
                return
            
            # 获取目标窗口截图
            hwnd = windll.user32.FindWindowW(None, self.window_title)
            if hwnd:
                try:
                    # 使用新的截图方法
                    screenshot = window_screenshot(hwnd)
                    
                    screenshot_path = os.path.join(self.screenshots_dir, f"{save_name}.png")
                    save_path = os.path.join(self.saves_dir, f"{save_name}.json")
                    game_save_backup = os.path.join(self.saves_dir, f"{save_name}.jkr")
                    
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
                except Exception as e:
                    messagebox.showerror("错误", f"截图失败: {str(e)}")
                    return
            else:
                messagebox.showerror("错误", f"找不到窗口: {self.window_title}")
            return  # 自动保存完成，退出函数

        # 创建存档名称输入窗口
        dialog_width = 300
        dialog_height = 100
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog_width) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog_height) // 2
        
        # 显示存档名称输入窗口  
        dialog = tk.Toplevel(self.root)
        dialog.title("保存存档")
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        dialog.transient(self.root)
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
                hwnd = windll.user32.FindWindowW(None, self.window_title)
                if hwnd:
                    try:
                        # 使用新的截图方法
                        screenshot = window_screenshot(hwnd)
                        
                        screenshot_path = os.path.join(self.screenshots_dir, f"{save_name}.png")
                        save_path = os.path.join(self.saves_dir, f"{save_name}.json")
                        game_save_backup = os.path.join(self.saves_dir, f"{save_name}.jkr")
                        
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
        selections = self.save_listbox.curselection()
        if not selections:
            return
        
        # 获取所有选中的存档名称
        save_names = [self.save_listbox.get(idx) for idx in selections]
        
        # 确认删除
        if len(save_names) == 1:
            confirm_msg = f"确定要删除存档 {save_names[0]} 吗？"
        else:
            confirm_msg = f"确定要删除选中的 {len(save_names)} 个存档吗？"
        
        if messagebox.askyesno("确认", confirm_msg):
            for save_name in save_names:
                # 所有相关文件路径
                save_path = os.path.join(self.saves_dir, f"{save_name}.json")  # 存档信息
                screenshot_path = os.path.join(self.screenshots_dir, f"{save_name}.png")  # 截图
                game_save_backup = os.path.join(self.saves_dir, f"{save_name}.jkr")  # 游戏存档备份
                
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
        selections = self.save_listbox.curselection()
        if not selections:
            # 清除预览
            self.preview_label.configure(image='')
            self.previous_selections = ()
            return
        
        # 确定最新选中的项
        current = None
        
        # 如果之前有选择，比较新旧选择集找出新增的选择
        if self.previous_selections:
            new_selections = set(selections) - set(self.previous_selections)
            if new_selections:
                current = max(new_selections)  # 获取新增选择中的最后一个
        
        # 如果没有找到新增的选择，使用当前选择集中的最后一个
        if current is None:
            current = selections[-1]
        
        # 更新上一次的选择记录
        self.previous_selections = selections
        
        # 显示预览
        save_name = self.save_listbox.get(current)
        screenshot_path = os.path.join(self.screenshots_dir, f"{save_name}.png")
        
        if os.path.exists(screenshot_path):
            # 加载原始图片
            img = Image.open(screenshot_path)
            img_width, img_height = img.size
            
            # 取预览区域大小
            self.preview_frame.update()
            frame_width = self.preview_frame.winfo_width() - 20  # 减去padding
            frame_height = self.preview_frame.winfo_height() - 20  # 减去padding
            
            # 优先适应宽度
            scale = frame_width / img_width
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # 如果高度超出，则改用高度缩放
            if new_height > frame_height:
                scale = frame_height / img_height
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
            
            # 缩放图片
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为PhotoImage以适配tkinter显示
            photo = ImageTk.PhotoImage(img_resized)
            
            # 更新预览
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo  # 保持引用

    def load_config(self):
        """加载配置"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.window_title = config.get('window_title', "Balatro")
                self.game_save_path = config.get('game_save_path', 
                    os.path.expandvars(r"%APPDATA%\Balatro\1\save.jkr"))
                self.auto_save_enabled = config.get('auto_save_enabled', False)
                self.auto_save_interval = config.get('auto_save_interval', 5)
        except FileNotFoundError:
            self.window_title = "Balatro"
            self.game_save_path = os.path.expandvars(r"%APPDATA%\Balatro\1\save.jkr")
            self.auto_save_enabled = False
            self.auto_save_interval = 5
            self.save_config()
    
    def save_config(self):
        """保存配置"""
        config = {
            'window_title': self.window_title,
            'game_save_path': self.game_save_path,
            'auto_save_enabled': self.auto_save_enabled,
            'auto_save_interval': self.auto_save_interval
        }
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    
    def start_auto_save(self):
        """开始自动存档"""
        if self.auto_save_job:
            self.root.after_cancel(self.auto_save_job)
        
        def auto_save():
            if self.auto_save_enabled:
                self.create_save(True)
                # 设置下一次自动存档
                self.auto_save_job = self.root.after(self.auto_save_interval * 60 * 1000, auto_save)
        
        # 设置第一次自动存档的定时
        self.auto_save_job = self.root.after(self.auto_save_interval * 60 * 1000, auto_save)

    def stop_auto_save(self):
        """停止自动存档"""
        if self.auto_save_job:
            self.root.after_cancel(self.auto_save_job)
            self.auto_save_job = None

    def show_settings(self):
        """显示设置窗口"""
        dialog_width = 400
        dialog_height = 300
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog_width) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog_height) // 2
        
        dialog = tk.Toplevel(self.root)
        dialog.withdraw()  # 先隐藏窗口
        dialog.title("设置")
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.deiconify()  # 显示窗口
        
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
        
        # 自动存档设置
        ttk.Label(form_frame, text="自动存档设置:").pack(fill=tk.X, pady=2)
        enabled_var = tk.BooleanVar(value=self.auto_save_enabled)
        ttk.Checkbutton(form_frame, text="启用自动存档", variable=enabled_var).pack(fill=tk.X, pady=2)
        
        interval_frame = ttk.Frame(form_frame)
        interval_frame.pack(fill=tk.X, pady=2)
        ttk.Label(interval_frame, text="间隔时间(分钟):").pack(side=tk.LEFT)
        interval_var = tk.StringVar(value=str(self.auto_save_interval))
        interval_entry = ttk.Entry(interval_frame, textvariable=interval_var, width=10)
        interval_entry.pack(side=tk.LEFT, padx=5)
    
        # 添加窗口列表按钮
        def show_window_list():
            windows = list_windows()
            list_width = 300
            list_height = 400
            x = self.root.winfo_x() + (self.root.winfo_width() - list_width) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - list_height) // 2
            
            list_dialog = tk.Toplevel(dialog)
            list_dialog.withdraw()  # 先隐藏窗口
            list_dialog.title("选择窗口")
            list_dialog.geometry(f"{list_width}x{list_height}+{x}+{y}")
            list_dialog.transient(dialog)
            list_dialog.resizable(False, False)
            list_dialog.deiconify()  # 显示窗口
            
            listbox = tk.Listbox(list_dialog)
            listbox.pack(fill=tk.BOTH, expand=True)
            
            for window in windows:
                listbox.insert(tk.END, window)
            
            def select_window():
                selection = listbox.curselection()
                if selection:
                    title_var.set(listbox.get(selection[0]))
                    list_dialog.destroy()
            
            ttk.Button(list_dialog, text="选择", command=select_window).pack(pady=5)
        
        ttk.Button(form_frame, text="列出窗口", command=show_window_list).pack(fill=tk.X, pady=2)
        
        def save_settings():
            self.window_title = title_var.get()
            new_save_path = path_var.get()
            
            # 验证存档文件是否存在
            if not os.path.exists(new_save_path):
                if not messagebox.askyesno("警告", 
                    "指定的存档文件不存在，是否继续保存设置？"):
                    return
            
            # 保存自动存档设置
            try:
                interval = max(1, int(interval_var.get()))
                self.auto_save_interval = interval
                new_enabled = enabled_var.get()
                
                # 更新自动存档状态
                if new_enabled != self.auto_save_enabled:
                    self.auto_save_enabled = new_enabled
                    if new_enabled:
                        self.start_auto_save()
                    else:
                        self.stop_auto_save()
            except ValueError:
                messagebox.showerror("错误", "请输入有效的时间间隔！")
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