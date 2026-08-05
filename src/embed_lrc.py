"""
Batch embed LRC lyrics into FLAC files.
MP3 files are converted to FLAC (preserving metadata & cover art) first.

Usage:
    uv run src/embed_lrc.py --input ./音乐 --output ./输出
"""

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

import imageio_ffmpeg
from mutagen.flac import FLAC

_FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def fmt_size(path: Path) -> str:
    """Return human-readable file size."""
    b = path.stat().st_size
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


def scan_folder(input_dir: Path) -> dict:
    """Scan input dir and return stats + matched pairs + orphans."""
    flacs = {f.stem: f for f in input_dir.glob("*.flac")}
    mp3s = {f.stem: f for f in input_dir.glob("*.mp3")}
    lrcs = {f.stem: f for f in input_dir.glob("*.lrc")}

    all_audio = set(flacs) | set(mp3s)
    common = sorted(all_audio & set(lrcs))
    orphans_audio = sorted(all_audio - set(lrcs))
    orphans_lrc = sorted(set(lrcs) - all_audio)
    conflicts = sorted(set(flacs) & set(mp3s) & set(lrcs))

    # 同一歌名同时有 flac 和 mp3 时，优先处理 flac（无需转换）
    pairs = []
    for stem in common:
        lrc_path = lrcs[stem]
        if stem in flacs:
            pairs.append((flacs[stem], lrcs[stem], "flac"))
        else:
            pairs.append((mp3s[stem], lrcs[stem], "mp3"))

    return {
        "pairs": pairs,
        "orphans_audio": orphans_audio,
        "orphans_lrc": orphans_lrc,
        "conflicts": conflicts,
        "total_flac": len(flacs),
        "total_mp3": len(mp3s),
        "total_lrc": len(lrcs),
    }


def convert_mp3_to_flac(mp3_path: Path, flac_path: Path) -> bool:
    """Convert MP3 to FLAC via ffmpeg, preserving metadata and cover art."""
    try:
        proc = subprocess.run(
            [
                _FFMPEG, "-y", "-loglevel", "error",
                "-i", str(mp3_path),
                "-map", "0", "-map_metadata", "0",
                "-c:a", "flac",
                str(flac_path),
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        print("  └─ ✗ 转换超时（超过 10 分钟）", file=sys.stderr)
        return False

    if proc.returncode != 0:
        err = proc.stderr.strip()
        print(f"  └─ ✗ ffmpeg 转换失败: {err[-300:]}", file=sys.stderr)
        return False
    return True


def embed_lyrics(flac_path: Path, lrc_path: Path) -> bool:
    """Write LRC content into the FLAC's LYRICS tag."""
    try:
        audio = FLAC(flac_path)
        lyrics = lrc_path.read_text(encoding="utf-8-sig")
        audio["LYRICS"] = lyrics
        audio.save()
        return True
    except Exception as e:
        print(f"  └─ ✗ 歌词嵌入失败: {e}", file=sys.stderr)
        return False


def process_flac(flac_path: Path, lrc_path: Path, output_path: Path) -> bool:
    """Copy FLAC to output (preserves all metadata), then embed lyrics."""
    try:
        shutil.copy2(flac_path, output_path)
    except Exception as e:
        print(f"  └─ ✗ 复制失败: {e}", file=sys.stderr)
        return False
    return embed_lyrics(output_path, lrc_path)


def process_mp3(mp3_path: Path, lrc_path: Path, output_path: Path) -> bool:
    """Convert MP3 to FLAC, then embed lyrics."""
    if not convert_mp3_to_flac(mp3_path, output_path):
        return False
    return embed_lyrics(output_path, lrc_path)


def print_header():
    """Print a clean section header."""
    width = 62
    sep = "─" * width
    print()
    print(f"  {'LRC → FLAC 歌词嵌入工具':^{width}}")
    print(f"  {sep}")


def print_summary(info: dict):
    """Print scanning summary."""
    print(f"  📂 扫描结果")
    print(f"     FLAC 文件: {info['total_flac']} 个")
    print(f"     MP3  文件: {info['total_mp3']} 个")
    print(f"     LRC  文件: {info['total_lrc']} 个")
    print(f"     配对成功: {len(info['pairs'])} 对")

    if info["conflicts"]:
        print(f"     ⚠ 同歌名 flac+mp3 并存（已优先 flac）: {', '.join(info['conflicts'])}")
    if info["orphans_audio"]:
        print(f"     ⚠ 音频无对应 LRC: {', '.join(info['orphans_audio'])}")
    if info["orphans_lrc"]:
        print(f"     ⚠ LRC 无对应音频: {', '.join(info['orphans_lrc'])}")

    print(f"  {'─' * 62}")


def main():
    parser = argparse.ArgumentParser(
        description="将 LRC 歌词嵌入到同名的 FLAC/MP3 文件中（MP3 会先转为 FLAC）"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        type=Path,
        help="源文件夹（存放 .flac/.mp3 和 .lrc）",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        type=Path,
        help="输出文件夹（嵌入歌词后的 .flac）",
    )
    args = parser.parse_args()

    input_dir = args.input.resolve()
    output_dir = args.output.resolve()

    if not input_dir.is_dir():
        print(f"错误: 输入路径不存在或不是文件夹: {input_dir}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # ── 扫描阶段 ──
    print_header()
    print(f"  📁 输入: {input_dir}")
    print(f"  📁 输出: {output_dir}")

    info = scan_folder(input_dir)
    print_summary(info)

    if not info["pairs"]:
        print("  没有匹配的音频 + LRC 文件对，无需处理。\n")
        return

    # ── 处理阶段 ──
    total = len(info["pairs"])
    success = 0
    skipped = 0
    start_time = time.time()

    for idx, (src_path, lrc_path, kind) in enumerate(info["pairs"], 1):
        output_path = output_dir / f"{src_path.stem}.flac"

        # ── 已存在跳过 ──
        if output_path.exists():
            print(f"  [{idx:>3}/{total}] ⏭  {src_path.stem}.flac  ─ 已存在，跳过")
            skipped += 1
            continue

        # ── 处理 ──
        if kind == "flac":
            print(f"  [{idx:>3}/{total}] ▶  嵌入歌词: {src_path.name}")
            ok = process_flac(src_path, lrc_path, output_path)
        else:
            print(f"  [{idx:>3}/{total}] ▶  转换+嵌入: {src_path.name} → {src_path.stem}.flac")
            ok = process_mp3(src_path, lrc_path, output_path)

        if ok:
            success += 1
        else:
            output_path.unlink(missing_ok=True)

    # ── 汇总 ──
    elapsed = time.time() - start_time
    failed = total - success - skipped

    print(f"  {'─' * 62}")
    print(f"  📊 汇总")
    print(f"     总计: {total} 对  |  ✓ 成功: {success}  |  ⏭ 跳过: {skipped}", end="")
    if failed:
        print(f"  |  ✗ 失败: {failed}", end="")
    print(f"\n     耗时: {elapsed:.1f} 秒")
    print()


if __name__ == "__main__":
    main()