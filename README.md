# FreeMusic

一个功能丰富的音乐处理工具集合，提供音乐播放、管理、转换等功能。

## 功能特性

- 🎵 **音乐播放** - 支持多种音频格式的播放
- 📁 **音乐管理** - 音乐文件的组织和管理
- ⚡ **高效处理** - 快速的音频处理性能

## 技术栈

- **Python** - 主要开发语言
- **Pyqt5** - GUI 界面框架
- **Requests** - Python 爬虫
- **Pillow** - 图像处理（图标转换等）

## 安装说明

### 依赖安装
bash
pip install -r requirements.txt

### 项目依赖

- Python 3.x
- Pyqt5 (通常随 Python 一起安装)
- Pillow - 用于图像处理

## 使用方法

### 开发环境运行
bash python main.py

### 打包为可执行文件
bash
pyinstaller --onefile --windowed --icon=icons/music.png -n "Free Music" --add-data "icons:icons" free_music.py
## 打包命令详细说明

### 各参数含义

- `--onefile` - 将所有依赖打包成单个exe文件
- `--windowed` - 创建窗口应用程序（无控制台窗口）
- `--icon=icons/music.png` - 设置应用程序图标
- `-n "Free Music"` - 指定生成的可执行文件名称
- `--add-data "icons:icons"` - 将icons文件夹复制到可执行文件中
- `free_music.py` - 要打包的主程序文件

### 参数扩展说明

- **`--onefile`**: 生成单一exe文件，便于分发，但启动速度稍慢
- **`--windowed`**: 隐藏控制台窗口，适用于GUI应用
- **`--icon`**: 指定应用图标，支持 `.ico`、`.exe` 和 `.png` 格式
- **`-n`**: 自定义输出文件名，支持空格和特殊字符
- **`--add-data`**: 复制资源文件到可执行文件中，格式为 `"源路径:目标路径"`

## 项目结构

├── free_music.py           # 主程序入口
├── icons/                  # 图标资源文件夹
│   ├── music.png           # 音乐图标PNG格式
│   └── music.ico           # 音乐图标ICO格式
├── dist/                   # 打包输出目录
├── build/                  # 临时构建目录
└── README.md               # 项目说明文档


## 配置说明

### 图标文件

项目中包含两种格式的图标文件：
- [music.png](file://D:\Code\tools\music\icons\music.png) - 原始PNG格式图标
- `music.ico` - Windows兼容的ICO格式图标

### 资源文件管理

- 使用 `--add-data` 参数确保资源文件被打包进exe
- 路径格式：`--add-data "src_path:dest_path"`
- Windows下使用分号(`;`)分隔，Linux/Mac使用冒号(`:`)分隔

## 常见问题

### 图标格式问题

如果遇到图标格式错误，请确保：
1. 安装了 Pillow 库：`pip install Pillow`
2. 使用 [.ico](file://D:\Code\tools\music\build\freemain\generated-3ef77f71b8e17f4f299cdadbe7df51c638e2cd25b9bb2de8bce3cf2921bf38c2.ico) 格式图标文件更兼容
3. 或者将 PNG 文件转换为 ICO 格式

### 资源文件访问

打包后的资源文件访问路径：


### 打包问题

如果 PyInstaller 打包失败：
1. 确保所有依赖已安装
2. 检查图标文件路径是否正确
3. 使用正确的 PyInstaller 参数
4. 确认文件权限设置

## 开发说明

### 代码规范

- 遵循 Python PEP8 编码规范
- 使用有意义的变量和函数命名
- 添加适当的代码注释

### 贡献指南

1. Fork 本项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 许可证

[在此处添加许可证信息]

## 作者

[在此处添加作者信息]
