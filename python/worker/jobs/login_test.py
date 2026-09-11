import time

from ..control import ControlState
from ..lms.auth import login
from ..lms.driver import build_driver
from ..utils.progress import emit_done, emit_log

JOB_NAME = "login_test"


def run(job_payload: dict, control: ControlState) -> None:
    """LMS 접속 + 로그인만 확인하는 테스트 작업.
    로그인 후 브라우저를 열어둔 채로 사용자가 화면을 직접 확인할 수 있게 하고,
    '중단' 버튼을 누르기 전까지 대기한다.
    """
    driver = build_driver()

    try:
        login(driver)
        emit_log("로그인 완료. 브라우저 창을 직접 확인해주세요.")
        emit_log("'중단' 버튼을 누르기 전까지 브라우저가 열린 상태로 유지됩니다.")

        while not control.should_stop():
            control.wait_if_paused()
            time.sleep(0.5)

        emit_log("사용자 요청으로 로그인 테스트를 종료합니다.")
    finally:
        driver.quit()

    emit_done({"job": JOB_NAME})
