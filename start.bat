@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

npm start

echo.
echo 프로그램이 종료되었습니다. 오류 메시지가 보이면 이 창을 캡처해서 알려주세요.
pause
