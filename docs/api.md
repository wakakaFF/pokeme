# API 文档

**Base URL**：`http://localhost:8000`  
**版本**：v1.0  

---

## POST /api/identify

识别图片中的动物，返回图鉴条目。

### 请求

```
Content-Type: multipart/form-data
file: 图片文件（jpg/png/webp，建议 ≤2MB）
```

### 响应 — 识别到动物（首次发现）

```json
{
  "is_new": true,
  "entry": {
    "id": 42,
    "number": "0042",
    "name": "橘猫",
    "scientific_name": "Felis catus",
    "category": "哺乳动物",
    "height": "0.3m",
    "weight": "4.5kg",
    "habitat": "人类居所、温带地区",
    "diet": "肉食性，以鱼类、小鼠为主",
    "predator": "大型犬科动物",
    "conservation": "无危 (LC)",
    "description": "慵懒的室内霸主。用橘色的毛发迷惑人类，实则掌控全局。",
    "rarity": "普通",
    "attributes": ["毛茸茸", "夜行", "独行"],
    "photo_url": "/static/photos/abc123.jpg",
    "scanned_at": "2026-04-13T10:30:00"
  }
}
```

### 响应 — 识别到动物（已发现过）

```json
{
  "is_new": false,
  "entry": { ...同上... }
}
```

### 响应 — 图片中无动物

```json
{
  "is_animal": false,
  "message": "未发现动物，请对准动物重新扫描"
}
```

### 响应 — 错误

```json
{
  "error": "识别失败，请重试"
}
```

---

## GET /api/collection

获取所有已发现的动物图鉴列表。

### 请求参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| category | string | 无 | 按类别筛选，如「哺乳动物」 |
| limit | int | 50 | 每页数量 |
| offset | int | 0 | 偏移量 |

### 响应

```json
{
  "total": 36,
  "entries": [
    {
      "id": 42,
      "number": "0042",
      "name": "橘猫",
      "category": "哺乳动物",
      "rarity": "普通",
      "photo_url": "/static/photos/abc123.jpg",
      "scanned_at": "2026-04-13T10:30:00"
    }
  ]
}
```

---

## GET /api/collection/{id}

获取单个图鉴条目完整信息。

### 响应

```json
{
  "id": 42,
  "number": "0042",
  "name": "橘猫",
  ...完整字段（同 identify 接口）...
}
```

---

## GET /api/stats

获取收集统计。

### 响应

```json
{
  "total": 36,
  "by_rarity": {
    "普通": 20,
    "稀有": 10,
    "极稀有": 5,
    "传说": 1
  },
  "by_category": {
    "哺乳动物": 15,
    "鸟类": 8,
    "昆虫": 7,
    "爬行动物": 4,
    "鱼类": 2
  },
  "latest_scanned_at": "2026-04-13T10:30:00"
}
```
