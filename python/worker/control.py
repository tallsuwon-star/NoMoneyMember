import json
import sys
import threading
import time


class ControlState:
    """stdin으로 들어오는 제어 명령({"type":"control","action":"pause|resume|stop"})을
    백그라운드 스레드에서 계속 읽어 일시정지/중단 상태를 관리한다.

    main.py가 첫 줄(작업 설정 JSON)을 직접 읽은 뒤, 이 클래스가 나머지 stdin을 이어서 읽는다.
    """

    def __init__(self) -> None:
        self._paused = False
        self._stopped = False
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._listen, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def _listen(self) -> None:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            if msg.get("type") != "control":
                continue

            action = msg.get("action")
            with self._lock:
                if action == "pause":
                    self._paused = True
                elif action == "resume":
                    self._paused = False
                elif action == "stop":
                    self._stopped = True

    def wait_if_paused(self) -> None:
        """일시정지 상태라면 재개될 때까지 대기한다. 기간(구간) 단위 루프 시작 시 호출."""
        while True:
            with self._lock:
                if not self._paused:
                    return
            time.sleep(0.5)

    def should_stop(self) -> bool:
        with self._lock:
            return self._stopped
