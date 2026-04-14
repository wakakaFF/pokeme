# 技术方案文档

**项目名称**：PokeMe — 动物图鉴  
**版本**：v1.0  
**日期**：2026-04-13  

---

## 一、技术栈

```
前端
├── 原生 HTML5 + CSS3 + JavaScript
├── 摄像头：MediaDevices API (getUserMedia)
└── 无需前端框架

后端
├── Python 3.10+
├── FastAPI
├── SQLite + aiosqlite
└── Pillow（图片压缩处理）

AI 服务
└── Anthropic Claude API（claude-opus-4-6，Vision）

部署
└── Railway（一键部署，自动 HTTPS）
```

---

## 二、项目结构

```
F:/fun/pokeme/
├── README.md
├── requirements.txt
├── .env.example
├── .env
│
├── backend/
│   ├── main.py             # FastAPI 入口 + 静态文件服务
│   ├── database.py         # SQLite 操作
│   ├── claude_service.py   # Claude API 封装
│   ├── models.py           # Pydantic 数据模型
│   └── photos/             # 扫描照片存储目录
│
├── frontend/
│   ├── index.html          # 扫描主页
│   ├── collection.html     # 图鉴收藏页
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── camera.js       # 摄像头控制
│       ├── scanner.js      # 扫描逻辑 + 结果渲染
│       └── collection.js   # 收藏页逻辑
│
└── docs/
```

---

## 三、系统架构

```
┌─────────────────────────────────────────┐
│              浏览器（前端）               │
│  摄像头预览 → 拍照 → 上传图片            │
│                    ↓                     │
│  图鉴卡片动画  ←  接收结果               │
└──────────────────┬──────────────────────┘
                   │ POST /api/identify
                   ↓
┌─────────────────────────────────────────┐
│              FastAPI（后端）              │
│                                          │
│  1. 接收图片                             │
│  2. 压缩图片（≤800px）                   │
│  3. 计算 MD5 hash                        │
│  4. 查询 SQLite 缓存                     │
│     ├─ 命中 → 直接返回                   │
│     └─ 未命中 → 调用 Claude Vision       │
│  5. 解析 JSON 结果                       │
│  6. 存储照片 + 写入数据库                │
│  7. 返回图鉴数据                         │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        ↓                     ↓
   SQLite DB            Claude API
```

---

## 四、Claude Prompt 设计

### System Prompt

```
你是「动物图鉴」AI 系统，专门识别动物并生成图鉴条目。

规则：
1. 如果图片中没有动物，返回：{"error": "no_animal"}
2. 如果有动物，返回以下 JSON（不含其他任何文字）：
{
  "number": "随机4位数字字符串，如0847",
  "name": "动物中文名（精确到品种，如可以的话）",
  "scientific_name": "拉丁学名",
  "category": "动物类别（哺乳动物/鸟类/爬行动物/两栖动物/鱼类/昆虫/其他）",
  "height": "估算体型高度或体长",
  "weight": "估算体重",
  "habitat": "自然栖息地",
  "diet": "食性描述",
  "predator": "主要天敌",
  "conservation": "IUCN保护状态，如 无危(LC)/近危(NT)/易危(VU)/濒危(EN)/极危(CR)",
  "description": "50字以内的图鉴风格描述，有趣略带拟人，适合儿童阅读",
  "rarity": "根据常见程度判断：普通/稀有/极稀有/传说",
  "attributes": ["属性1", "属性2"]  // 2-3个，如毛茸茸、夜行、独行、群居等
}
```

### 稀有度判定逻辑

```
传说   → 极危(CR)物种 或 野外灭绝物种
极稀有 → 濒危(EN)/易危(VU)物种
稀有   → 近危(NT) 或 不常见野生动物
普通   → 无危(LC) 且 日常常见
```

---

## 五、核心流程

### 5.1 图片处理

```python
# 前端：压缩后上传
canvas.toBlob(blob => {
    // 限制最大边长 800px，减少传输和 API 费用
}, 'image/jpeg', 0.85)

# 后端：再次确认尺寸
from PIL import Image
img.thumbnail((800, 800))
```

### 5.2 缓存策略

```python
# 相同图片（MD5相同）直接返回数据库结果
hash = md5(image_bytes)
cached = await db.get_by_hash(hash)
if cached:
    return {"is_new": False, "entry": cached}
```

### 5.3 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| 图片中无动物 | 返回友好提示，不写入数据库 |
| Claude API 超时 | 返回错误提示，前端引导重试 |
| 图片格式不支持 | 前端限制上传格式 |
| API Key 无效 | 启动时检测，给出配置提示 |

---

## 六、性能指标

| 场景 | 预期耗时 |
|------|---------|
| 首次识别（调用 Claude） | 3-5 秒 |
| 重复识别（读缓存） | < 100ms |
| 图鉴列表加载 | < 200ms |
