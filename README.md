# PokeMe 动物图鉴

用手机扫描身边的动物，生成专属图鉴卡片，配合语音播报和 AI 问答，适合亲子互动与自然科普。

---

## 功能概览

### 扫描识别
- 打开摄像头对准动物，点击快门按钮拍照识别
- 支持上传本地图片作为备用
- 相同图片自动命中缓存，不重复调用 AI
- 识别结果包含：中文名、学名、类别、体型、体重、栖息地、食性、天敌、保护状态、稀有度、属性标签

### 图鉴卡片
- 识别成功后弹出宝可梦风格底部滑入卡片
- 稀有度分四级：普通 / 稀有 / 极稀有 / 传说，边框颜色和光效随稀有度变化
- 首次发现显示"✨ 新动物发现！"金色横幅
- 描述文字打字机动画逐字显示

### 语音功能
- **名称朗读**：动物中文名旁有小喇叭，点击用 MiniMax TTS 朗读
- **学名朗读**：拉丁学名旁有小喇叭，点击用浏览器英语语音朗读（发音更准确）
- **图鉴播报**：卡片右上角大喇叭，播报专属介绍词（以"发现了一只XX！"开头）
- 播报音频经带通滤波 + 轻微失真处理，模拟图鉴小喇叭电子感
- **TTS 缓存**：音频生成后缓存到本地，同一文字只调一次 API
- **预生成**：识别成功后自动后台预生成音频，点喇叭时零等待

### 图鉴收藏页
- 展示所有已发现动物，网格排列
- 按类别筛选：哺乳动物 / 鸟类 / 昆虫 / 爬行动物 / 鱼类 / 两栖动物 / 其他
- 点击卡片弹出完整详情，与扫描页卡片一致

### AI 聊天
- 内置 AI 助手"图图"🦉，可问任何动物相关问题
- 流式输出，回复自动渲染 Markdown 格式
- 支持麦克风语音输入，说完自动发送

---

## 技术架构

```
pokeme/
├── backend/
│   ├── main.py           # FastAPI 服务，所有 API 路由
│   ├── database.py       # SQLite 数据库操作
│   ├── claude_service.py # AI 调用（识别 + 聊天）
│   ├── photos/           # 识别照片存储
│   └── tts_cache/        # TTS 音频本地缓存
├── frontend/
│   ├── index.html        # 扫描页
│   ├── collection.html   # 图鉴收藏页
│   ├── chat.html         # AI 聊天页
│   ├── css/style.css     # 全局样式
│   └── js/
│       ├── camera.js     # 摄像头控制
│       ├── scanner.js    # 扫描逻辑 + 卡片渲染
│       ├── collection.js # 图鉴页逻辑
│       ├── chat.js       # 聊天逻辑（SSE 流式）
│       └── narration.js  # 语音播报（TTS + Web Audio 效果）
└── .env                  # API 密钥配置
```

### AI 模型分工

| 功能 | 模型 | 说明 |
|------|------|------|
| 动物识别 | Claude（via oneapi.hk） | 支持图片输入，识别准确 |
| AI 聊天 | MiniMax-M2.7 | 流式文本输出，中文对话 |
| 语音合成 | MiniMax speech-2.8-hd | 中文 TTS，音色自然 |
| 学名朗读 | 浏览器 speechSynthesis | 英语语音，拉丁发音准确 |

### API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/identify` | 上传图片识别动物 |
| GET  | `/api/collection` | 获取图鉴列表（支持分类筛选和分页） |
| GET  | `/api/collection/{id}` | 获取单条图鉴详情 |
| POST | `/api/chat` | AI 聊天（SSE 流式响应） |
| POST | `/api/tts` | 文字转语音（带本地缓存） |
| GET  | `/api/stats` | 统计数据（总数、按稀有度、按类别） |

### 数据库字段（SQLite）

| 字段 | 说明 |
|------|------|
| `image_hash` | 图片 MD5，用于去重 |
| `photo_path` | 照片本地路径 |
| `number` | 图鉴编号（4位数字） |
| `name` | 动物中文名 |
| `scientific_name` | 拉丁学名 |
| `category` | 类别 |
| `height` / `weight` | 体型 / 体重 |
| `habitat` / `diet` / `predator` | 栖息地 / 食性 / 天敌 |
| `conservation` | IUCN 保护状态 |
| `description` | 图鉴描述（50字以内，儿童风格） |
| `rarity` | 稀有度（普通 / 稀有 / 极稀有 / 传说） |
| `attributes` | 属性标签（JSON 数组） |
| `narration` | 语音播报词（80字，口语化，以"发现了一只XX！"开头） |

---

## 部署

### 环境要求
- Python 3.10+
- 现代浏览器（Chrome / Edge，语音功能支持最好）

### 安装依赖

```bash
cd backend
pip install fastapi uvicorn aiosqlite python-dotenv pillow openai httpx
```

### 配置 `.env`

```env
# 聊天模型 + TTS（MiniMax）
CHAT_BASE_URL=https://api.minimaxi.com/v1
CHAT_API_KEY=你的MiniMax密钥
CHAT_MODEL=MiniMax-M2.7

# 视觉识别模型（支持图片输入的 Claude）
VISION_BASE_URL=https://oneapi.hk/v1
VISION_API_KEY=你的oneapi.hk密钥
VISION_MODEL=claude-opus-4-6
```

### 启动

```bash
cd backend
python main.py
```

访问 `http://localhost:8000`

---

## 注意事项

- 摄像头和麦克风：首次使用浏览器会弹出权限请求，需要允许
- 语音输入仅支持 Chrome / Edge（Firefox 不支持 Web Speech API）
- TTS 音频缓存在 `backend/tts_cache/`，可定期清理释放空间
- 已识别的图片以 MD5 去重，相同图片不会重复扣费
- MiniMax TTS 按字符计费，缓存机制确保每段文字只生成一次
