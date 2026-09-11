import logging
from datetime import datetime

from .config import LOG_DIR


def get_logger(job_name: str) -> logging.Logger:
    """작업별 로거를 생성한다. 실행 로그는 /log/{job_name}_{timestamp}.log 에 저장된다."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(job_name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(LOG_DIR / f"{job_name}_{timestamp}.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(file_handler)

    return logger
