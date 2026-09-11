from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def build_driver() -> webdriver.Chrome:
    """항상 화면에 보이는 크롬으로 실행한다 (headless 금지).
    Selenium 4.6+ 의 Selenium Manager가 chromedriver를 자동으로 관리한다.
    """
    options = Options()
    options.add_argument("--start-maximized")
    # TODO: 필요 시 사용자 프로필 경로 등 옵션 추가

    return webdriver.Chrome(options=options)
