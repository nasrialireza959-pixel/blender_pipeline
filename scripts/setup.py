"""
راه‌اندازی محیط: کلون کردن ریپوی رسمی TripoSR و نصب وابستگی‌هایش.

اجرا: python scripts/setup.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_DIR = PROJECT_ROOT / "external"
TRIPOSR_DIR = EXTERNAL_DIR / "TripoSR"
TRIPOSR_REPO_URL = "https://github.com/VAST-AI-Research/TripoSR.git"


def clone_triposr_if_needed() -> None:
    if TRIPOSR_DIR.exists():
        print(f"[اطلاع] TripoSR از قبل در {TRIPOSR_DIR} وجود دارد؛ کلون رد می‌شود.")
        return

    EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[اطلاع] کلون کردن TripoSR از {TRIPOSR_REPO_URL} ...")
    subprocess.run(["git", "clone", TRIPOSR_REPO_URL, str(TRIPOSR_DIR)], check=True)


def install_requirements() -> None:
    requirements_file = TRIPOSR_DIR / "requirements.txt"
    if not requirements_file.exists():
        print(
            "[هشدار] requirements.txt در ریپوی TripoSR پیدا نشد؛ "
            "ممکن است ساختار ریپو تغییر کرده باشد."
        )
        return

    print("[اطلاع] نصب وابستگی‌های TripoSR ...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
        check=True,
    )


def main() -> None:
    clone_triposr_if_needed()
    install_requirements()
    print("[اطلاع] راه‌اندازی کامل شد.")
    print(f"[اطلاع] مسیر ریپوی TripoSR: {TRIPOSR_DIR}")
    print("[اطلاع] حالا می‌توانی scripts/run_pipeline.py را اجرا کنی.")


if __name__ == "__main__":
    main()
