import json
import sys
from datetime import date


def emit(payload: dict) -> None:
    """Electron 메인 프로세스가 한 줄씩 파싱할 수 있도록 JSON을 stdout에 출력하고 즉시 flush한다."""
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def emit_log(message: str, level: str = "info") -> None:
    emit({"type": "log", "level": level, "message": message})


def _as_iso(value) -> str:
    return value if isinstance(value, str) else value.isoformat()


def emit_period(
    kind: str,
    label: str,
    start: date | str,
    end: date | str,
    status: str,
    count: int | None = None,
    reason: str | None = None,
) -> None:
    """구간(월별/6개월/수동조회) 단위 진행 상황을 스트리밍한다.

    kind: "month" | "chunk" | "manual"
    status: pending | processing | success | failed
    """
    payload = {
        "type": "period",
        "kind": kind,
        "label": label,
        "start": _as_iso(start),
        "end": _as_iso(end),
        "status": status,
    }
    if count is not None:
        payload["count"] = count
    if reason is not None:
        payload["reason"] = reason
    emit(payload)


def emit_done(summary: dict) -> None:
    emit({"type": "done", "summary": summary})
