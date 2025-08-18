import os
import pandas as pd
import openai
import tiktoken
import time
import json
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# OpenAI APIキー（環境変数から取得）
openai.api_key = os.getenv("OPENAI_API_KEY")

# 読み込むCSVファイル名
CSV_FILE = "FAQ検索データ.csv"
OUTPUT_FILE = "faq_embeddings.json"

# OpenAIのモデル設定
EMBEDDING_MODEL = "text-embedding-3-small"

# トークン数カウントのためのエンコーダ
tokenizer = tiktoken.encoding_for_model(EMBEDDING_MODEL)

def get_embedding(text, model=EMBEDDING_MODEL):
    """OpenAI APIを使ってテキストのベクトルを取得"""
    try:
        response = openai.embeddings.create(
            input=[text],
            model=model
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding取得エラー: {e}")
        return None

def main():
    df = pd.read_csv(CSV_FILE, encoding="cp932")
    df = df[df["up_check"] == True].copy()

    embeddings = []

    for _, row in df.iterrows():
        question = str(row["question"]) if pd.notna(row["question"]) else ""
        note = str(row["note"]) if pd.notna(row["note"]) else ""
        text = f"Q: {question}\n補足: {note}"

        tokens = len(tokenizer.encode(text))
        if tokens > 8191:
            print(f"スキップ（トークン多すぎ）: {text[:30]}... ({tokens} tokens)")
            continue

        embedding = get_embedding(text)
        if embedding:
            embeddings.append({
                "text": text,
                "answer": row["answer"],
                "embedding": embedding
            })
            time.sleep(1.2)  # レート制限対策

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(embeddings, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(embeddings)} 件のembeddingを {OUTPUT_FILE} に保存しました")

if __name__ == "__main__":
    main()
