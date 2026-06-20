"""
نقطه‌ی ورود اصلی برای اجرای pipeline از خط فرمان.

تفاوت کلیدی با نسخه‌ی pro_blender_pipeline: مسیر src به sys.path اضافه
می‌شود قبل از import، پس این اسکریپت از هر پوشه‌ای که اجرا شود کار می‌کند
(نه فقط از ریشه‌ی پروژه) — برخلاف نسخه‌ی قبلی که با ModuleNotFoundError
خراب می‌شد.

اجرا:
    python scripts/run_pipeline.py path/to/image.jpg
    python scripts/run_pipeline.py path/to/image.jpg --object-name MyModel
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from core.config import load_config  # noqa: E402 — بعد از تنظیم sys.path عمدی است
from orchestration.pipeline import Pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="اجرای کامل blender_pipeline برای یک عکس")
    parser.add_argument("image", type=str, help="مسیر فایل عکس ورودی")
    parser.add_argument(
        "--config", type=str, default=str(PROJECT_ROOT / "configs" / "default.yaml")
    )
    parser.add_argument("--object-name", type=str, default="GeneratedMesh")
    args = parser.parse_args()

    config = load_config(args.config)
    pipeline = Pipeline(config)

    print(f"[اطلاع] شروع Job برای عکس: {args.image}")
    job = pipeline.run(args.image, object_name=args.object_name)

    print(f"[اطلاع] Job تمام شد — شناسه: {job.id}")
    print(f"[اطلاع] وضعیت نهایی: {job.status.value}")
    print(f"[اطلاع] مسیر mesh: {job.mesh_path}")
    print(f"[اطلاع] مسیر اسکریپت بلندر: {job.blender_script_path}")
    print()
    print(
        "[راهنما] برای اجرای این صحنه در بلندر از طریق Claude، محتوای فایل "
        f"'{job.blender_script_path}' را به ابزار execute_blender_code "
        "(از طریق blender-mcp) بده."
    )


if __name__ == "__main__":
    main()
