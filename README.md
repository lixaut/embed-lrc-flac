# embed-lrc-flac

将 LRC 歌词批量嵌入到同名的 FLAC 音乐文件中。支持两种输入：

- **FLAC**：直接复制并写入 `LYRICS` 标签（保留封面、原元数据）
- **MP3**：先用 ffmpeg 转为 FLAC（保留封面、ID3 标签），再写入 `LYRICS` 歌词

## 环境要求

- [uv](https://docs.astral.sh/uv/)（项目级 Python 环境管理）

所有依赖均通过 uv 项目级管理，无需全局安装。

## 安装

```bash
uv sync
```

## 使用

```bash
uv run src/embed_lrc.py -i ./音乐 -o ./输出
```

| 参数 | 说明 |
|---|---|
| `-i, --input` | 源文件夹（存放 `.flac` / `.mp3` 和 `.lrc`，文件名需同名） |
| `-o, --output` | 输出文件夹（嵌入歌词后的 `.flac`） |

### 行为说明

- 按文件名（不含扩展名）匹配 `.flac` / `.mp3` 与 `.lrc`
- 同名 `flac` + `mp3` 并存时优先处理 `flac`
- 输出文件夹已有同名文件时自动跳过，不覆盖
- 处理失败会清理残留的残文件

## 依赖

| 包 | 用途 |
|---|---|
| [mutagen](https://mutagen.readthedocs.io/) | 读写 FLAC 元数据 |
| [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) | 自带 ffmpeg 二进制，用于 MP3→FLAC 转换 |

## 验证歌词是否嵌入

```bash
uv run python -c "
from mutagen.flac import FLAC
audio = FLAC('输出/歌曲名.flac')
print(audio.get('LYRICS', ['未找到'])[0][:200])
"
```
