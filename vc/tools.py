"""外部工具定位與執行。專案內的工具優先於系統 PATH，確保環境可重現。"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 依序搜尋：專案內 FFmpeg、根目錄 Node 工具、Remotion 專案、虛擬環境
LOCAL_BIN_DIRS = (
    ROOT / "tools" / "ffmpeg" / "bin",
    ROOT / "node_modules" / ".bin",
    ROOT / "remotion" / "node_modules" / ".bin",
    ROOT / ".venv" / "Scripts",
)

_EXTS = (".exe", ".cmd", ".bat", "")

# 模型權重放在專案內，避免散落到使用者目錄，也方便整包搬移
MODELS_DIR = ROOT / "models"
WHISPER_DIR = MODELS_DIR / "whisper"


def configure_model_cache() -> None:
    """讓 Hugging Face（Kokoro）與 torch hub 的下載都落在 models/ 底下。"""
    os.environ.setdefault("HF_HOME", str(MODELS_DIR / "hf"))
    os.environ.setdefault("TORCH_HOME", str(MODELS_DIR / "torch"))
    # Windows 一般帳號無法建立 symlink，關掉警告訊息
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


def detect_torch_device() -> str:
    """偵測 PyTorch 推論裝置（支援 VC_DEVICE 環境變數覆寫）。"""
    forced = os.environ.get("VC_DEVICE", "").strip().lower()
    if forced:
        return forced
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        mps = getattr(torch.backends, "mps", None)
        if mps is not None and mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


def find_tool(name: str) -> str | None:
    """回傳工具的絕對路徑；專案內找不到才查 PATH。"""
    for d in LOCAL_BIN_DIRS:
        for ext in _EXTS:
            p = d / f"{name}{ext}"
            if p.is_file():
                return str(p)
    return shutil.which(name)


def use_system_certs() -> None:
    """改用 Windows 憑證存放區驗證 HTTPS。

    公司網路會用自簽憑證檢查加密流量，Python 內建的 certifi 憑證清單不認得，
    所以 Edge TTS 等連線會出現 CERTIFICATE_VERIFY_FAILED。
    """
    import truststore

    truststore.inject_into_ssl()


def run(cmd: list[str], timeout: float = 60) -> subprocess.CompletedProcess:
    """執行指令並擷取輸出；以 UTF-8 解碼，無法解碼的位元組以替代字元處理。"""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
