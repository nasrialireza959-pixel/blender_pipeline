"""
پیاده‌سازی واقعی MeshGenerator برای TripoSR.

تفاوت کلیدی با نسخه‌ی pro_blender_pipeline: آن نسخه فقط print می‌زد و
هیچ inference واقعی انجام نمی‌داد. این نسخه inference واقعی (بارگذاری
مدل از HuggingFace، پیش‌پردازش، استخراج mesh) را پیاده می‌کند — اما هنوز
نیاز به تست روی یک محیط واقعی با GPU و ریپوی TripoSR کلون‌شده دارد.

⚠️ پیش‌نیاز: ریپوی رسمی TripoSR باید در config.repo_path کلون شده باشد
(به scripts/setup.py مراجعه شود که این کار را خودکار می‌کند).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from PIL import Image

from core.config import TripoSRSettings
from .base import MeshGenerator
from .preprocess import preprocess_image


class TripoSRGenerator(MeshGenerator):
    def __init__(self, settings: TripoSRSettings):
        self.settings = settings
        self.repo_path = Path(settings.repo_path)
        self._model: Any = None
        self._device: str | None = None
        # نکته‌ی عمدی: چک وجود ریپو اینجا (در __init__) انجام نمی‌شود، بلکه در
        # load(). این یعنی ساختن Pipeline/Job ممکن است حتی اگر TripoSR هنوز
        # کلون نشده باشد — و خطا وقتی واقعاً اتفاق می‌افتد در دل یک Job ثبت
        # می‌شود (با job.mark(FAILED, error=...))، نه قبل از ساخته‌شدن Job.

    def load(self) -> None:
        """بارگذاری مدل از HuggingFace Hub. سنگین است؛ فقط یک‌بار صدا زده شود."""
        if not self.repo_path.exists():
            raise RuntimeError(
                f"ریپوی TripoSR در مسیر '{self.repo_path}' پیدا نشد. "
                "ابتدا scripts/setup.py را اجرا کن یا مسیر را در کانفیگ اصلاح کن."
            )
        sys.path.insert(0, str(self.repo_path))

        import torch
        from tsr.system import TSR  # noqa: مستلزم بودن ریپوی TripoSR در sys.path

        device = self.settings.device if torch.cuda.is_available() else "cpu"
        if device != self.settings.device:
            print(
                f"[هشدار] GPU با CUDA پیدا نشد؛ روی '{device}' اجرا می‌شود "
                "(می‌تواند به‌شدت کندتر باشد یا برای رزولوشن بالا کافی نباشد)."
            )

        model = TSR.from_pretrained(
            self.settings.pretrained_repo,
            config_name="config.yaml",
            weight_name="model.ckpt",
        )
        model.renderer.set_chunk_size(self.settings.chunk_size)
        model.to(device)

        self._model = model
        self._device = device

    def generate(self, image: Image.Image, output_path: str | Path) -> Path:
        """
        تولید mesh از یک تصویر PIL (که قبلاً preprocess شده) و ذخیره در output_path.
        """
        if self._model is None:
            raise RuntimeError("مدل بارگذاری نشده؛ ابتدا load() را صدا بزن.")

        import torch
        from tsr.utils import to_gradio_3d_orientation

        with torch.no_grad():
            scene_codes = self._model([image], device=self._device)

        meshes = self._model.extract_mesh(
            scene_codes, resolution=self.settings.mesh_resolution
        )
        mesh = meshes[0]
        mesh = to_gradio_3d_orientation(mesh)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mesh.export(str(output_path))
        return output_path

    def generate_from_path(self, image_path: str | Path, output_path: str | Path) -> Path:
        """
        تابع کمکی: مسیر یک فایل عکس خام را می‌گیرد، پیش‌پردازش را خودش انجام
        می‌دهد، و mesh را تولید می‌کند. برای استفاده‌ی مستقیم بدون نیاز به
        صدا زدن preprocess_image جدا.
        """
        image = preprocess_image(
            image_path,
            foreground_ratio=self.settings.foreground_ratio,
            remove_bg=self.settings.remove_background,
        )
        return self.generate(image, output_path)
