from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from fuzzywuzzy import fuzz
import openai
import os

from dotenv import load_dotenv
load_dotenv()

# OpenAIのAPIキーを環境変数から設定
openai.api_key = os.getenv("OPENAI_API_KEY")

# CSVファイルを読み込む
CSV_FILE = "FAQ検索データ.csv"

# FastAPI アプリ作成
app = FastAPI()

# CORS設定（フロントエンドからのアクセス許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://faq-chatbot-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエスト用のデータモデル
class QuestionRequest(BaseModel):
    message: str
    category: str

# ルート確認
@app.get("/")
def read_root():
    return {"message": "FAQチャットボットのバックエンドが起動中です"}

# カテゴリ一覧を返す
@app.get("/categories")
async def get_categories():
    """カテゴリ一覧を返す（複数カテゴリ対応）"""
    try:
        df = pd.read_csv(CSV_FILE, encoding="cp932")
        df = df[df["up_check"] == True]  # 有効な行だけ

        # 改行（\r\n, \n）で複数カテゴリを分割し、すべてをセット化
        category_series = df["カテゴリ"].dropna().apply(
            lambda x: [c.strip() for c in str(x).splitlines()]
        )
        all_categories = set(cat for sublist in category_series for cat in sublist)

        return {"categories": sorted(all_categories)}
    except Exception as e:
        print(f"カテゴリ取得エラー: {e}")
        raise HTTPException(status_code=500, detail="カテゴリ読み込みに失敗しました")

# ChatGPT に問い合わせる関数（補完用）
def ask_chatgpt(prompt: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # または gpt-3.5-turbo
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

# 質問を処理
@app.post("/ask")
async def ask_faq(req: QuestionRequest):
    try:
        df = pd.read_csv(CSV_FILE, encoding="cp932")
        df = df[df["up_check"] == True]  # 有効な行だけ

        msg = req.message.strip()
        selected_category = req.category.strip()

        if selected_category:
            # カテゴリが指定された場合のみフィルタ
            def match_category(cell):
                if pd.isna(cell):
                    return False
                categories = [c.strip() for c in str(cell).splitlines()]
                return selected_category in categories

            filtered_df = df[df["カテゴリ"].apply(match_category)]
        else:
            # カテゴリ未指定の場合はすべて対象
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
            return {"answer": best_match["answer"]}
        else:
            # OpenAIで補完回答
            gpt_reply = ask_chatgpt(f"ユーザーからの質問: {msg}")
            return {"answer": gpt_reply}

    except Exception as e:
        print(f"検索エラー: {e}")
        raise HTTPException(status_code=500, detail="検索中にエラーが発生しました")
