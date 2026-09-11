import re
import time

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .. import config
from ..utils.debug import save_debug_snapshot
from ..utils.progress import emit_log

# 실제 확인된 선택자 (일일정산달력 페이지, /edu/admin_common/assessment_cm/index.php):
# <input type="text" name="sdate" id="sdate" class="form-control from-date ... hasDatepicker">
# <input type="text" name="edate" id="edate" class="form-control to-date ... hasDatepicker">
# <button type="button" onclick="totalClassList( )" class="btn btn-talk">검색</button>
# 검색 결과는 <div id="jq-today-class-list">에 jQuery.load()로 채워진다.
SDATE_INPUT_ID = "sdate"
EDATE_INPUT_ID = "edate"
SEARCH_BUTTON_XPATH = "//button[contains(@onclick, 'totalClassList')]"
RESULT_CONTAINER_ID = "jq-today-class-list"

# 결과 하단 "Showing 1 page of 7 entries" 형태 문구에서 전체 인원수(entries)를 뽑아낸다.
# 이 값이 페이지네이션 여부와 무관하게 항상 전체 인원수이므로 가장 신뢰할 수 있는 소스다.
_ENTRIES_RE = re.compile(r"of\s+([\d,]+)\s+entries", re.IGNORECASE)


class DelinquentQueryError(Exception):
    pass


def set_search_period(driver, sdate: str, edate: str) -> None:
    """#sdate / #edate 입력값을 직접 설정한다.

    두 필드 모두 jQuery UI datepicker가 붙어 있어(hasDatepicker) 클릭/send_keys로 조작하면
    달력 팝업이 뜨면서 이후 조작(검색 버튼 클릭 등)을 방해할 수 있다. 검색 함수
    (totalClassList)는 클릭 시점에 jQuery(".from-date").val() / jQuery(".to-date").val()을
    그대로 읽어가므로, change 이벤트 없이 JS로 value만 바꿔도 검색에는 문제가 없다.
    """
    sdate_el = driver.find_element(By.ID, SDATE_INPUT_ID)
    edate_el = driver.find_element(By.ID, EDATE_INPUT_ID)
    driver.execute_script("arguments[0].value = arguments[1];", sdate_el, sdate)
    driver.execute_script("arguments[0].value = arguments[1];", edate_el, edate)


def get_delinquent_count(driver, sdate: str, edate: str) -> int:
    """미납자기간설정을 (sdate~edate)로 맞추고 검색 후, 결과 인원수를 반환한다.

    일일정산달력의 '검색' 버튼(totalClassList)은 항상 detail_mode=102(원어민 미납)로
    조회하므로 별도 옵션 없이 이 함수만으로 '미납자' 인원수를 얻을 수 있다.
    """
    emit_log(f"미납자 조회: {sdate} ~ {edate}")

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, SDATE_INPUT_ID)))
    except TimeoutException as exc:
        raise DelinquentQueryError("검색 기간 입력창(#sdate)을 찾지 못했습니다.") from exc

    set_search_period(driver, sdate, edate)

    try:
        search_btn = driver.find_element(By.XPATH, SEARCH_BUTTON_XPATH)
    except NoSuchElementException as exc:
        raise DelinquentQueryError("'검색' 버튼을 찾지 못했습니다.") from exc

    search_btn.click()
    # totalClassList()가 결과 영역을 'loading...'으로 바꾼 뒤 비동기로 채우므로,
    # 아래 대기가 로딩 시작 전 완료 상태를 잘못 감지하지 않도록 짧게 먼저 대기한다.
    time.sleep(0.5)

    try:
        WebDriverWait(driver, 20).until(
            lambda d: "loading" not in d.find_element(By.ID, RESULT_CONTAINER_ID).text.lower()
        )
    except TimeoutException as exc:
        save_debug_snapshot(driver, f"delinquent_query_timeout_{sdate}_{edate}")
        raise DelinquentQueryError(f"검색 결과 로딩 시간 초과 ({sdate} ~ {edate})") from exc

    time.sleep(config.REQUEST_DELAY_SECONDS)

    container = driver.find_element(By.ID, RESULT_CONTAINER_ID)
    count = _parse_result_count(container)
    emit_log(f"미납자 조회 결과: {sdate} ~ {edate} -> {count}명")
    return count


def _parse_result_count(container) -> int:
    """결과 영역에서 전체 인원수를 뽑아낸다.

    1순위: 하단 페이지네이션 문구("Showing 1 page of 7 entries")의 entries 값.
           페이지가 여러 장으로 나뉘어도 이 값 자체가 항상 전체 인원수다.
    2순위: 결과 표(NO/이름/... 행)의 데이터 행 개수. 마지막 "Total: ..." 합계 행은
           <td colspan="9">로 되어 있어 이 행만 제외하면 실제 인원수와 같다.
    둘 다 실패하면(빈 결과 등) 0을 반환한다.
    """
    text = container.text
    match = _ENTRIES_RE.search(text)
    if match:
        return int(match.group(1).replace(",", ""))

    rows = container.find_elements(By.CSS_SELECTOR, "table.table-performance-data tbody tr")
    data_rows = [row for row in rows if not row.find_elements(By.CSS_SELECTOR, "td[colspan]")]
    if data_rows:
        return len(data_rows)

    return 0
