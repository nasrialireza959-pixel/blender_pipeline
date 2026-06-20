"""
تولید کد bpy برای import کردن mesh و ساخت صحنه‌ی پایه در بلندر.

نسبت به نسخه‌ی pro_blender_pipeline دو اصلاح مهم:
  ۱. از bpy.ops.wm.obj_import (API مدرن بلندر ۴.x) استفاده می‌شود، نه
     bpy.ops.import_scene.obj که در بلندر ۴.x دیگر وجود ندارد و خطا می‌دهد.
  ۲. پاک کردن صحنه (read_factory_settings) دیفالت False است و باید عمداً
     فعال شود — تا کاربری که صحنه‌ی دستی باز دارد، ناخواسته آن را از دست نده.

این توابع رشته‌ی کد bpy برمی‌گردانند. اجرای واقعی این کد یا با اسکریپت
مستقیم در بلندر انجام می‌شود، یا (مسیر اصلی این پروژه) توسط Claude از طریق
ابزار execute_blender_code که blender-mcp فراهم می‌کند.
"""

from __future__ import annotations

from pathlib import Path


def _clear_scene_snippet() -> str:
    return 'bpy.ops.wm.read_factory_settings(use_empty=True)\n'


def _import_mesh_snippet(mesh_path: str | Path, object_name: str | None) -> str:
    mesh_path = Path(mesh_path)
    suffix = mesh_path.suffix.lower()

    if suffix == ".obj":
        import_call = f'bpy.ops.wm.obj_import(filepath=r"{mesh_path}")\n'
    elif suffix in (".glb", ".gltf"):
        import_call = f'bpy.ops.import_scene.gltf(filepath=r"{mesh_path}")\n'
    else:
        raise ValueError(f"فرمت پشتیبانی‌نشده برای import: {suffix}")

    rename = ""
    if object_name:
        rename = (
            "imported_obj = bpy.context.selected_objects[0]\n"
            f'imported_obj.name = "{object_name}"\n'
        )
    return import_call + rename


def _normalize_scale_snippet(object_name: str, target_size: float) -> str:
    return f"""obj = bpy.data.objects.get("{object_name}")
if obj is not None:
    dimensions = obj.dimensions
    max_dim = max(dimensions.x, dimensions.y, dimensions.z)
    if max_dim > 0:
        scale_factor = {target_size} / max_dim
        obj.scale = (scale_factor, scale_factor, scale_factor)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
"""


def _material_snippet(
    object_name: str,
    material_name: str,
    base_color: tuple[float, float, float, float],
) -> str:
    r, g, b, a = base_color
    return f"""obj = bpy.data.objects.get("{object_name}")
if obj is not None:
    mat = bpy.data.materials.new(name="{material_name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = ({r}, {g}, {b}, {a})
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
"""


def _lighting_snippet() -> str:
    return """import math

def _add_area_light(name, location, rotation, power, size):
    light_data = bpy.data.lights.new(name=name, type='AREA')
    light_data.energy = power
    light_data.size = size
    light_obj = bpy.data.objects.new(name=name, object_data=light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.location = location
    light_obj.rotation_euler = rotation
    return light_obj

_add_area_light("KeyLight", (4, -4, 5), (math.radians(45), 0, math.radians(45)), 800, 2.0)
_add_area_light("FillLight", (-4, -3, 3), (math.radians(60), 0, math.radians(-45)), 300, 3.0)
_add_area_light("RimLight", (0, 5, 4), (math.radians(-30), 0, math.radians(180)), 400, 1.5)
"""


def _camera_snippet() -> str:
    return """camera_data = bpy.data.cameras.new("Camera")
camera = bpy.data.objects.new("Camera", camera_data)
bpy.context.collection.objects.link(camera)
camera.location = (3, -3, 2)
camera.rotation_euler = (1.2, 0, 0.8)
bpy.context.scene.camera = camera
"""


def build_import_script(
    mesh_path: str | Path,
    object_name: str = "GeneratedMesh",
    material_name: str = "AutoMaterial",
    base_color: tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0),
    target_size: float = 2.0,
    clear_scene: bool = False,
    apply_material: bool = True,
    normalize_scale: bool = True,
    add_lighting: bool = True,
    add_camera: bool = True,
) -> str:
    """
    تابع ترکیبی اصلی: یک رشته‌ی کد bpy کامل می‌سازد که import، نرمالایز
    اندازه، متریال، نورپردازی و دوربین را پشت‌سرهم انجام می‌دهد.

    این تابع جای build_import_script (ساده و ثابت) در pro_blender_pipeline
    و build_full_import_pipeline_code در نسخه‌ی اول این پروژه را گرفته،
    با این تفاوت که هر مرحله مستقل قابل خاموش/روشن کردن است.
    """
    parts = ["import bpy"]

    if clear_scene:
        parts.append(_clear_scene_snippet())

    parts.append(_import_mesh_snippet(mesh_path, object_name))

    if normalize_scale:
        parts.append(_normalize_scale_snippet(object_name, target_size))

    if apply_material:
        parts.append(_material_snippet(object_name, material_name, base_color))

    if add_lighting:
        parts.append(_lighting_snippet())

    if add_camera:
        parts.append(_camera_snippet())

    return "\n".join(parts)


def save_script_to_file(code: str, output_path: str | Path) -> Path:
    """
    ذخیره‌ی کد bpy تولیدشده در یک فایل .py — مفید برای اجرای دستی در بلندر
    (Scripting tab → Open → Run) در مواردی که اتصال زنده‌ی blender-mcp
    در دسترس نیست.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(code, encoding="utf-8")
    return output_path
