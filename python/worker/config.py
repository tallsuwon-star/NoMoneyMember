import os
from pathlib import Path

from dotenv import load_dotenv

# python/worker/config.py -> parents[2] == 저장소 루트
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

LMS_ID = os.getenv("LMS_ID", "")
LMS_PASSWORD = os.getenv("LMS_PASSWORD", "")

# TODO: 실제 LMS 관리자 페이지 로그인 URL이 확정되면 .env에 채워넣기
LMS_BASE_URL = os.getenv("LMS_BASE_URL", "")

DATA_DIR = ROOT_DIR / "data"
LOG_DIR = ROOT_DIR / "log"

# 요청/클릭 사이 딜레이 (초)
REQUEST_DELAY_SECONDS = 2.5

# 미납자 집계를 시작하는 기준일 (이전 데이터는 조회하지 않는다)
DELINQUENT_HISTORY_START = "2023-01-01"
