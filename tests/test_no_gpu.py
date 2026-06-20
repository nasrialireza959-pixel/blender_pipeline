"""
تست‌های واحد برای بخش‌هایی از پروژه که نیاز به GPU یا بلندر واقعی ندارند.

اجرا: python -m pytest tests/  (یا  python tests/test_no_gpu.py)

این تست‌ها عمداً محدود به منطق خالص پایتون هستند — چیزی که می‌توان همین
الان (بدون GPU، بدون بلندر باز) واقعاً تأیید کرد. inference واقعی TripoSR
و اجرای زنده‌ی کد bpy در بلندر، تست‌های جدا و دستی نیاز دارند که فقط در
محیط واقعی (Claude Code + GPU + بلندر باز) قابل انجام‌اند.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from blender_bridge.scene_builder import build_import_script
from core.config import PipelineConfig, load_config
from core.job import JobStatus, PipelineJob
from generators.preprocess import flatten_on_gray_background, resize_foreground


def test_resize_foreground_centers_object():
    canvas = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    square = Image.new("RGBA", (40, 40), (255, 0, 0, 255))
    canvas.paste(square, (80, 80), square)

    result = resize_foreground(canvas, foreground_ratio=0.85)
    expected_size = int(40 / 0.85)
    assert result.size == (expected_size, expected_size), "اندازه کانواس باید با foreground_ratio هماهنگ باشد"


def test_flatten_on_gray_background_produces_rgb():
    rgba = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
    flattened = flatten_on_gray_background(rgba)
    assert flattened.mode == "RGB", "خروجی باید RGB باشد (بدون کانال آلفا)"
    assert flattened.size == (10, 10)


def test_build_import_script_contains_modern_obj_import():
    code = build_import_script(mesh_path="outputs/test.obj", object_name="TestObj")
    assert "bpy.ops.wm.obj_import" in code, "باید از API مدرن بلندر ۴.x استفاده شود"
    assert "import_scene.obj" not in code, "نباید از API منسوخ بلندر استفاده شود"


def test_build_import_script_respects_clear_scene_flag():
    code_without_clear = build_import_script(mesh_path="outputs/test.obj", clear_scene=False)
    code_with_clear = build_import_script(mesh_path="outputs/test.obj", clear_scene=True)

    assert "read_factory_settings" not in code_without_clear
    assert "read_factory_settings" in code_with_clear


def test_pipeline_config_validation_rejects_bad_device():
    config = PipelineConfig()
    config.triposr.device = "tpu"  # نامعتبر
    try:
        config.validate()
        assert False, "باید ValueError بدهد"
    except ValueError:
        pass


def test_pipeline_job_creates_directory_and_metadata(tmp_path):
    image_path = tmp_path / "fake.jpg"
    image_path.write_bytes(b"fake-image-data")

    job = PipelineJob(input_image=image_path, output_root=tmp_path / "outputs")
    assert job.job_dir.exists()

    job.mark(JobStatus.DONE)
    assert job.metadata_path.exists()

    reloaded = PipelineJob.load(job.job_dir)
    assert reloaded.status == JobStatus.DONE
    assert reloaded.id == job.id


def test_load_config_from_default_yaml():
    config_path = Path(__file__).resolve().parent.parent / "configs" / "default.yaml"
    config = load_config(config_path)
    assert config.generator == "triposr"
    assert config.triposr.device in ("cuda", "cpu", "auto")


if __name__ == "__main__":
    # اجرای دستی بدون pytest، برای محیط‌هایی که pytest نصب نیست
    import tempfile

    tests = [
        test_resize_foreground_centers_object,
        test_flatten_on_gray_background_produces_rgb,
        test_build_import_script_contains_modern_obj_import,
        test_build_import_script_respects_clear_scene_flag,
        test_pipeline_config_validation_rejects_bad_device,
        test_load_config_from_default_yaml,
    ]

    for test_fn in tests:
        test_fn()
        print(f"OK: {test_fn.__name__}")

    with tempfile.TemporaryDirectory() as tmp:
        test_pipeline_job_creates_directory_and_metadata(Path(tmp))
        print("OK: test_pipeline_job_creates_directory_and_metadata")

    print("\nهمه‌ی تست‌ها با موفقیت اجرا شدند.")
