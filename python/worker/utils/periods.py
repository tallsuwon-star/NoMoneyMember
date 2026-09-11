"""미납자 보고에 필요한 기간 계산 로직.

- 6개월 구간: 일일정산달력의 '미납자기간설정'이 한 번에 최대 6개월까지만 조회되므로,
  2023-01-01부터 기준일(전날)까지를 반기(1~6월 / 7~12월) 단위로 쪼갠다.
- 최근 월별 구간: 기준일이 속한 '이번달(전날까지, 부분월)' + 직전 4개월(전체월) = 총 5구간.
"""

import calendar
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class Period:
    label: str
    start: date
    end: date


def parse_iso_date(value: str) -> date:
    year, month, day = (int(part) for part in value.split("-"))
    return date(year, month, day)


def month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def build_half_year_chunks(history_start: date, end: date) -> list[Period]:
    """history_start부터 end(포함)까지, 1~6월 / 7~12월 단위로 쪼갠 구간 목록.
    마지막 구간은 end에서 잘린다 (예: 2026-07-01 ~ 2026-09-10).
    """
    if end < history_start:
        return []

    chunks: list[Period] = []
    year = history_start.year
    half = 1 if history_start.month <= 6 else 2

    while True:
        if half == 1:
            chunk_start, chunk_end = date(year, 1, 1), date(year, 6, 30)
        else:
            chunk_start, chunk_end = date(year, 7, 1), date(year, 12, 31)

        if chunk_start > end:
            break

        actual_start = max(chunk_start, history_start)
        actual_end = min(chunk_end, end)
        label = f"{actual_start.strftime('%Y.%m.%d')} ~ {actual_end.strftime('%Y.%m.%d')}"
        chunks.append(Period(label=label, start=actual_start, end=actual_end))

        if half == 1:
            half = 2
        else:
            half = 1
            year += 1

    return chunks


def build_recent_months(end: date, months_back: int = 4) -> list[Period]:
    """end가 속한 달(1일 ~ end, 부분월) + 그 이전 `months_back`개월(전체월).
    최근 달이 먼저 오도록(내림차순) 정렬해 반환한다.
    """
    periods: list[Period] = [Period(label=f"{end.month}월", start=date(end.year, end.month, 1), end=end)]

    year, month = end.year, end.month
    for _ in range(months_back):
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        start = date(year, month, 1)
        finish = month_end(year, month)
        periods.append(Period(label=f"{month}월", start=start, end=finish))

    return periods


def build_report_text(
    reference_date: date,
    history_start: date,
    yesterday: date,
    month_results: list[dict],
    chunk_results: list[dict],
    total: int,
) -> str:
    def count_text(count: int | None) -> str:
        return f"{count}명" if count is not None else "확인 실패"

    lines = [f"<미납자 보고 - {reference_date.strftime('%y.%m.%d')}>"]
    for item in month_results:
        lines.append(f"-{item['label']} : {count_text(item['count'])}")
    lines.append(
        f"-전체 ({history_start.strftime('%Y.%m.%d')} ~ {yesterday.strftime('%Y.%m.%d')}) : {total}명"
    )

    lines.append("")
    lines.append(f"<6개월 구간별 미납자 - {reference_date.strftime('%y.%m.%d')}>")
    for item in chunk_results:
        lines.append(f"-{item['label']} : {count_text(item['count'])}")

    return "\n".join(lines)


def yesterday_of(reference_date: date) -> date:
    return reference_date - timedelta(days=1)
