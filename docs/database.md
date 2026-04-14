# 数据库设计

**数据库**：SQLite  
**文件路径**：`backend/pokeme.db`  
**版本**：v1.0  

---

## 表结构

### entries 表

```sql
CREATE TABLE entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    image_hash      TEXT UNIQUE NOT NULL,   -- MD5，用于去重缓存
    photo_path      TEXT,                   -- 照片相对路径
    number          TEXT,                   -- 图鉴编号，如 "0042"
    name            TEXT NOT NULL,          -- 动物中文名
    scientific_name TEXT,                   -- 拉丁学名
    category        TEXT,                   -- 动物类别
    height          TEXT,                   -- 估算体型
    weight          TEXT,                   -- 估算体重
    habitat         TEXT,                   -- 栖息地
    diet            TEXT,                   -- 食性
    predator        TEXT,                   -- 天敌
    conservation    TEXT,                   -- IUCN 保护状态
    description     TEXT,                   -- 图鉴描述
    rarity          TEXT DEFAULT '普通',    -- 普通/稀有/极稀有/传说
    attributes      TEXT,                   -- JSON 数组字符串
    raw_json        TEXT,                   -- Claude 原始返回（调试用）
    scanned_at      DATETIME DEFAULT (datetime('now', 'localtime'))
);

-- 索引
CREATE INDEX idx_category   ON entries(category);
CREATE INDEX idx_rarity     ON entries(rarity);
CREATE INDEX idx_scanned_at ON entries(scanned_at DESC);
```

---

## 字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| image_hash | TEXT | 图片 MD5，防重复调用 API | `"d41d8cd98f00b204..."` |
| photo_path | TEXT | 相对路径 | `"photos/abc123.jpg"` |
| number | TEXT | 4位编号，AI 生成 | `"0042"` |
| category | TEXT | AI 判断的动物类别 | `"哺乳动物"` |
| conservation | TEXT | IUCN 状态 | `"无危 (LC)"` |
| rarity | TEXT | 稀有度 | `"普通"` |
| attributes | TEXT | JSON 字符串 | `'["毛茸茸","夜行"]'` |
| raw_json | TEXT | Claude 完整返回，保留调试 | `'{"name":...}'` |

---

## 常用查询

```sql
-- 全部记录，时间倒序
SELECT * FROM entries ORDER BY scanned_at DESC;

-- 按动物类别筛选
SELECT * FROM entries WHERE category = '鸟类';

-- 按稀有度统计
SELECT rarity, COUNT(*) AS count
FROM entries
GROUP BY rarity;

-- 检查是否已扫描过（缓存判断）
SELECT id FROM entries WHERE image_hash = ?;

-- 各类别数量
SELECT category, COUNT(*) AS count
FROM entries
GROUP BY category
ORDER BY count DESC;
```

---

## 数据示例

```json
{
  "id": 1,
  "image_hash": "abc123...",
  "photo_path": "photos/abc123.jpg",
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
  "scanned_at": "2026-04-13T10:30:00"
}
```
