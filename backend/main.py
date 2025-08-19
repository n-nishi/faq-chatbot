from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chat import get_answer_from_faq_or_chatgpt, get_all_categories

# FastAPIアプリ
app = FastAPI()

# CORS設定（必要に応じて適宜変更）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://faq-chatbot-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストモデル
class QuestionRequest(BaseModel):
    message: str
    category: str

# ルート確認用
@app.get("/")
def read_root():
    return {"message": "FAQチャットボットのバックエンドが起動中です"}

# カテゴリ一覧を取得
@app.get("/categories")
async def categories():
    try:
        return {"categories": get_all_categories()}
    except Exception as e:
        print(f"カテゴリ取得エラー: {e}")
        raise HTTPException(status_code=500, detail="カテゴリ取得に失敗しました")

# チャットエンドポイント
@app.post("/ask")
async def ask(req: QuestionRequest):
    try:
        response = get_answer_from_faq_or_chatgpt(req.message, req.category)
        return {"answer": response}
    except Exception as e:
        print(f"質問処理エラー: {e}")
        raise HTTPException(status_code=500, detail="質問処理中にエラーが発生しました")
