from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chat import get_answer_from_faq_or_chatgpt
from dotenv import load_dotenv
import os

# 環境変数読み込み
load_dotenv()

# FastAPIアプリケーションの初期化
app = FastAPI()

# CORS設定（必要に応じてドメイン制限も可能）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # フロントエンドと連携するドメインに限定するのが理想
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストボディ用のデータモデル
class ChatRequest(BaseModel):
    msg: str

# ルート確認用
@app.get("/")
async def root():
    return {"message": "FAQ Chatbot API is running."}

# チャット用のエンドポイント
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_msg = request.msg
    answer = get_answer_from_faq_or_chatgpt(user_msg)
    return {"response": answer}
