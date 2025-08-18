from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os

from chat import get_categories_from_csv, get_answer_from_faq

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://faq-chatbot-frontend.onrender.com"],
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
def get_categories():
    try:
        return {"categories": get_categories_from_csv()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
def ask_faq(req: QuestionRequest):
    try:
        answer = get_answer_from_faq(req.message, req.category)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
