from fastapi import FastAPI, Form, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.staticfiles import StaticFiles
import os
import shutil
from dotenv import load_dotenv
from app.chatBot import GPTBasedChatBot
from app.searcher import CosineNearestNeighborsFinder
from app.embedder import OpenAIEmbedder, get_embedding, save_embeddings

load_dotenv()
app = FastAPI()
# テンプレート・静的ファイルのディレクトリ設定
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
# エンベディング設定
UPLOAD_DIR = "embeddings"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# トップページの表示
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ファイルアップロード処理
@app.post("/upload_file/")
async def upload_file(file: UploadFile = File(...)):
    # ファイル名から拡張子を取り除き、ベース名を取得
    base_filename = os.path.splitext(file.filename)[0]
    # アップロードファイルの保存先パス
    upload_path = os.path.join(UPLOAD_DIR, f"{base_filename}.txt")
    # アップロードされたファイルを保存
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # 埋め込み情報を保存するファイル名を設定
    embedding_filename = f"{base_filename}.json"
    embedding_path = os.path.join(UPLOAD_DIR, embedding_filename)
    # 1行ずつテキストを読み込み
    with open(upload_path, "r", encoding="utf-8") as f:
        texts = f.readlines()
    # 埋め込み情報を生成して保存
    api_key = os.getenv("OPENAI_API_KEY")
    response = save_embeddings(texts, embedding_path, api_key)
    # レスポンス返却
    return {"response": response, "embedding_filename": embedding_filename}

# チャット処理
@app.post("/chat/")
async def chat(user_query: str = Form(...), embedding_files: list = Form(None)):
    combined_texts = []
    if embedding_files:
        # 埋め込みファイルが選択されている場合
        for file in embedding_files:
            embedding_path = os.path.join(UPLOAD_DIR, file)
            searcher = CosineNearestNeighborsFinder(embedding_path)
            embedder = OpenAIEmbedder(api_key=os.getenv("OPENAI_API_KEY"))
            user_query_vector = embedder.embed([user_query])[0]
            search_results = searcher.find_nearest(user_query_vector, topk=3)
            combined_texts.extend([result["text"] for result in search_results])

        chat_bot = GPTBasedChatBot()
        response = chat_bot.generate_response(user_query, combined_texts)
    else:
        # 埋め込みファイルが選択されていない場合
        chat_bot = GPTBasedChatBot()
        response = chat_bot.generate_response(user_query, [])
    # # タイムアウトテスト用
    # import time
    # time.sleep(10)
    # レスポンス返却
    return {
        "user_query": user_query,
        "response": response,
        "embedding_files": embedding_files,
        "combined_texts": combined_texts
    }

# 埋め込みファイル一覧取得
@app.get("/embedding_files/")
async def get_embedding_files():
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".json")]
    return {"files": files}
