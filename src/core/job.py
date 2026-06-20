"""
الگوی Job: هر بار اجرای pipeline یک "اجرا" مجزا با شناسه‌ی یکتا (UUID) و
پوشه‌ی خروجی اختصاصی خود است. این الگو از پروژه‌ی pro_blender_pipeline
قرض گرفته شده چون ایده‌ی خوبی برای ردیابی و جداسازی اجراهای مختلف است؛
اینجا با ردیابی وضعیت (status) و ثبت خطا تکمیل شده.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class JobStatus(str, Enum):
    CREATED = "created"
    GENERATING_MESH = "generating_mesh"
    MESH_READY = "mesh_ready"
    BUILDING_SCENE = "building_scene"
    DONE = "done"
    FAILED = "failed"


@dataclass
class PipelineJob:
    input_image: Path
    output_root: Path
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    status: JobStatus = JobStatus.CREATED
    error: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        self.input_image = Path(self.input_image)
        self.output_root = Path(self.output_root)
        self.job_dir.mkdir(parents=True, exist_ok=True)

    @property
    def job_dir(self) -> Path:
        return self.output_root / "jobs" / self.id

    @property
    def mesh_path(self) -> Path:
        """مسیر فایل mesh خروجی. پسوند را generator هنگام export مشخص می‌کند."""
        return self.job_dir / "mesh.obj"

    @property
    def blender_script_path(self) -> Path:
        return self.job_dir / "scene.py"

    @property
    def metadata_path(self) -> Path:
        return self.job_dir / "job.json"

    def mark(self, status: JobStatus, error: str | None = None) -> None:
        """به‌روزرسانی وضعیت Job و ذخیره‌ی فوری متادیتا روی دیسک."""
        self.status = status
        if error:
            self.error = error
        self.save_metadata()

    def save_metadata(self) -> None:
        """ذخیره‌ی وضعیت فعلی Job در یک فایل json، برای دیباگ یا بازرسی بعدی."""
        data = asdict(self)
        data["input_image"] = str(self.input_image)
        data["output_root"] = str(self.output_root)
        data["status"] = self.status.value
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, job_dir: str | Path) -> "PipelineJob":
        """بازخوانی یک Job قبلی از روی فایل job.json (مثلاً برای رزومه یا بازرسی)."""
        job_dir = Path(job_dir)
        metadata_path = job_dir / "job.json"
        with open(metadata_path, encoding="utf-8") as f:
            data = json.load(f)

        job = cls(
            input_image=Path(data["input_image"]),
            output_root=Path(data["output_root"]),
            id=data["id"],
        )
        job.status = JobStatus(data["status"])
        job.error = data.get("error")
        job.created_at = data["created_at"]
        return job
