# Blender Pipeline (v2 — نسخه‌ی ترکیبی)

[![CI](https://github.com/nasrialireza959-pixel/blender_pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/nasrialireza959-pixel/blender_pipeline/actions/workflows/ci.yml)

تولید خودکار مدل سه‌بعدی از روی یک عکس و وارد کردن آن در بلندر، با
ارکستراسیون توسط Claude (از طریق Claude Code یا Claude Desktop + blender-mcp).

این نسخه ترکیبی از دو پروژه‌ی قبلی است:
- **نسخه‌ی اول** (طراحی خودم): پیش‌پردازش تست‌شده‌ی عکس، inference واقعی
  TripoSR، API مدرن بلندر.
- **نسخه‌ی آپلودی کاربر** (`pro_blender_pipeline`): الگوی `Job` با شناسه‌ی
  یکتا، و `MeshGenerator` به‌عنوان کلاس پایه‌ی انتزاعی (قابل تعویض مدل).

## معماری

```
عکس ورودی
   │
   ▼
┌─────────────────────────┐
│  Pipeline (orchestration)│  ساخت Job → صدا زدن Generator → ساخت اسکریپت بلندر
└─────────────────────────┘
   │                    │
   ▼                    ▼
┌──────────────┐   ┌──────────────────┐
│ generators/   │   │ blender_bridge/   │
│ TripoSRGen.   │   │ scene_builder.py  │
│ (واقعی، GPU)  │   │ (کد bpy می‌سازد)  │
└──────────────┘   └──────────────────┘
   │                    │
   ▼                    ▼
 mesh.obj          scene.py (کد bpy)
   │                    │
   └────────┬───────────┘
            ▼
   outputs/jobs/<job-id>/
   ├── job.json   (وضعیت و متادیتای اجرا)
   ├── mesh.obj
   └── scene.py
```

## چه چیزی نسبت به دو نسخه‌ی قبلی عوض شده

| بخش | تغییر |
|---|---|
| `core/job.py` | الگوی Job از نسخه‌ی آپلودی گرفته شد، اما با وضعیت (`JobStatus`)، ثبت خطا، و ذخیره/بازخوانی متادیتا (`job.json`) تکمیل شد |
| `core/config.py` | اعتبارسنجی واقعی (`validate()`) اضافه شد — مقادیر نامعتبر (device اشتباه، resolution منفی و...) زود و با پیام واضح رد می‌شوند |
| `generators/base.py` | کلاس انتزاعی (`ABC`) از نسخه‌ی آپلودی گرفته شد |
| `generators/triposr_generator.py` | inference واقعی (بارگذاری مدل، استخراج mesh) از نسخه‌ی اول گرفته شد — نسخه‌ی آپلودی این بخش را فقط با `print` جا گذاشته بود |
| `blender_bridge/scene_builder.py` | از `bpy.ops.wm.obj_import` (API مدرن بلندر ۴.x) استفاده می‌شود؛ نسخه‌ی آپلودی از `import_scene.obj` (منسوخ، در ۴.x خطا می‌دهد) استفاده کرده بود |
| | پاک کردن صحنه (`clear_scene`) اختیاری و پیش‌فرض خاموش است — نسخه‌ی آپلودی همیشه صحنه را پاک می‌کرد، حتی بدون اطلاع کاربر |
| `orchestration/pipeline.py` | registry قابل‌توسعه برای انتخاب generator، به‌جای `if/elif` ثابت؛ ردیابی وضعیت Job در هر مرحله |
| import پروژه | مشکل `ModuleNotFoundError` نسخه‌ی آپلودی (نبود `__init__.py` و ناهماهنگی مسیر اجرا) حل شد — `scripts/run_pipeline.py` مسیر `src` را قبل از import به `sys.path` اضافه می‌کند |
| `tests/` | نسخه‌ی آپلودی هیچ تستی نداشت و حتی اجرای پایه‌اش (بدون GPU) با خطا متوقف می‌شد. این نسخه ۷ تست واقعی دارد که همگی پاس می‌شوند بدون نیاز به GPU یا بلندر باز |

## پیش‌نیازها

1. **بلندر** (نسخه‌ی ۴.x توصیه می‌شود، چون از API مدرن `obj_import` استفاده شده) با افزونه‌ی [blender-mcp](https://github.com/ahujasid/blender-mcp) نصب و فعال.
2. **GPU** برای اجرای TripoSR — لوکال (NVIDIA/CUDA) یا Google Colab.
3. **Claude Code** یا **Claude Desktop** متصل به blender-mcp برای ارکستراسیون نهایی.
4. پایتون ۳.۱۰+

## نصب و اجرا

```bash
pip install -r requirements.txt

# کلون کردن TripoSR (یک‌بار)
python scripts/setup.py

# اجرای کامل (نیاز به GPU برای این مرحله)
python scripts/run_pipeline.py path/to/photo.jpg --object-name MyModel
```

خروجی در `outputs/jobs/<job-id>/` قرار می‌گیرد:
- `job.json` — وضعیت و متادیتای اجرا
- `mesh.obj` — مدل سه‌بعدی تولید‌شده
- `scene.py` — کد bpy آماده برای اجرا در بلندر (مستقیم یا از طریق Claude/blender-mcp)

## اجرای تست‌ها (بدون نیاز به GPU)

```bash
python tests/test_no_gpu.py
# یا
python -m pytest tests/
```

این تست‌ها منطق پیش‌پردازش عکس، تولید کد bpy، اعتبارسنجی کانفیگ، و چرخه‌ی
عمر Job را تأیید می‌کنند — بدون نیاز به GPU یا بلندر باز.

## نقش Claude در این پروژه

Claude (با Claude Code یا Claude Desktop) نقش ارکستراتور نهایی را دارد:
۱. اجرای `run_pipeline.py` (لوکال در صورت وجود GPU، یا راهنمایی برای Colab).
۲. خوانش فایل `scene.py` تولیدشده.
۳. اجرای محتوای آن از طریق ابزار `execute_blender_code` که blender-mcp فراهم می‌کند.
۴. اصلاح صحنه بر اساس بازخورد کاربر (نور، دوربین، متریال) با دستورات bpy تازه.

## وضعیت فعلی و آنچه هنوز تست نشده

- ✅ پیش‌پردازش عکس، کانفیگ، Job، و تولید کد bpy — همگی با تست واقعی تأیید شدند.
- ⚠️ inference واقعی TripoSR — نیاز به GPU واقعی برای تست (هنوز انجام نشده).
- ⚠️ اتصال زنده‌ی `scene.py` به بلندر از طریق blender-mcp — نیاز به بلندر باز و افزونه‌ی نصب‌شده (هنوز انجام نشده).

به `docs/architecture.md` برای جزئیات بیشتر مراجعه کن.
