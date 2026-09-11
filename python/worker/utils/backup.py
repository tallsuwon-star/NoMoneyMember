import json
from datetime import datetime
from pathlib import Path

from ..config import DATA_DIR


def save_backup(job_name: str, records: dict | list) -> Path:
    """/data/YYYYMMDD/{job_name}.json 에 결과를 백업 저장한다."""
    day_dir = DATA_DIR / datetime.now().strftime("%Y%m%d")
    day_dir.mkdir(parents=True, exist_ok=True)

    out_path = day_dir / f"{job_name}.json"
    out_path.write_text(json.dumps(records, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return out_path
