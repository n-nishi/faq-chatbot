import pandas as pd
from fuzzywuzzy import fuzz
import openai
import os

# OpenAIキー読み込み（環境変数）
openai.api_key = os.getenv("OPENAI_API_KEY")

CSV_FILE = "FAQ検索データ.csv"

# カテゴリ抽出
def get_all_categories():
    df = pd.read_csv(CSV_FILE, encoding="cp932")
    df = df[df["up_check"] == True]
    category_series = df["カテゴリ"].dropna().apply(
        lambda x: [c.strip() for c in str(x).splitlines()]
    )
    all_categories = set(cat for sublist in category_series for cat in sublist)
    return sorted(all_categories)

# ChatGPT補完関数
def ask_chatgpt(prompt: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # 必要に応じて変更
            messages=[
                {"role": "system", "content": "あなたはFAQ対応のチャットボットです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print(f"OpenAIエラー: {e}")
        return "OpenAIでの回答取得に失敗しました。"

# 回答ロジック本体
def get_answer(user_message: str, selected_category: str) -> str:
    df = pd.read_csv(CSV_FILE, encoding="cp932")
    df = df[df["up_check"] == True]

    # カテゴリで絞り込み（なければ全件対象）
    if selected_category:
        def match_category(cell):
            if pd.isna(cell):
                return False
            categories = [c.strip() for c in str(cell).splitlines()]
            return selected_category in categories
        df = df[df["カテゴリ"].apply(match_category)]

    best_score = 0
    best_match = None

    for _, row in df.iterrows():
        question = str(row["question"]) if pd.notna(row["question"]) else ""
        note = str(row["note"]) if pd.notna(row["note"]) else ""
        score = max(fuzz.partial_ratio(user_message, question),
                    fuzz.partial_ratio(user_message, note))
        if score > best_score:
            best_score = score
            best_match = row

    if best_match is not None and best_score >= 60:
        return best_match["answer"]
    else:
        return ask_chatgpt(f"ユーザーからの質問: {user_message}")
