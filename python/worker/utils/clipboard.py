"""electron/main/ipc/clipboard.js 가 `python3 clipboard.py` 형태로 직접 실행하는 스크립트.
stdin으로 받은 텍스트를 시스템 클립보드에 복사한다 (pyperclip 사용).
"""
import sys

import pyperclip


def main() -> None:
    # Windows 콘솔 기본 인코딩(cp949 등)으로 한글 요약 텍스트가 깨지는 것을 방지.
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")

    text = sys.stdin.read()
    pyperclip.copy(text)


if __name__ == "__main__":
    main()
