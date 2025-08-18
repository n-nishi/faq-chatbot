import pandas as pd
import os
from fuzzywuzzy import fuzz
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

CSV_FILE = "FAQ検索データ.csv"

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
        print(f"OpenAIエラー: {e}")
        return "OpenAIでの回答取得に失敗しました。"

def get_categories_from_csv() -> list:
    df = pd.read_csv(CSV_FILE, encoding="cp932")
    df = df[df["up_check"] == True]

    category_series = df["カテゴリ"].dropna().apply(
        lambda x: [c.strip() for c in str(x).splitlines()]
    )
    all_categories = set(cat for sublist in category_series for cat in sublist)

    return sorted(all_categories)

def get_answer_from_faq(message: str, category: str) -> str:
    df = pd.read_csv(CSV_FILE, encoding="cp932")
    df = df[df["up_check"] == True]

    msg = message.strip()
    selected_category = category.strip()

    if selected_category:
        def match_category(cell):
            if pd.isna(cell):
                return False
            categories = [c.strip() for c in str(cell).splitlines()]
            return selected_category in categories

        filtered_df = df[df["カテゴリ"].apply(match_category)]
    else:
        filtered_df = df

    best_match = None
    best_score = 0

    for _, row in filtered_df.iterrows():
        question = str(row["question"]) if pd.notna(row["question"]) else ""
        note = str(row["note"]) if pd.notna(row["note"]) else ""

        score_q = fuzz.partial_ratio(msg, question)
        score_n = fuzz.partial_ratio(msg, note)
        total_score = max(score_q, score_n)

        if total_score > best_score:
            best_score = total_score
            best_match = row

    if best_match is not None and best_score >= 60:
        return best_match["answer"]
    else:
        return ask_chatgpt(f"ユーザーからの質問: {msg}")
