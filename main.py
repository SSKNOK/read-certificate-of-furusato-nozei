from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
import spacy
import re
import cv2
import numpy as np
from PIL import Image
import logging
import csv
from collections import Counter


# ===== Windows 環境設定 =====
POPPLER_PATH = r"C:\poppler\Library\bin"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ===== ログ設定（ファイル + ターミナル） =====
LOG_DIR = Path.cwd() / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# --- ファイル出力（上書き） ---
file_handler = logging.FileHandler(LOG_DIR / "log.log", mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# --- ターミナル出力 ---
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)


# spaCy + GiNZA（日付抽出用）
nlp = spacy.load("ja_ginza")

# input フォルダ
INPUT_DIR = Path(__file__).parent / "input"

# 金額抽出用 正規表現
AMOUNT_PATTERN = re.compile(
    r'(?:寄附金額|合計金額|金額|請求額|金)?\s*[¥￥]?\s*([\d,]+)\s*円'
)

# 市区町村抽出用 正規表現（都道府県＋市区町村）
CITY_PATTERN = re.compile(
    r'(?:北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|'
    r'茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|神奈川県|'
    r'新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|'
    r'三重県|滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|'
    r'鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|'
    r'福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県)'
    r'[\S]*?(?:市|区|町|村)'
)

# 都道府県削除用
PREF_PATTERN = re.compile(
    r'^(北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|'
    r'茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|神奈川県|'
    r'新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|'
    r'三重県|滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|'
    r'鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|'
    r'福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県)'
)


def preprocess_image(pil_image):
    """OCR精度向上のための画像前処理"""
    img = np.array(pil_image)

    # グレースケール化
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    return Image.fromarray(gray)



def ocr_pdf_with_tesseract(pdf_path: Path):
    """
    PDF → 画像 → Tesseract OCR
    各ページごとの全文テキストをリストで返す
    デバッグ用に前処理後画像を保存する
    """
    images = convert_from_path(
        pdf_path,
        dpi=800,
        poppler_path=POPPLER_PATH
    )

    page_texts = []

    for page_no, image in enumerate(images, start=1):
        # 画像前処理
        image = preprocess_image(image)

        # ===== デバッグ用画像保存 =====
        # debug_image_name = f"{pdf_path.stem}_page{page_no}_debug.png"
        # image.save(debug_image_name)

        # Tesseract 設定
        custom_config = r'--oem 3 --psm 4'

        # OCR実行
        text = pytesseract.image_to_string(
            image,
            lang="jpn",
            config=custom_config
        )

        page_texts.append(text)

    return page_texts



def ptint_ocr_rezult(text: str):
    """
    デバッグ用のOCR解析結果出力処理
    """
    logging.debug("---- OCR解析結果 ----")
    logging.debug(text)



def print_ginza_result(text: str):
    """
    デバッグ用のginza解析結果出力処理
    """
    logging.debug("---- GiNZA解析結果 ----")
    doc = nlp(text)
    for ent in doc.ents:
        logging.debug(f"[{ent.label_}] {ent.text}")



def extract_city(text: str):
    """
    自治体名抽出（GiNZA頻度優先追加版）

    優先度:
    1. 正規表現で複数件 → 2件目
    2. GiNZAで複数件 → 2件目
    3. GiNZAで複数件 → 最頻出
    4. 正規表現で1件 → 1件目
    5. GiNZAで1件 → 1件目
    """
    logging.debug("---- 自治体抽出　開始 ----")

    cities_regex = list(dict.fromkeys(CITY_PATTERN.findall(text)))

    GINZA_CITY_LABELS = {"City", "Province", "GPE", "LOC"}

    cities_ginza_all = []
    doc = nlp(text)

    for ent in doc.ents:
        if ent.label_ in GINZA_CITY_LABELS:
            if re.search(r'(市|区|町|村)$', ent.text):
                cities_ginza_all.append(ent.text)

    cities_ginza_unique = list(dict.fromkeys(cities_ginza_all))

    if len(cities_regex) >= 2:
        city = PREF_PATTERN.sub("", cities_regex[1])
        return [city]

    if len(cities_ginza_unique) >= 2:
        city = PREF_PATTERN.sub("", cities_ginza_unique[1])
        return [city]

    if len(cities_ginza_all) >= 2:
        most_common_city, _ = Counter(cities_ginza_all).most_common(1)[0]
        city = PREF_PATTERN.sub("", most_common_city)
        return [city]

    if len(cities_regex) == 1:
        city = PREF_PATTERN.sub("", cities_regex[0])
        return [city]

    if len(cities_ginza_unique) == 1:
        city = PREF_PATTERN.sub("", cities_ginza_unique[0])
        return [city]

    return []



def extract_date(text: str):
    """
    日付抽出（和暦 → 西暦変換）

    GiNZAの固有表現認識（NER）を用いて日付を取得
    補助的に正規表現で「令和○年○月○日」形式の日付も抽出
    「平成」の日付は除外
    月・日の組み合わせを 100*m + d で比較し、最も早い日付を返却
    """
    text_clean = text.replace("\n", " ").replace("　", " ")
    candidates = []

    doc = nlp(text_clean)
    logging.debug("---- 日付抽出　開始 ----")

    for ent in doc.ents:

        if ent.label_ != "Date":
            continue

        if "平成" in ent.text:
            continue

        match = re.search(r'(\d+)年(\d+)月(\d+)?日?', ent.text)
        if not match:
            continue

        ry = int(match.group(1))
        m = int(match.group(2))
        d = int(match.group(3)) if match.group(3) else 1
        y = 2018 + ry  #  西暦変換

        if re.search(rf'平成\s*{y}\s*年', text_clean):
            continue

        if not re.search(rf'令和\s*{y}\s*年', text_clean):
            continue

        candidates.append((100 * m + d, f"{y:04d}/{m:02d}/{d:02d}"))

    for match in re.finditer(r'令和\s*(\d+)年(\d+)月(\d+)?日?', text_clean):
        ry, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3) or 1)
        y = 2018 + ry
        candidates.append((100 * m + d, f"{y:04d}/{m:02d}/{d:02d}"))

    if not candidates:
        return []

    candidates.sort(key=lambda x: x[0])
    return [candidates[0][1]]



def extract_amount(text: str):
    """
    寄付金額抽出

    正規表現で金額を抽出
    """
    logging.debug("---- 寄付金額抽出　開始 ----")
    for match in AMOUNT_PATTERN.finditer(text):
        amount = match.group(1).replace(",", "")
        return [amount]
    return []



def main():
    """
    メイン処理
    """
    logging.info("ふるさと納税寄付金証明書読み取り処理を開始します")

    OUTPUT_DIR = Path.cwd() / "output"
    OUTPUT_DIR.mkdir(exist_ok=True)

    output_csv = OUTPUT_DIR / "output.csv"

    pdf_files = sorted(INPUT_DIR.glob("*.pdf"))
    if not pdf_files:
        logging.warning("inputフォルダにPDFがありません")
        return

    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["ファイル名", "ページ数", "市区町村名", "日付", "金額"])

        for pdf_file in pdf_files:
            logging.info(f"========= 処理開始: {pdf_file.name} =========")

            page_texts = ocr_pdf_with_tesseract(pdf_file)

            for page_no, text in enumerate(page_texts, start=1):
                logging.info(f"--------- 処理開始: {pdf_file.name} ページ{page_no} ---------")
                if not text.strip():
                    logging.warning(f"{pdf_file.name} ページ{page_no}: OCR失敗")
                    continue

                ptint_ocr_rezult(text)
                print_ginza_result(text)
                cities = extract_city(text)
                dates = extract_date(text)
                amounts = extract_amount(text)

                writer.writerow([
                    pdf_file.name,
                    page_no,
                    cities[0] if cities else "",
                    dates[0] if dates else "",
                    amounts[0] if amounts else ""
                ])

    logging.info("処理完了")



if __name__ == "__main__":
    main()
