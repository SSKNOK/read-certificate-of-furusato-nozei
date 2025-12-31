@echo off
REM ============================================================
REM 仮想環境を使って main.py を実行するバッチ
REM ============================================================

REM 仮想環境名
set VENV_NAME=venv

REM 仮想環境が存在するか確認
IF NOT EXIST %VENV_NAME%\Scripts\activate.bat (
    echo 仮想環境 "%VENV_NAME%" が存在しません。
    echo 先に setup_env.bat で仮想環境を作成してください。
    pause
    exit /b 1
)

REM 仮想環境をアクティブ化
call %VENV_NAME%\Scripts\activate.bat

REM main.py の存在確認
IF NOT EXIST main.py (
    echo main.py が見つかりません。
    pause
    exit /b 1
)

REM main.py 実行
echo ============================================================
echo main.py を実行中...
echo ============================================================
python main.py

echo ============================================================
echo 実行完了
echo ============================================================
pause
