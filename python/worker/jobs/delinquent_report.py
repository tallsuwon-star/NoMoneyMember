from datetime import date, datetime

from selenium.common.exceptions import InvalidSessionIdException, WebDriverException

from .. import config
from ..control import ControlState
from ..lms.auth import login
from ..lms.delinquent import DelinquentQueryError, get_delinquent_count
from ..lms.driver import build_driver
from ..lms.navigation import go_to_daily_settlement_calendar
from ..utils.backup import save_backup
from ..utils.periods import (
    Period,
    build_half_year_chunks,
    build_recent_months,
    build_report_text,
    parse_iso_date,
    yesterday_of,
)
from ..utils.progress import emit_done, emit_log, emit_period

JOB_NAME = "delinquent_report"

MONTHS_BACK = 4


def run(job_payload: dict, control: ControlState) -> None:
    """미납자 보고 작업 전체 흐름.

    1) 기준일(referenceDate, 기본값 오늘)의 전날까지를 대상으로,
       - 2023-01-01부터 전날까지 6개월 단위 구간(chunk)별 미납자 수를 모두 조회해 합산 -> 전체
       - 최근 5개 월(이번 달 부분월 + 직전 4개월 전체월)의 미납자 수를 조회
    2) 위 결과로 보고서 텍스트를 만들어 emit_done으로 전달한다.

    구간 하나 처리 중 오류가 나도 전체를 멈추지 않고 그 구간만 실패 처리한 뒤 다음 구간으로 진행한다.
    """
    reference_date = _parse_reference_date(job_payload.get("referenceDate"))
    history_start = parse_iso_date(config.DELINQUENT_HISTORY_START)
    yesterday = yesterday_of(reference_date)

    months = build_recent_months(yesterday, months_back=MONTHS_BACK)
    chunks = build_half_year_chunks(history_start, yesterday)

    driver = build_driver()
    month_results: list[dict] = []
    chunk_results: list[dict] = []

    try:
        login(driver)
        go_to_daily_settlement_calendar(driver)

        driver = _process_periods(driver, control, months, "month", month_results)
        if not control.should_stop():
            driver = _process_periods(driver, control, chunks, "chunk", chunk_results)
    finally:
        driver.quit()

    total = sum(item["count"] for item in chunk_results if item["count"] is not None)
    report_text = build_report_text(reference_date, history_start, yesterday, month_results, chunk_results, total)

    backup_path = save_backup(
        JOB_NAME,
        {
            "referenceDate": reference_date.isoformat(),
            "yesterday": yesterday.isoformat(),
            "months": month_results,
            "chunks": chunk_results,
            "total": total,
            "reportText": report_text,
        },
    )
    emit_log(f"백업 저장 완료: {backup_path}")

    emit_done(
        {
            "referenceDate": reference_date.isoformat(),
            "yesterday": yesterday.isoformat(),
            "months": month_results,
            "chunks": chunk_results,
            "total": total,
            "reportText": report_text,
        }
    )


def _process_periods(
    driver, control: ControlState, periods: list[Period], kind: str, results: list[dict]
):
    """구간 목록을 순회하며 조회한다. 브라우저 세션이 끊기면 재로그인 후 이어서 진행한다.
    (재시작된 driver를 반환하므로 호출부에서 반드시 반환값으로 갱신해야 한다.)
    """
    for period in periods:
        control.wait_if_paused()
        if control.should_stop():
            emit_log("사용자 요청으로 작업을 중단합니다.")
            break

        emit_period(kind, period.label, period.start, period.end, status="processing")

        try:
            count = get_delinquent_count(driver, period.start.isoformat(), period.end.isoformat())
            results.append({"label": period.label, "start": period.start.isoformat(), "end": period.end.isoformat(), "count": count})
            emit_period(kind, period.label, period.start, period.end, status="success", count=count)
        except DelinquentQueryError as exc:
            _fail(results, period, str(exc))
            emit_period(kind, period.label, period.start, period.end, status="failed", reason=str(exc))
        except (InvalidSessionIdException, WebDriverException) as exc:
            # 브라우저가 죽었거나 강제 종료된 경우: 이 구간만 실패 처리하고 끝내는 게 아니라,
            # 브라우저를 재시작해서 남은 구간들을 계속 이어서 처리한다.
            _fail(results, period, "브라우저 세션 끊김, 재시작 후 재개")
            emit_period(kind, period.label, period.start, period.end, status="failed", reason="브라우저 세션 끊김")
            emit_log(f"브라우저 세션이 끊어졌습니다. 재시작을 시도합니다: {exc}", level="error")
            try:
                try:
                    driver.quit()
                except Exception:  # noqa: BLE001 - 이미 죽은 드라이버 종료 시도는 무시
                    pass
                driver = build_driver()
                login(driver)
                go_to_daily_settlement_calendar(driver)
                emit_log("브라우저 재시작 및 재로그인 완료, 남은 구간 처리를 이어갑니다.")
            except Exception as recovery_exc:  # noqa: BLE001
                emit_log(f"브라우저 재시작 실패, 작업을 중단합니다: {recovery_exc}", level="error")
                break
        except Exception as exc:  # noqa: BLE001 - 구간 단위 오류도 전체 중단 없이 계속 진행해야 함
            _fail(results, period, f"알 수 없는 오류: {exc}")
            emit_period(kind, period.label, period.start, period.end, status="failed", reason=str(exc))

    return driver


def _fail(results: list[dict], period: Period, reason: str) -> None:
    results.append(
        {"label": period.label, "start": period.start.isoformat(), "end": period.end.isoformat(), "count": None, "reason": reason}
    )
    emit_log(f"[실패] {period.label} ({period.start} ~ {period.end}): {reason}", level="error")


def _parse_reference_date(value: str | None) -> date:
    if not value:
        return date.today()
    return datetime.strptime(value, "%Y-%m-%d").date()
