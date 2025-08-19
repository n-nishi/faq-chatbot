import os
import pandas as pd
from fuzzywuzzy import fuzz
import openai

# OpenAI APIキーの設定
openai.api_key = os.getenv("OPENAI_API_KEY")

# FAQデータファイルのパス
CSV_FILE = "FAQ検索データ.csv"

# FAQデータの読み込み関数
def load_faq_data():
    try:
        df = pd.read_csv(CSV_FILE, encoding="cp932")
        return df[df["up_check"] == True]
    except Exception as e:
        print(f"FAQデータ読み込み失敗: {e}")
        return pd.DataFrame()  # 空のDataFrame返却で落ちないように

# ChatGPTからの補完回答
def ask_chatgpt(prompt: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたはFAQ対応のチャットボットです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print(f"OpenAI APIエラー: {e}")
        return "OpenAIでの回答取得に失敗しました。"

# カテゴリ一覧を返す
def get_all_categories():
    df = load_faq_data()
    category_series = df["カテゴリ"].dropna().apply(
        lambda x: [c.strip() for c in str(x).splitlines()]
    )
    all_categories = set(cat for sublist in category_series for cat in sublist)
    return sorted(all_categories)

# 質問に対するFAQ or ChatGPTからの回答取得
def get_answer_from_faq_or_chatgpt(message: str, category: str = "") -> str:
    df = load_faq_data()
    if df.empty:
        return "FAQデータの読み込みに失敗しています。"

    msg = message.strip()
    category = category.strip()

    # カテゴリフィルタ（指定されていれば）
    if category:
        def match_category(cell):
            if pd.isna(cell):
                return False
            categories = [c.strip() for c in str(cell).splitlines()]
            return category in categories

        df = df[df["カテゴリ"].apply(match_category)]

    best_match = None
    best_score = 0
    THRESHOLD = 70  # 類似度しきい値（調整可能）

    for _, row in df.iterrows():
        question = str(row["question"]) if pd.notna(row["question"]) else ""
        note = str(row["note"]) if pd.notna(row["note"]) else ""

        # 質問・備考それぞれでスコアを計算（partialとtoken_setの最大値）
        score_q = max(
            fuzz.partial_ratio(msg, question),
            fuzz.token_set_ratio(msg, question)
        )
        score_n = max(
            fuzz.partial_ratio(msg, note),
            fuzz.token_set_ratio(msg, note)
        )
        total_score = max(score_q, score_n)

        if total_score > best_score:
            best_score = total_score
            best_match = row

    # FAQヒット時
    if best_match is not None and best_score >= THRESHOLD:
        return best_match["answer"]

    # ヒットしない場合はChatGPTで補完
    return ask_chatgpt(f"ユーザーからの質問: {msg}")
