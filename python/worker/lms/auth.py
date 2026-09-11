import time

from selenium.common.exceptions import NoAlertPresentException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .. import config
from ..utils.progress import emit_log

# 로그인 폼 요소를 실제 id/class 대신 화면에 보이는 placeholder/버튼 텍스트로 찾는다.
# (실제 선택자를 확인하기 전, 우선 눈으로 확인한 텍스트 기준으로 작성)
EMAIL_INPUT_SELECTOR = "input[placeholder='Admin Email']"
PASSWORD_INPUT_SELECTOR = "input[placeholder='Password']"
LOGIN_BUTTON_XPATH = (
    "//button[contains(., 'Login')] | //input[@type='submit' and contains(@value, 'Login')]"
)


class LoginFailedError(Exception):
    pass


def login(driver) -> None:
    """LMS(토크스테이션) 로그인. .env 의 LMS_ID / LMS_PASSWORD 사용."""
    emit_log("LMS 로그인 시도")

    if not config.LMS_BASE_URL:
        raise LoginFailedError("LMS_BASE_URL이 .env에 설정되지 않았습니다.")

    driver.get(config.LMS_BASE_URL)

    _dismiss_alert_if_present(driver)

    try:
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, EMAIL_INPUT_SELECTOR))
        )
    except TimeoutException as exc:
        raise LoginFailedError("로그인 폼(아이디 입력창)을 찾을 수 없습니다.") from exc

    password_input = driver.find_element(By.CSS_SELECTOR, PASSWORD_INPUT_SELECTOR)

    email_input.clear()
    email_input.send_keys(config.LMS_ID)
    password_input.clear()
    password_input.send_keys(config.LMS_PASSWORD)

    time.sleep(config.REQUEST_DELAY_SECONDS)

    login_button = driver.find_element(By.XPATH, LOGIN_BUTTON_XPATH)
    login_button.click()

    time.sleep(config.REQUEST_DELAY_SECONDS)

    _dismiss_alert_if_present(driver)

    # TODO: 로그인 성공 여부를 판별하는 요소(예: 대시보드 표시)를 확인하고,
    # 실패 시(아이디/비번 틀림 등) LoginFailedError를 발생시켜야 한다.
    emit_log("LMS 로그인 시도 완료 (TODO: 성공 여부 검증 로직 추가 필요)")


def _dismiss_alert_if_present(driver, timeout: float = 3) -> None:
    """페이지 진입 시 뜨는 JS alert('먼저 관리자 로그인 후 이용하세요' 등)를 자동으로 닫는다."""
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert_text = driver.switch_to.alert.text
        emit_log(f"알림창 감지 후 닫음: {alert_text}")
        driver.switch_to.alert.accept()
    except (TimeoutException, NoAlertPresentException):
        pass
