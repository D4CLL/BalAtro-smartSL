# BalAtro-smartSL
Python Script about quick save ＆ load of game balatro.  

# Balatro 存档管理器

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
- Anaconda/Miniconda (推荐)

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
- Anaconda/Miniconda (推荐)

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
   - 游戏存档路径（默认为 "%APPDATA%\\Balatro\\1\\save.jdr"）

3. 基本操作：
   - 保存存档：点击"保存存档"按钮，输入存档名称
   - 读取存档：选择存档后点击"读取存档"按钮
   - 删除存档：选择存档后点击"删除存档"按钮
   - 预览存档：在左侧列表选择存档即可在右侧查看预览图

## 文件说明

- `save_loader.py`: 主程序文件
- `config.json`: 配置文件，存储窗口标题和存档路径
- `saves/`: 存档文件夹
- `screenshots/`: 截图文件夹

## 注意事项

1. 确保游戏窗口标题正确设置
2. 存档前通过主菜单退出设置，不要点入开始游戏界面，否则要重复操作一次
3. 建议定期清理不需要的存档  

