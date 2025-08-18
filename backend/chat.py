import os
import pandas as pd
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from openai import OpenAI
from typing import Optional

# 環境変数の読み込み
load_dotenv()

# OpenAIクライアント初期化
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# FAQデータの読み込み（必要に応じてパス修正）
faq_data = pd.read_csv("FAQ検索データ.csv")


def search_faq(user_input: str) -> dict:
    """
    FAQの中からユーザーの質問に最も近いものを検索する
    """
    best_score = 0
    best_match = None

    for _, row in faq_data.iterrows():
        question = str(row["question"])
        score = fuzz.token_sort_ratio(user_input, question)  # 語順の違いに強い比較

        if score > best_score:
            best_score = score
            best_match = row

    return {"score": best_score, "answer": best_match["answer"] if best_match is not None else None}


def ask_chatgpt(msg: str) -> str:
    """
    OpenAI ChatGPT に質問を投げる
    """
    prompt = f"""
あなたはFAQ対応専用のAIです。
曖昧な質問に対しても、過去のFAQを想定しながら、分かりやすく簡潔に日本語で答えてください。

【質問】
{msg}

※回答が不明な場合は「申し訳ありませんが、その件については分かりません」と返答してください。
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたはFAQ対応に特化したアシスタントです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"ChatGPTとの通信中にエラーが発生しました: {e}"


def get_answer_from_faq_or_chatgpt(user_input: str) -> str:
    """
    FAQから回答を取得し、信頼度が低ければChatGPTに委ねる
    """
    result = search_faq(user_input)
    score = result["score"]
    answer = result["answer"]

    if score >= 75:
        return f"【FAQより回答】\n{answer}"
    else:
        return f"【ChatGPTによる推測回答】\n{ask_chatgpt(user_input)}"
