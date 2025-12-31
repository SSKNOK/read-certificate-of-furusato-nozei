@echo off
REM ============================================================
REM Python インストール確認バッチ（ウィンドウを閉じない）
REM ============================================================

REM Python のバージョン確認
python --version >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    python --version
    echo Python はインストールされています。
    pause
    exit /b 0
)

REM python3 コマンドでも確認
python3 --version >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    python3 --version
    echo Python はインストールされています。
    pause
    exit /b 0
)

REM インストールされていない場合
echo Python が見つかりません。
echo 公式サイトからインストールしてください:
echo https://www.python.org/downloads/
pause
exit /b 1
