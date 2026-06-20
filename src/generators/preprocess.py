"""
پیش‌پردازش عکس ورودی قبل از این‌که به یک MeshGenerator داده شود.

این منطق در نسخه‌ی قبلی پروژه نوشته و با تصویر مصنوعی تست شد (حذف
پس‌زمینه، یافتن bounding box، resize با حفظ نسبت foreground، صاف کردن
روی پس‌زمینه‌ی خاکستری). pro_blender_pipeline اصلاً این مرحله را نداشت.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


def remove_background(image: Image.Image) -> Image.Image:
    """پس‌زمینه را حذف می‌کند و RGBA با کانال آلفای شفاف برمی‌گرداند."""
    from rembg import remove

    result = remove(image)
    return result.convert("RGBA")


def resize_foreground(image: Image.Image, foreground_ratio: float = 0.85) -> Image.Image:
    """
    شیء اصلی را پیدا کرده و در کادر تصویر بازمقیاس‌دهی می‌کند طوری که نسبت
    foreground_ratio از کادر را اشغال کند. ورودی باید RGBA باشد.
    """
    image_array = np.array(image)
    alpha = image_array[:, :, 3]

    nonzero_rows = np.where(alpha.sum(axis=1) > 0)[0]
    nonzero_cols = np.where(alpha.sum(axis=0) > 0)[0]

    if len(nonzero_rows) == 0 or len(nonzero_cols) == 0:
        return image

    top, bottom = nonzero_rows[0], nonzero_rows[-1]
    left, right = nonzero_cols[0], nonzero_cols[-1]

    cropped = image.crop((left, top, right + 1, bottom + 1))

    size = max(cropped.size)
    canvas_size = int(size / foreground_ratio)
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))

    paste_x = (canvas_size - cropped.size[0]) // 2
    paste_y = (canvas_size - cropped.size[1]) // 2
    canvas.paste(cropped, (paste_x, paste_y), cropped)

    return canvas


def flatten_on_gray_background(image: Image.Image, gray_value: float = 0.5) -> Image.Image:
    """تصویر RGBA را روی یک پس‌زمینه‌ی خاکستری یکدست صاف می‌کند (خروجی RGB)."""
    array = np.array(image).astype(np.float32) / 255.0
    rgb = array[:, :, :3]
    alpha = array[:, :, 3:4]

    flattened = rgb * alpha + (1 - alpha) * gray_value
    return Image.fromarray((flattened * 255.0).astype(np.uint8))


def preprocess_image(
    input_path: str | Path,
    foreground_ratio: float = 0.85,
    remove_bg: bool = True,
) -> Image.Image:
    """تابع اصلی: سه مرحله‌ی بالا را به ترتیب صحیح روی یک عکس اجرا می‌کند."""
    image = Image.open(input_path).convert("RGBA" if remove_bg else "RGB")

    if remove_bg:
        image = remove_background(image)
        image = resize_foreground(image, foreground_ratio)
        image = flatten_on_gray_background(image)

    return image
