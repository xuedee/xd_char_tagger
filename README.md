# xd_char_tagger

[中文说明](#中文说明) | [English Documentation](#english-documentation)

---

## 中文说明

一个轻量级、零第三方依赖的本地网页打标工作台，专为 **角色 / 人像 LoRA 训练数据集** 设计。支持结构化分槽位拼词、单选/多选切换、Basket 词条回收篮、批量重命名，以及可选的本地 **Ollama（羊驼）** 视觉模型自动预填。

> **💡 核心说明：手动打标点开即用！**  
> 本工具仅依赖 Python 自带标准库，**无需安装 Ollama 或任何第三方 Python 依赖包**即可直接运行手动打标、改词与批量整理功能。仅当你希望使用「✨ AI 填当前 / 🚀 AI 批量填全部」自动识别图片并预填 Tag 时，才需要额外安装 Ollama。

### ✨ 核心功能
- **结构化槽位打标（Slots）**：按维度分框管理人像属性（触发词、主体与体型、机位视角、景别、头部姿态、表情、服装、发型、背景等），支持自由新增、删除、上下调整大框顺序，自动按顺序输出干净的英文 `.txt` 标注文件。
- **单选 / 多选自由切换**：每个分类大框右上角均提供独立的 **「多选」** 开关，默认单选互斥；需要叠加多个特征时（如头部姿态组合）勾选即可多选。
- **Basket 回收篮与历史映射**：暂不使用的词条可拖入框内 Basket 或底部全局 Basket，避免误选；双击词条可直接修改并自动映射兼容历史 `.txt` 中的旧词，右键可删除。
- **数据集批量整理**：
  - **📌 批量固定**：将当前选中的公共词条（如触发词、画风/背景词）一键同步应用到整个文件夹的所有图片。
  - **🧹 一键整理命名**：采用两阶段安全重命名，输入前缀（如 `tjb`）即可将文件夹内所有图片及同名 `.txt` 统一整理为 `tjb1`、`tjb2`……
  - **🗑️ 删当前图**：一键彻底删除废片及其对应的 `.txt` 标注文件。
- **中英双语界面（`🌐 ENG/CN`）**：顶部按钮一键切换中文与英文界面提示，默认中文。
- **可选 AI 自动预填（Ollama）**：对接本地 Ollama 视觉多模态模型，支持单张预填或全文件夹批量预填。

### 🚀 快速开始（手动打标，点开即用）
1. 确保本地已安装 **Python 3.8+**（Windows 与 macOS 官方安装包默认自带 `tkinter`；Linux 如提示缺少 `tkinter`，执行 `sudo apt-get install python3-tk` 即可）。
2. 在终端运行脚本：
   ```bash
   python xd_char_tagger.py
   ```

1. 浏览器会自动打开 http://127.0.0.1:8765。
2. 点击顶部 「📂 选择」 选中你的训练图片文件夹，点击词条即可自动生成并保存同名 .txt 文件（同时会在该目录生成 _tagger_config.json 保存你的槽位与词库配置）。


🤖 【可选】AI Auto Tag 功能配置（安装 Ollama 与下载模型）
如果你希望让本地 AI 帮你自动识别图片并勾选预设 Tag，请按以下步骤配置：
1. 安装 Ollama（羊驼）：
前往官网 https://ollama.com/ 下载对应系统（Windows / macOS / Linux）的安装包并完成安装。
2.下载支持视觉识别的多模态模型：
打开终端（Windows 下打开 CMD 或 PowerShell），运行以下命令拉取默认推荐的视觉模型（需具备图像理解能力的 VL 模型）：
```
ollama pull qwen2.5vl:7b
```

模型选型参考（可根据显卡显存自行替换）：
|模型名称|显存参考|特点说明|
| :---: | :---: | :---: |
|qwen2.5vl:7b（默认）|~6–8 GB|综合识别准确度高，推荐首选|
|qwen2.5vl:3b|~4 GB|速度更快，适合轻薄本或小显存显卡|
|llama3.2-vision:11b|~8–10 GB|英文指令遵循稳定，适合纯英文词库|



3. 启动并开始自动预填：
确保 Ollama 在后台处于运行状态（Windows/macOS 任务栏出现羊驼图标，或cmd终端运行 ollama serve）。
cmd终端python xd_char_tagger 打开 xd_char_tagger 网页，确认顶部输入框的模型名称与你下载的一致（如 qwen2.5vl:7b），点击 「✨ AI 填当前」 或 「🚀 AI 批量填全部」 即可自动匹配tags并保存。

### ✨常用操作与快捷键
- **↑ / ↓ 方向键**：快速切换上一张 / 下一张图片（每次点击词条均自动保存，无需手动点保存）。

- **单击词条**：选中或取消选中；若点击 Basket 内的词条，会自动激活移回上方并选中。

- **双击词条**：编辑修改词条文本（支持 英文 | 中文提示 格式）。

- **右键词条**：从当前槽位或 Basket 中删除该词条。

- **拖拽词条**：可在不同槽位之间、或槽位与 Basket 之间自由拖动归类。




## English Documentation
A lightweight, zero-dependency local web workbench for character / portrait LoRA dataset tagging. It features structured slot-based prompt assembly, per-slot single/multi-select toggles, tag baskets, batch renaming, and optional local Ollama vision model prefill.

> **💡 Plug & Play for Manual Tagging:

> This tool relies strictly on Python's built-in standard library. No Ollama installation or third-party Python packages are required for manual tagging, editing, and dataset organization. You only need Ollama if you want to use the optional AI auto-prefill features.

### ✨ Features
Structured Slot Tagging: Organize portrait attributes into ordered slots (trigger word, subject & build, camera angle, shot type, head pose, expression, outfit, hairstyle, background, etc.) and automatically output clean comma-separated English .txt captions.

Per-Slot Single / Multi-Select: Toggle Multi on the top-right of any slot when traits should be combined (e.g., head poses), or keep it unchecked for mutually exclusive selection.

Tag Baskets & Legacy Mapping: Drag unused tags into per-slot baskets or the global basket to prevent accidental clicks. Double-click any tag to rename it while preserving compatibility with existing .txt captions; right-click to delete.

Batch Dataset Cleanup:

📌 Apply All: Propagate currently selected global tags (such as trigger words or background tags) across all images in the folder.

🧹 Batch Rename: Safely rename all images and matching .txt files in two stages using a custom prefix (e.g., tjb → tjb1, tjb2, ...).

🗑️ Del Image: Permanently remove unwanted images along with their paired .txt files.

Bilingual UI (🌐 ENG/CN): Toggle all interface buttons, status messages, and dialogs between Chinese and English with one click.

Optional Ollama Vision Prefill: Connect to a local Ollama multimodal model for single-image or full-dataset batch pre-tagging.

### 🚀 Quick Start (Manual Tagging — Out of the Box)
1. Ensure Python 3.8+ is installed (Windows and macOS official installers include tkinter by default; on Debian/Ubuntu Linux, run sudo apt-get install python3-tk if missing).

2. Run the script in your terminal:
```
python xd_char_tagger.py
```

3. Your browser will open http://127.0.0.1:8765 automatically.

4. Click 📂 Browse to select your dataset folder. Click tags to build .txt captions (auto-saved on every change). Slot layouts and baskets are saved locally in _tagger_config.json inside the dataset folder.


🤖 [Optional] AI Auto-Prefill Setup (Installing Ollama & Vision Models)
If you want a local vision model to inspect your images and pre-select matching preset tags:

Install Ollama:

Download and install Ollama for Windows, macOS, or Linux from https://ollama.com/.

Pull a Vision-Language Model:

Open your terminal (Command Prompt / PowerShell on Windows) and download the default vision model:
```
ollama pull qwen2.5vl:7b
```

Recommended Vision Models by VRAM:
|Model Name|Approx. VRAM|Notes|
| :---: | :---: | :---: |
|qwen2.5vl:7b (Default)	|~6–8 GB|	Best overall accuracy for portrait attributes|
|qwen2.5vl:3b	|~4 GB|	Faster inference for lower-VRAM GPUs|
|llama3.2-vision:11b	|~8–10 GB|	Strong English prompt adherence|


3. Run AI Prefill:

Make sure Ollama is running in the background (check the system tray icon or run ollama serve).

Verify the model name in the top toolbar matches your downloaded model (e.g., qwen2.5vl:7b), then click ✨ AI Current or 🚀 AI All.

## ⌨️ Controls & Shortcuts
- **↑ / ↓ Arrow Keys**: Switch to the previous or next image (all changes are auto-saved).

- **Left-Click Tag**: Select/deselect an active tag, or restore and select a tag from a Basket.

- **Double-Click Tag**: Edit tag text (English | Chinese Note format supported).

- **Right-Click Tag**: Delete the tag from its slot or basket.

- **Drag & Drop**: Reorganize tags across slots or move them into/out of Baskets.

📄 License
MIT License — free to use, modify, and distribute.
