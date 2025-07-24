# faq-chatbot-backend

## 実行方法

1. 必要パッケージをインストール:

```
pip install fastapi uvicorn pandas
```

2. CSVファイル（FAQ検索データ.csv）をこのフォルダに置く

3. サーバーを起動:

```
uvicorn main:app --reload --port 8000
```

4. フロントエンドから http://localhost:8000/ask にアクセスされます