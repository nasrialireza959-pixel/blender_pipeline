"""بررسی منطق سلول‌های ۵، ۶، ۷ notebook بدون GPU"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blender_bridge.scene_builder import build_import_script, save_script_to_file
from core.config import load_config
from core.job import JobStatus, PipelineJob


def run():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        img = tmp / "fake.jpg"
        img.write_bytes(b"fake")

        job = PipelineJob(input_image=img, output_root=tmp / "outputs")
        job.mark(JobStatus.GENERATING_MESH)

        # شبیه‌سازی mesh خروجی
        job.mesh_path.parent.mkdir(parents=True, exist_ok=True)
        job.mesh_path.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")

        # ساخت اسکریپت Blender (دقیقاً همان کار pipeline.run)
        config = load_config(Path(__file__).parent.parent / "configs" / "default.yaml")
        bridge = config.blender_bridge
        code = build_import_script(
            mesh_path=job.mesh_path,
            object_name="CoffeeMug",
            base_color=bridge.default_material_color,
            target_size=bridge.target_size,
            clear_scene=bridge.clear_scene_before_import,
            apply_material=bridge.auto_apply_material,
            normalize_scale=bridge.scale_to_fit,
            add_lighting=bridge.add_default_lighting,
        )
        save_script_to_file(code, job.blender_script_path)
        job.mark(JobStatus.DONE)

        # سلول ۵ — بررسی mesh (بدون trimesh؛ روی Colab با trimesh کامل تست می‌شود)
        assert job.mesh_path.exists(), "mesh.obj ساخته نشد!"
        size_kb = job.mesh_path.stat().st_size / 1024
        assert size_kb > 0, "mesh.obj خالی است!"
        content = job.mesh_path.read_text()
        assert content.startswith("v "), "فرمت OBJ معتبر نیست!"
        print(f"[cell 5] mesh.obj exists, size={size_kb:.1f} KB, format=OBJ — PASS")

        # سلول ۶ — بررسی اسکریپت Blender
        script = job.blender_script_path.read_text(encoding="utf-8")
        assert "bpy.ops.wm.obj_import" in script
        assert "import_scene.obj" not in script
        assert "CoffeeMug" in script
        print("[cell 6] Blender 4.x API + object name — PASS")

        # سلول ۷ — بررسی job.json
        metadata = json.loads(job.metadata_path.read_text(encoding="utf-8"))
        assert metadata["status"] == "done"
        assert metadata["error"] is None
        assert len(metadata["id"]) == 12, f"UUID باید 12 کاراکتر باشد، هست: {len(metadata['id'])}"
        print(f"[cell 7] status=done, error=None, UUID={len(metadata['id'])} chars — PASS")

    print("\nAll notebook cells (no-GPU): PASS")


if __name__ == "__main__":
    run()
