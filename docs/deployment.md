# 部署指南

**版本**：v1.0  

---

## 本地开发

### 1. 环境准备

```bash
# 确认 Python 版本（需要 3.10+）
python --version

# 进入项目目录
cd F:/fun/pokeme

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

```
ANTHROPIC_API_KEY=sk-ant-xxxxxx
```

### 3. 启动服务

```bash
python backend/main.py
```

浏览器打开 http://localhost:8000

---

## Railway 部署（上线）

> Railway 提供免费额度，自动配置 HTTPS，摄像头权限可正常使用。

### 1. 安装 Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### 2. 初始化并部署

```bash
cd F:/fun/pokeme
railway init
railway up
```

### 3. 配置环境变量

在 Railway 控制台 → Variables，添加：

```
ANTHROPIC_API_KEY=sk-ant-xxxxxx
```

### 4. 访问

部署完成后获得 `https://xxx.railway.app`，分享给手机直接访问。

---

## 注意事项

| 问题 | 说明 |
|------|------|
| 摄像头权限 | 必须 HTTPS，本地 localhost 除外 |
| SQLite 持久化 | Railway 重新部署会重置数据库，demo 阶段够用 |
| 照片存储 | 本地文件系统不持久，生产环境换对象存储 |
| API 费用 | 每次识别约 $0.01-0.02，$5 够充分测试 |
