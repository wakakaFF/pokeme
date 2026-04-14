# PokeMe 项目上下文

## 项目简介
AI 驱动的动物图鉴 Web App，模仿宝可梦图鉴风格。
用摄像头扫描动物 → AI 识别 → 生成图鉴卡片 + 语音播报 → 存入收藏数据库。

---

## 当前功能（已完成）

- [x] 摄像头扫描 + 本地图片上传识别
- [x] 图鉴卡片（稀有度、属性、打字机动画）
- [x] 图鉴收藏页（网格、分类筛选、点开详情卡片）
- [x] AI 聊天助手"图图"（流式输出、Markdown 渲染）
- [x] 麦克风语音输入（Web Speech API）
- [x] 语音播报（MiniMax TTS + Web Audio 电子音效）
- [x] 动物名 / 学名小喇叭朗读（教小朋友发音）
- [x] TTS 本地缓存 + 识别后自动预生成（零等待）
- [x] 相同图片 MD5 去重，不重复调用 AI

---

## 技术栈

### 后端
- Python 3.10+，FastAPI，SQLite (aiosqlite)，Pillow，httpx
- 启动：`cd backend && python main.py`（端口 8000）

### 前端
- 原生 HTML + CSS + JS，无框架
- marked.js（Markdown 渲染）
- Web Speech API（语音输入）
- Web Audio API（TTS 音效处理）

---

## AI 模型分工

| 功能 | 模型 | env 变量 |
|------|------|----------|
| 动物识别（视觉） | claude-opus-4-6 via oneapi.hk | `VISION_*` |
| AI 聊天 | MiniMax-M2.7 | `CHAT_*` |
| TTS 语音合成 | MiniMax speech-2.8-hd | `CHAT_*` |
| 学名朗读 | 浏览器 speechSynthesis (en-US) | 无需配置 |

---

## 环境变量（.env）

```env
# 聊天模型 + TTS
CHAT_BASE_URL=https://api.minimaxi.com/v1
CHAT_API_KEY=...
CHAT_MODEL=MiniMax-M2.7

# 视觉识别
VISION_BASE_URL=https://oneapi.hk/v1
VISION_API_KEY=...
VISION_MODEL=claude-opus-4-6
```

---

## 文件结构

```
F:/fun/pokeme/
├── CLAUDE.md
├── README.md
├── .env
├── backend/
│   ├── main.py            # FastAPI，所有路由
│   ├── database.py        # SQLite CRUD
│   ├── claude_service.py  # AI 调用（识别+聊天，含 think 块过滤）
│   ├── photos/            # 识别照片存储
│   └── tts_cache/         # TTS 音频本地缓存（MD5 命名）
└── frontend/
    ├── index.html          # 扫描页
    ├── collection.html     # 图鉴收藏页
    ├── chat.html           # AI 聊天页
    ├── css/style.css
    └── js/
        ├── camera.js       # 摄像头
        ├── scanner.js      # 扫描 + 卡片渲染
        ├── collection.js   # 图鉴页
        ├── chat.js         # SSE 流式聊天
        └── narration.js    # TTS 播报 + Web Audio 效果
```

---

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/identify` | 上传图片识别 |
| GET  | `/api/collection` | 图鉴列表（category/limit/offset） |
| GET  | `/api/collection/{id}` | 单条详情 |
| POST | `/api/chat` | 聊天（SSE 流式） |
| POST | `/api/tts` | 文字转语音（本地缓存） |
| GET  | `/api/stats` | 统计 |

---

## 数据库关键字段

`narration`：语音播报词，识别时由 AI 生成，80 字口语化，以"发现了一只XX！"开头。
`image_hash`：MD5 去重，相同图片直接返回缓存。
`photo_url`：由 `_row_to_dict()` 从 `photo_path` 转换，格式为 `/static/photos/{hash}.jpg`。

---

## 已知问题 / 踩坑记录

- MiniMax-M2.7 **不支持 base64 图片输入**，识别必须用支持视觉的 Claude 模型
- MiniMax TTS 套餐限制：`speech-01-turbo` / `speech-01` 不支持，用 `speech-2.8-hd`
- `get_collection()` 返回需调用 `_row_to_dict()` 才有 `photo_url`，否则图片显示为空
- MiniMax-M2.7 输出含 `<think>...</think>` 块，`claude_service.py` 中有流式过滤逻辑
- `makeSpeakBtn` 等工具函数须定义在全局作用域，不能放在 `DOMContentLoaded` 内部（否则 `showDetail` 等全局函数调用不到）
- edge-tts 在国内被墙（`speech.platform.bing.com` 不通），改用 MiniMax TTS

---

## 硬件计划（未来）

目标：拍立得形状实体设备，成本 ¥200 以内。
主控：ESP32-S3（TTGO T-Camera S3），小屏幕显示图鉴卡，WiFi 上传到云端 API。
