import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .. import config
from ..utils.debug import save_debug_snapshot
from ..utils.progress import emit_log

# LNB 상단 탭: '수강료관리' (실제 아이콘 class 미확인 상태라 텍스트 기준으로 찾는다. TODO: 확인되면 교체)
FEE_MANAGEMENT_MENU_XPATH = "//a[contains(normalize-space(.), '수강료관리')]"

# '일일정산달력' 버튼/링크: 실제 확인된 대상 페이지 경로(assessment_cm/index.php)를 href 기준으로 찾는다.
# 화면에 보이는 라벨이 정확히 '일일정산달력'이 아니더라도(아이콘 버튼 등) href로 찾으므로 영향이 없다.
DAILY_SETTLEMENT_CALENDAR_XPATH = "//a[contains(@href, 'assessment_cm')]"

# 페이지가 제대로 열렸는지 확인용: '미납자기간설정' 라벨 옆의 시작일 입력창
SDATE_INPUT_SELECTOR = "#sdate"


class NavigationError(Exception):
    pass


def go_to_daily_settlement_calendar(driver) -> None:
    """LNB '수강료관리' → '일일정산달력' 진입.

    '수강료관리' 탭을 먼저 클릭해 하위 메뉴를 펼쳐야 '일일정산달력' 링크가 클릭 가능한
    상태가 될 수 있어 우선 시도하되, 이미 펼쳐져 있거나 탭을 못 찾아도(TODO: 실제 선택자
    확인 필요) 치명적인 오류로 보지 않고 '일일정산달력' 링크를 바로 찾는 시도로 넘어간다.
    """
    emit_log("'수강료관리' 메뉴 열기")

    try:
        fee_menu = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, FEE_MANAGEMENT_MENU_XPATH))
        )
        fee_menu.click()
        time.sleep(config.REQUEST_DELAY_SECONDS)
    except TimeoutException:
        emit_log("'수강료관리' 메뉴를 찾지 못했습니다. '일일정산달력' 링크를 바로 찾아봅니다.", level="error")

    emit_log("'일일정산달력' 클릭")

    try:
        calendar_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, DAILY_SETTLEMENT_CALENDAR_XPATH))
        )
    except TimeoutException as exc:
        save_debug_snapshot(driver, "daily_settlement_menu_not_found")
        raise NavigationError("'일일정산달력' 메뉴를 찾지 못했습니다.") from exc

    calendar_link.click()
    time.sleep(config.REQUEST_DELAY_SECONDS)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, SDATE_INPUT_SELECTOR)))
    except TimeoutException as exc:
        save_debug_snapshot(driver, "daily_settlement_page_not_loaded")
        raise NavigationError("일일정산달력 페이지(미납자기간설정)가 열리지 않았습니다.") from exc

    emit_log("일일정산달력 페이지 진입 완료")
