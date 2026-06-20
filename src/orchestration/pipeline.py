"""
ارکستراتور اصلی: عکس ورودی → Job → mesh (از طریق یک MeshGenerator) →
کد بلندر (از طریق blender_bridge).

نسبت به نسخه‌ی pro_blender_pipeline:
  - وضعیت Job در هر مرحله به‌روزرسانی و ذخیره می‌شود (مفید برای دیباگ و
    برای این‌که Claude بتواند بعداً بپرسد "این Job در چه مرحله‌ای متوقف شد؟").
  - خطاها گرفته می‌شوند و در Job ثبت می‌شوند، نه این‌که فقط traceback خام بدهند.
  - انتخاب generator از طریق یک registry قابل توسعه است، نه if/elif ثابت.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from blender_bridge import build_import_script, save_script_to_file
from core.config import PipelineConfig
from core.job import JobStatus, PipelineJob
from generators.base import MeshGenerator
from generators.triposr_generator import TripoSRGenerator

# registry قابل توسعه: برای افزودن مدل تازه، فقط یک ورودی این‌جا اضافه می‌شود.
GENERATOR_REGISTRY: dict[str, Callable[[PipelineConfig], MeshGenerator]] = {
    "triposr": lambda config: TripoSRGenerator(config.triposr),
}


class Pipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config

        if config.generator not in GENERATOR_REGISTRY:
            available = ", ".join(GENERATOR_REGISTRY)
            raise ValueError(
                f"generator '{config.generator}' در registry نیست. "
                f"گزینه‌های موجود: {available}"
            )

        self.generator: MeshGenerator = GENERATOR_REGISTRY[config.generator](config)
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """مدل را فقط در صورت نیاز و فقط یک‌بار بارگذاری می‌کند (lazy loading)."""
        if not self._loaded:
            self.generator.load()
            self._loaded = True

    def run(self, image_path: str | Path, object_name: str = "GeneratedMesh") -> PipelineJob:
        """
        اجرای کامل pipeline برای یک عکس: ساخت Job → تولید mesh → ساخت
        اسکریپت بلندر. خروجی: شیء PipelineJob با مسیرهای mesh و اسکریپت
        و وضعیت نهایی (DONE یا FAILED).
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"عکس ورودی پیدا نشد: {image_path}")

        job = PipelineJob(input_image=image_path, output_root=self.config.output.root_dir)
        job.mark(JobStatus.CREATED)

        try:
            job.mark(JobStatus.GENERATING_MESH)
            self._ensure_loaded()

            self.generator.generate_from_path(image_path, job.mesh_path)

            job.mark(JobStatus.MESH_READY)

            job.mark(JobStatus.BUILDING_SCENE)
            bridge_cfg = self.config.blender_bridge
            code = build_import_script(
                mesh_path=job.mesh_path,
                object_name=object_name,
                base_color=bridge_cfg.default_material_color,
                target_size=bridge_cfg.target_size,
                clear_scene=bridge_cfg.clear_scene_before_import,
                apply_material=bridge_cfg.auto_apply_material,
                normalize_scale=bridge_cfg.scale_to_fit,
                add_lighting=bridge_cfg.add_default_lighting,
            )
            save_script_to_file(code, job.blender_script_path)

            job.mark(JobStatus.DONE)

        except Exception as exc:  # noqa: BLE001 — عمداً گسترده، چون می‌خواهیم هر خطا در Job ثبت شود
            job.mark(JobStatus.FAILED, error=str(exc))
            raise

        return job
