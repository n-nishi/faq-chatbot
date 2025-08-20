import os
import pandas as pd
from dotenv import load_dotenv
from rapidfuzz import fuzz
from openai import OpenAI, APIStatusError

# .envから環境変数読み込み
load_dotenv()

# OpenAI初期化（新SDK対応）
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# モデル設定
MAIN_MODEL = "gpt-4o"
FALLBACK_MODEL = "gpt-3.5-turbo"

# CSVファイルのパス
CSV_FILE = "FAQ検索データ.csv"

# 類似度のしきい値（60以上で一致と判定）
SIMILARITY_THRESHOLD = 60


def ask_chatgpt(prompt: str) -> str:
    """
    OpenAI ChatGPT APIで補完回答を取得。
    クォータ超過時は gpt-3.5-turbo に自動フォールバック。
    """
    def _query_openai(model_name):
        return client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "あなたはFAQ対応のチャットボットです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        ).choices[0].message.content.strip()

    try:
        return _query_openai(MAIN_MODEL)

    except APIStatusError as e:
        if e.status_code == 429:
            print("[WARNING] クォータ超過によりフォールバックを試行します。")
            try:
                return _query_openai(FALLBACK_MODEL)
            except Exception as fallback_error:
                print(f"[ERROR] フォールバックも失敗: {fallback_error}")
                return "APIの使用制限により回答ができません。"
        else:
            print(f"[ERROR] ChatGPTエラー: {e}")
            return "OpenAI APIでエラーが発生しました。"

    except Exception as e:
        print(f"[ERROR] ChatGPT呼び出し失敗: {e}")
        return "ChatGPTとの通信に失敗しました。"


def get_all_categories() -> list:
    """
    CSVからカテゴリ一覧を抽出（改行区切りも対応）
    """
    try:
        df = pd.read_csv(CSV_FILE, encoding="utf-8")
        df = df[df["up_check"] == True]
        category_series = df["カテゴリ"].dropna().apply(
            lambda x: [c.strip() for c in str(x).splitlines()]
        )
        all_categories = set(cat for sublist in category_series for cat in sublist)
        return sorted(all_categories)
    except Exception as e:
        print(f"[ERROR] カテゴリ抽出エラー: {e}")
        return []


def get_answer_from_faq_or_chatgpt(message: str, category: str = "") -> str:
    """
    ユーザーの質問に対して、FAQ検索 or ChatGPT補完で回答する
    """
    print(f"[DEBUG] ユーザー入力: {message}")
    print(f"[DEBUG] 選択カテゴリ: {category}")

    try:
        df = pd.read_csv(CSV_FILE, encoding="utf-8")
        df = df[df["up_check"] == True]
        print(f"[DEBUG] FAQ件数: {len(df)}")
    except Exception as e:
        print(f"[ERROR] CSV読み込み失敗: {e}")
        return "FAQデータの読み込みに失敗しました。"

    # カテゴリで絞り込み（改行複数対応）
    if category:
        def match_category(cell):
            if pd.isna(cell):
                return False
            return category in [c.strip() for c in str(cell).splitlines()]
        df = df[df["カテゴリ"].apply(match_category)]

    # 類似度スコア最大のFAQを検索
    best_row = None
    best_score = 0

    for _, row in df.iterrows():
        q = str(row["question"]) if pd.notna(row["question"]) else ""
        n = str(row["note"]) if pd.notna(row["note"]) else ""
        score = max(
            fuzz.partial_ratio(message, q),
            fuzz.partial_ratio(message, n),
            fuzz.token_set_ratio(message, q),
            fuzz.token_set_ratio(message, n)
        )

        if score > best_score:
            best_score = score
            best_row = row

    if best_row is not None and best_score >= SIMILARITY_THRESHOLD:
        print(f"[DEBUG] 類似度スコア: {best_score}")
        return best_row["answer"]

    print(f"[DEBUG] 類似FAQが見つからず、ChatGPTへ委ねます。スコア={best_score}")
    return ask_chatgpt(f"ユーザーの質問: {message}")
