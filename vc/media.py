"""ffprobe / ffmpeg 與 GPU 硬體編碼共用包裝。"""
from __future__ import annotations

import functools
import json
import os
import re
from fractions import Fraction
from pathlib import Path

from vc.tools import find_tool, run

HW_ENCODERS = ("h264_nvenc", "hevc_nvenc", "av1_nvenc", "h264_qsv", "h264_amf")


def ffmpeg() -> str:
    exe = find_tool("ffmpeg")
    if not exe:
        raise FileNotFoundError("找不到 ffmpeg，執行 python -m vc doctor")
    return exe


def ffprobe() -> str:
    exe = find_tool("ffprobe")
    if not exe:
        raise FileNotFoundError("找不到 ffprobe，執行 python -m vc doctor")
    return exe


def gpu_encoders() -> list[str]:
    """列出目前 ffmpeg 支援的 GPU 硬體視訊編碼器。"""
    exe = find_tool("ffmpeg")
    if not exe:
        return []
    res = run([exe, "-hide_banner", "-encoders"], timeout=30)
    if res.returncode != 0:
        return []
    out = res.stdout
    return [enc for enc in HW_ENCODERS if re.search(rf"\s{re.escape(enc)}\s", out)]


@functools.lru_cache(maxsize=1)
def _probe_nvenc() -> bool:
    exe = find_tool("ffmpeg")
    if not exe or "h264_nvenc" not in gpu_encoders():
        return False
    res = run([
        exe, "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "color=c=black:s=64x64:d=0.04",
        "-frames:v", "1", "-c:v", "h264_nvenc", "-f", "null", "-",
    ], timeout=15)
    return res.returncode == 0


def can_use_nvenc() -> bool:
    """回傳目前環境是否可啟用 NVIDIA NVENC 硬體編碼（支援 VC_GPU=off 停用）。"""
    mode = os.environ.get("VC_GPU", "auto").strip().lower()
    if mode in ("0", "off", "false", "no"):
        return False
    if mode in ("1", "on", "true", "yes"):
        return "h264_nvenc" in gpu_encoders()
    return _probe_nvenc()


def h264_encode_args(quality: int = 16, cpu_preset: str = "veryfast", use_gpu: bool = True) -> list[str]:
    """回傳 H.264 編碼參數：GPU 可用時採用 h264_nvenc，否則自動降級為 libx264。"""
    if use_gpu and can_use_nvenc():
        return ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", str(quality), "-pix_fmt", "yuv420p"]
    return ["-c:v", "libx264", "-crf", str(quality), "-preset", cpu_preset, "-pix_fmt", "yuv420p"]


def probe(path: Path) -> dict:
    """回傳長度、解析度、影格率、有無聲音。"""
    res = run([ffprobe(), "-v", "error", "-show_entries",
               "format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate",
               "-of", "json", str(path)])
    if res.returncode != 0:
        raise RuntimeError(f"ffprobe 失敗：{res.stderr.strip()}")
    info = json.loads(res.stdout)
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fps = float(Fraction(video["avg_frame_rate"])) if video and video.get("avg_frame_rate", "0/0") != "0/0" else None
    return {
        "duration": float(info["format"]["duration"]),
        "width": video["width"] if video else None,
        "height": video["height"] if video else None,
        "fps": round(fps, 3) if fps else None,
        "video_codec": video["codec_name"] if video else None,
        "has_audio": audio is not None,
        "audio_codec": audio["codec_name"] if audio else None,
    }


def ffmpeg_run(args: list[str], timeout: float = 600) -> None:
    res = run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", *args], timeout=timeout)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg 失敗：{res.stderr.strip()[-500:]}")
