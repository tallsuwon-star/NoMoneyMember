from datetime import datetime

from .. import config
from .progress import emit_log


def save_debug_snapshot(driver, tag: str) -> None:
    """원하는 요소를 못 찾았을 때, 그 순간 화면과 HTML 구조를 남겨서 원인 파악을 돕는다.
    저장 자체가 실패해도(예: 이미 죽은 드라이버) 작업 흐름에는 영향 없어야 한다.
    """
    try:
        debug_dir = config.DATA_DIR / "debug_screenshots"
        debug_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{timestamp}_{tag}"

        screenshot_path = debug_dir / f"{base_name}.png"
        driver.save_screenshot(str(screenshot_path))

        html_path = debug_dir / f"{base_name}.html"
        html_path.write_text(driver.page_source, encoding="utf-8")

        emit_log(f"디버그 스크린샷/HTML 저장: {screenshot_path.name}, {html_path.name}")
    except Exception as exc:  # noqa: BLE001 - 저장 실패는 무시하고 원래 오류만 전달
        emit_log(f"디버그 스크린샷/HTML 저장 실패: {exc}", level="error")
