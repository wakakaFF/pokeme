import asyncio
import hashlib
import io
import os
import uuid

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from contextlib import asynccontextmanager
import database
import claude_service

@asynccontextmanager
async def lifespan(app):
    await database.init_db()
    yield

app = FastAPI(title="PokeMe 动物图鉴", lifespan=lifespan)

# 照片存储目录
PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static/photos", StaticFiles(directory=PHOTOS_DIR), name="photos")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ── 前端页面路由 ──────────────────────────────────────────────

@app.get("/")
async def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/collection")
async def collection_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "collection.html"))


@app.get("/chat")
async def chat_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "chat.html"))


# ── API ──────────────────────────────────────────────────────

@app.post("/api/identify")
async def identify(file: UploadFile = File(...)):
    # 读取并压缩图片
    image_bytes = await file.read()
    image_bytes, media_type = _compress_image(image_bytes)

    # 计算 hash，检查缓存
    image_hash = hashlib.md5(image_bytes).hexdigest()
    cached = await database.get_by_hash(image_hash)
    if cached:
        return JSONResponse({"is_new": False, "entry": cached})

    # 调用 Claude 识别
    try:
        result, raw_json = await claude_service.identify_animal(image_bytes, media_type)
        print(result)
        print(raw_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别失败：{str(e)}")

    # 无动物
    if result.get("error") == "no_animal":
        return JSONResponse({"is_animal": False, "message": "未发现动物，请对准动物重新扫描"})

    # 保存照片
    photo_filename = f"{image_hash}.jpg"
    photo_path = os.path.join(PHOTOS_DIR, photo_filename)
    with open(photo_path, "wb") as f:
        f.write(image_bytes)

    # 写入数据库
    entry = await database.insert_entry(image_hash, photo_path, result, raw_json)

    # 后台预生成 TTS 缓存（不阻塞响应）
    asyncio.create_task(_prefetch_tts([
        result.get("name"),
        result.get("narration") or result.get("description"),
    ]))

    return JSONResponse({"is_new": True, "entry": entry})


@app.get("/api/collection")
async def get_collection(category: str = None, limit: int = 50, offset: int = 0):
    total, entries = await database.get_collection(category, limit, offset)
    return JSONResponse({"total": total, "entries": entries})


@app.get("/api/collection/{entry_id}")
async def get_entry(entry_id: int):
    entry = await database.get_entry_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="未找到该条目")
    return JSONResponse(entry)


class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

@app.post("/api/chat")
async def chat(req: ChatRequest):
    import json as _json
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    async def generate():
        try:
            async for text in claude_service.chat_stream(messages):
                yield f"data: {_json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {_json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


TTS_CACHE_DIR = os.path.join(os.path.dirname(__file__), "tts_cache")
os.makedirs(TTS_CACHE_DIR, exist_ok=True)


async def _prefetch_tts(texts: list[str]):
    """后台预生成 TTS 缓存，识别成功后静默调用。"""
    import httpx
    api_key = os.environ.get("CHAT_API_KEY")
    base_url = os.environ.get("CHAT_BASE_URL", "https://api.minimaxi.com/v1").rstrip("/")

    for text in texts:
        if not text:
            continue
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_path = os.path.join(TTS_CACHE_DIR, f"{text_hash}.mp3")
        if os.path.exists(cache_path):
            continue  # 已有缓存，跳过
        try:
            payload = {
                "model": "speech-2.8-hd",
                "text": text,
                "stream": False,
                "voice_setting": {"voice_id": "female-shaonv", "speed": 1.0, "vol": 1.0, "pitch": 0},
                "audio_setting": {"format": "mp3", "sample_rate": 32000},
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{base_url}/t2a_v2",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                data = resp.json()
            audio_hex = data.get("data", {}).get("audio", "")
            if audio_hex:
                with open(cache_path, "wb") as f:
                    f.write(bytes.fromhex(audio_hex))
                print(f"[TTS prefetch] cached: {text[:20]}...")
        except Exception as e:
            print(f"[TTS prefetch] failed for '{text[:20]}': {e}")

class TTSRequest(BaseModel):
    text: str

@app.post("/api/tts")
async def tts(req: TTSRequest):
    import httpx, hashlib, io as _io

    # 用文本 hash 作为缓存文件名，相同文字直接返回缓存
    text_hash = hashlib.md5(req.text.encode()).hexdigest()
    cache_path = os.path.join(TTS_CACHE_DIR, f"{text_hash}.mp3")

    if os.path.exists(cache_path):
        return FileResponse(cache_path, media_type="audio/mpeg")

    # 缓存不存在，调用 MiniMax TTS API
    api_key = os.environ.get("CHAT_API_KEY")
    base_url = os.environ.get("CHAT_BASE_URL", "https://api.minimaxi.com/v1").rstrip("/")

    payload = {
        "model": "speech-2.8-hd",
        "text": req.text,
        "stream": False,
        "voice_setting": {
            "voice_id": "female-shaonv",
            "speed": 1.0,
            "vol": 1.0,
            "pitch": 0,
        },
        "audio_setting": {
            "format": "mp3",
            "sample_rate": 32000,
        }
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{base_url}/t2a_v2",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    audio_hex = data.get("data", {}).get("audio", "")
    if not audio_hex:
        raise HTTPException(status_code=500, detail=f"TTS 返回为空: {data}")
    audio_bytes = bytes.fromhex(audio_hex)

    # 写入缓存
    with open(cache_path, "wb") as f:
        f.write(audio_bytes)

    return FileResponse(cache_path, media_type="audio/mpeg")


@app.get("/api/stats")
async def get_stats():
    stats = await database.get_stats()
    return JSONResponse(stats)


# ── 工具函数 ─────────────────────────────────────────────────

def _compress_image(image_bytes: bytes) -> tuple[bytes, str]:
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGB")
    img.thumbnail((320, 320))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=60)
    return buf.getvalue(), "image/jpeg"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
