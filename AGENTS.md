# AGENTS.md

本文件为项目级智能体指令，适用于各类 AI 编码助手（Claude Code、Cursor、Copilot、AtomCode 等）。请遵守以下约定。

## 项目概述

批量将 LRC 歌词嵌入 FLAC 音乐文件的命令行工具：

- **FLAC 输入**：直接复制到输出目录并写入 `LYRICS` 歌词标签，保留封面与原元数据
- **MP3 输入**：先用 ffmpeg 转为 FLAC（保留封面与 ID3 标签），再写入 `LYRICS` 歌词
- 按文件名（不含扩展名）自动匹配 `.flac`/`.mp3` 与 `.lrc`；孤立的文件提示并跳过
- 输出目录已有同名文件时自动跳过，不覆盖
- 同名 `flac` + `mp3` 并存时优先处理 `flac`

## 常用命令

| 用途 | 命令 |
|---|---|
| 安装依赖 | `uv sync` |
| 运行工具 | `uv run src/embed_lrc.py -i <输入目录> -o <输出目录>` |
| 语法检查 | `uv run python -m py_compile src/embed_lrc.py` |
| 验证歌词嵌入 | `uv run python -c "from mutagen.flac import FLAC; print(FLAC('文件.flac').get('LYRICS', ['未找到'])[0][:200])"` |

## 技术栈与依赖管理（强制）

- Python >= 3.10，使用 **uv** 进行项目级依赖管理
- 本项目所有依赖、工具一律**项目级安装**（写入 `pyproject.toml`），**禁止全局安装**（如 pip 全局装、winget/choco 装工具等）
- 关键依赖：
  - `mutagen`：读写 FLAC 元数据
  - `imageio-ffmpeg`：自带 ffmpeg 二进制（PyPI 分发），用于 MP3→FLAC 转换

## Git 提交流程（强制）

- **每次执行 `git commit` 之前，必须先向用户展示本次提交的完整内容**（`git status` + `git diff --cached`）以及拟定的提交信息
- 必须等待用户**明确同意**后，才能执行提交
- 用户不同意时不得提交，按用户反馈修改后重新展示审核
- 提交信息使用**中文**，格式美观（分段式）
- 该规则适用于本项目所有 commit，包括首次提交

## 代码风格

- 匹配现有文件风格，保留中文注释与命名习惯
- 不改动与任务无关的代码
