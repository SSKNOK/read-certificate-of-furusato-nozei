@echo off
REM ============================================================
REM Python 仮想環境作成 + 必要ライブラリインストールバッチ
REM ============================================================

REM 仮想環境名
set VENV_NAME=venv

REM Python 3 がインストールされているか確認
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python が見つかりません。インストールしてください。
    pause
    exit /b 1
)

REM 既存の仮想環境がある場合は削除するか確認
IF EXIST %VENV_NAME% (
    echo 既存の仮想環境 "%VENV_NAME%" を削除します...
    rmdir /s /q %VENV_NAME%
)

REM 仮想環境作成
echo 仮想環境を作成中...
python -m venv %VENV_NAME%
IF %ERRORLEVEL% NEQ 0 (
    echo 仮想環境の作成に失敗しました。
    pause
    exit /b 1
)

REM 仮想環境をアクティブ化
echo 仮想環境をアクティブ化します...
call %VENV_NAME%\Scripts\activate.bat

REM pip を最新にアップグレード
echo pip をアップグレード中...
python -m pip install --upgrade pip

REM 必要なライブラリをインストール
echo 必要なライブラリをインストール中...
pip install --upgrade wheel setuptools
pip install pdf2image pytesseract spacy opencv-python pillow numpy

REM GiNZA 日本語モデルをダウンロード
echo GiNZA 日本語モデルをインストール中...
pip install ja_ginza

echo ============================================================
echo 仮想環境のセットアップが完了しました！
echo 実行するには:
echo call %VENV_NAME%\Scripts\activate.bat
echo その後、python your_script.py を実行してください。
echo ============================================================
pause
