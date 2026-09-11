import time

from ..control import ControlState
from ..lms.auth import login
from ..lms.delinquent import DelinquentQueryError, get_delinquent_count
from ..lms.driver import build_driver
from ..lms.navigation import NavigationError, go_to_daily_settlement_calendar
from ..utils.progress import emit_done, emit_log, emit_period

JOB_NAME = "delinquent_manual_query"


def run(job_payload: dict, control: ControlState) -> None:
    """직접 입력한 (sdate~edate) 한 구간만 조회하는 수동 확인용 작업.
    로그인 -> 일일정산달력 이동 -> 조회까지 마치면 브라우저를 열어둔 채
    '중단' 버튼을 누르기 전까지 대기한다.
    """
    sdate = (job_payload.get("sdate") or "").strip()
    edate = (job_payload.get("edate") or "").strip()

    if not sdate or not edate:
        emit_log("조회 기간이 비어 있습니다.", level="error")
        emit_done({"job": JOB_NAME})
        return

    label = f"{sdate} ~ {edate}"
    emit_period("manual", label, sdate, edate, status="processing")

    driver = build_driver()

    try:
        login(driver)
        go_to_daily_settlement_calendar(driver)

        try:
            count = get_delinquent_count(driver, sdate, edate)
            emit_period("manual", label, sdate, edate, status="success", count=count)
        except DelinquentQueryError as exc:
            emit_period("manual", label, sdate, edate, status="failed", reason=str(exc))
            emit_log(f"조회 실패: {exc}", level="error")

        emit_log("조회 완료. 브라우저 창을 직접 확인해주세요.")
        emit_log("'중단' 버튼을 누르기 전까지 브라우저가 열린 상태로 유지됩니다.")

        while not control.should_stop():
            control.wait_if_paused()
            time.sleep(0.5)

        emit_log("사용자 요청으로 조회를 종료합니다.")
    except NavigationError as exc:
        emit_period("manual", label, sdate, edate, status="failed", reason=str(exc))
        emit_log(f"이동 실패: {exc}", level="error")
    finally:
        driver.quit()

    emit_done({"job": JOB_NAME})
