"""
رابط پایه برای هر مدل تولید mesh از عکس.

این الگو (Abstract Base Class) از pro_blender_pipeline قرض گرفته شده چون
اضافه کردن یک مدل تازه (مثلاً Stable Fast 3D یا TRELLIS) را در آینده به
نوشتن یک کلاس تازه با همین رابط محدود می‌کند، بدون نیاز به تغییر در
orchestration یا blender_bridge.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image


class MeshGenerator(ABC):
    """
    رابط پایه‌ی هر generator. هر زیرکلاس باید load() و generate() را پیاده کند.

    تفکیک load/generate عمدی است: load() عملیات سنگین (دانلود/بارگذاری
    وزن‌های مدل روی GPU) را یک‌بار انجام می‌دهد، و generate() می‌تواند
    چندین بار بدون بارگذاری مجدد صدا زده شود.
    """

    @abstractmethod
    def load(self) -> None:
        """بارگذاری مدل در حافظه/GPU. باید قبل از اولین generate() صدا زده شود."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, image: Image.Image, output_path: str | Path) -> Path:
        """
        تولید mesh از یک تصویر PIL از پیش پردازش‌شده و ذخیره‌ی آن در output_path.
        خروجی: مسیر فایل mesh ذخیره‌شده.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_from_path(self, image_path: str | Path, output_path: str | Path) -> Path:
        """
        تولید mesh مستقیماً از مسیر فایل عکس خام (شامل پیش‌پردازش).
        خروجی: مسیر فایل mesh ذخیره‌شده.
        """
        raise NotImplementedError
