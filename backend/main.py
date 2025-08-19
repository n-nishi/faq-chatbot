from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chat import get_answer, get_all_categories

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://faq-chatbot-frontend.onrender.com"],  # 必要に応じて変更
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    message: str
    category: str

@app.get("/")
def read_root():
    return {"message": "FAQチャットボットのバックエンドが起動中です"}

@app.get("/categories")
async def get_categories():
    try:
        return {"categories": get_all_categories()}
    except Exception as e:
        print(f"カテゴリ取得エラー: {e}")
        raise HTTPException(status_code=500, detail="カテゴリ読み込みに失敗しました")

@app.post("/ask")
async def ask_question(req: QuestionRequest):
    try:
        return {"answer": get_answer(req.message.strip(), req.category.strip())}
    except Exception as e:
        print(f"検索エラー: {e}")
        raise HTTPException(status_code=500, detail="検索中にエラーが発生しました")
