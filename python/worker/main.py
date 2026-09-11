import argparse
import json
import sys

# Windows에서 콘솔 기본 인코딩(cp949 등)으로 인해 한글 로그가 깨지는 것을 방지.
# Electron이 이 프로세스의 stdout/stdin을 UTF-8로 읽으므로 여기서도 반드시 UTF-8로 맞춰야 한다.
for _stream in (sys.stdin, sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

from .control import ControlState
from .jobs import delinquent_manual_query, delinquent_report, login_test
from .utils.progress import emit_log

# 신규 작업(job) 추가 시 여기에 jobId -> run 함수를 등록한다.
JOBS = {
    "delinquent_report": delinquent_report.run,
    "delinquent_manual_query": delinquent_manual_query.run,
    "login_test": login_test.run,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True, choices=list(JOBS.keys()))
    args = parser.parse_args()

    # 첫 줄: Electron이 보낸 작업 설정 JSON (referenceDate, sdate/edate 등)
    first_line = sys.stdin.readline()
    try:
        job_payload = json.loads(first_line)
    except json.JSONDecodeError:
        emit_log("작업 설정(JSON)을 읽지 못했습니다.", level="error")
        sys.exit(1)

    # 이후 stdin은 pause/resume/stop 제어 메시지용
    control = ControlState()
    control.start()

    run_job = JOBS[args.job]
    run_job(job_payload, control)


if __name__ == "__main__":
    main()
