"""
بارگذاری و اعتبارسنجی تنظیمات پروژه از فایل YAML.

نسبت به نسخه‌ی اولیه‌ی این بخش (dataclass خالی بدون اعتبارسنجی)، این نسخه:
  - مقادیر را قبل از ساخت Pipeline چک می‌کند تا خطاهای پیکربندی زود (و با
    پیام واضح) دیده شوند، نه وسط اجرای یک عملیات سنگین GPU.
  - مسیرهای نسبی را به Path تبدیل می‌کند تا در توابع بعدی دردسر کمتری بدهند.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class TripoSRSettings:
    pretrained_repo: str = "stabilityai/TripoSR"
    repo_path: str = "external/TripoSR"
    mesh_resolution: int = 256
    chunk_size: int = 8192
    device: str = "cuda"
    foreground_ratio: float = 0.85
    remove_background: bool = True


@dataclass
class OutputSettings:
    root_dir: Path = field(default_factory=lambda: Path("outputs"))
    mesh_format: str = "obj"


@dataclass
class BlenderBridgeSettings:
    auto_apply_material: bool = True
    default_material_color: tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0)
    scale_to_fit: bool = True
    target_size: float = 2.0
    add_default_lighting: bool = True
    clear_scene_before_import: bool = False  # عمداً پیش‌فرض False؛ پاک کردن صحنه باید انتخابی باشد


@dataclass
class PipelineConfig:
    generator: str = "triposr"
    output: OutputSettings = field(default_factory=OutputSettings)
    triposr: TripoSRSettings = field(default_factory=TripoSRSettings)
    blender_bridge: BlenderBridgeSettings = field(default_factory=BlenderBridgeSettings)

    def validate(self) -> None:
        """بررسی صحت تنظیمات. در صورت مشکل، ValueError با پیام واضح می‌دهد."""
        if self.generator not in ("triposr",):
            raise ValueError(
                f"generator نامعتبر: '{self.generator}'. گزینه‌های فعلی: 'triposr'"
            )

        if self.triposr.mesh_resolution <= 0:
            raise ValueError("triposr.mesh_resolution باید عدد مثبت باشد")

        if self.triposr.device not in ("cuda", "cpu"):
            raise ValueError("triposr.device باید 'cuda' یا 'cpu' باشد")

        if not (0 < self.triposr.foreground_ratio <= 1):
            raise ValueError("triposr.foreground_ratio باید بین صفر و یک باشد")

        if self.output.mesh_format not in ("obj", "glb"):
            raise ValueError("output.mesh_format باید 'obj' یا 'glb' باشد")


def load_config(path: str | Path = "configs/default.yaml") -> PipelineConfig:
    """
    خوانش فایل YAML و ساخت یک PipelineConfig معتبرشده.
    اگر فایل تنظیمات کلیدی را نداشته باشد، مقادیر پیش‌فرض دیتاکلاس‌ها استفاده می‌شود
    (یعنی فایل کانفیگ می‌تواند ناقص باشد و پروژه باز هم کار کند).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"فایل تنظیمات پیدا نشد: {path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    output_data = data.get("output", {})
    output = OutputSettings(
        root_dir=Path(output_data.get("root_dir", "outputs")),
        mesh_format=output_data.get("mesh_format", "obj"),
    )

    triposr_data = data.get("triposr", {})
    triposr = TripoSRSettings(**{**TripoSRSettings().__dict__, **triposr_data})

    bridge_data = data.get("blender_bridge", {})
    bridge_defaults = BlenderBridgeSettings().__dict__
    bridge = BlenderBridgeSettings(**{**bridge_defaults, **bridge_data})

    config = PipelineConfig(
        generator=data.get("generator", "triposr"),
        output=output,
        triposr=triposr,
        blender_bridge=bridge,
    )
    config.validate()
    return config
