# BalAtro-smartSL
Python Script about quick save ＆ load of game Balatro.  

# Balatro 存档管理器

一个简单的 Balatro 游戏存档管理工具，支持存档备份、读取和预览功能。

## 功能特点

- 自动截取游戏窗口画面
- 保存/读取游戏存档
- 存档预览功能
- 支持自定义游戏窗口标题和存档路径
- 存档文件统一管理

## 环境要求

- Windows OS
- Python 3.9 +
- Anaconda/Miniconda

## 安装步骤

1. 克隆或下载本项目到本地

2. 使用 Conda 创建环境（推荐）：
一个简单的 Balatro 游戏存档管理工具，支持存档备份、读取和预览功能。

## 功能特点

- 自动截取游戏窗口画面
- 保存/读取游戏存档
- 存档预览功能
- 支持自定义游戏窗口标题和存档路径
- 存档文件统一管理

## 环境要求

- Windows 操作系统
- Python 3.9 或更高版本
- Anaconda/Miniconda

## 安装步骤

1. 克隆或下载本项目到本地

2. 使用 Conda 创建环境（推荐）：.yml

# 激活环境
conda activate saveloader
```

或者使用 pip 安装依赖：

```bash
pip install -r requirements.txt
```

## 使用说明

1. 启动程序：

```bash
python save_loader.py
```
 游戏窗口标题（默认为 "Balatro"）
   - 游戏存档路径（默认为 "%APPDATA%\Balatro\1\save.jkr"）

1. 基本操作：
   - 保存存档：点击"保存存档"按钮，输入存档名称
   - 读取存档：选择存档后点击"读取存档"按钮
   - 删除存档：选择存档后点击"删除存档"按钮
   - 预览存档：在左侧列表选择存档即可在右侧查看预览图
   - 设置支持自定义监视窗口和存档文件路径  

## 文件说明

- `save_loader.py`: 主程序文件
- `config.json`: 配置文件，存储窗口标题和存档路径
- `saves/`: 存档文件夹
- `screenshots/`: 截图文件夹

## 注意事项  

> **⚠️ 使用管理员身份运行 **

1. 确保游戏窗口标题正确设置
2. **确保存档前游戏窗口不是最小化**
3. 读档前要通过设置主菜单退出到开始界面，先不要点开始游戏，否则要重复操作一次
4. 建议定期清理不需要的存档  

