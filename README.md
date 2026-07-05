# AI-News

> AI 资讯智能聚合与推送系统 —— 自动采集、LLM 分析、飞书推送、持久存储

## 📖 文档

- [需求文档](./docs/需求文档.md) — 项目背景、功能清单、架构设计
- [开发指导](./docs/开发指导.md) — 分 Step 执行的落地指南
- [开发进度](./docs/开发进度.md) — **当前迭代状态与任务看板**
- [Cursor Superpowers](./.cursor/rules/superpowers.mdc) — Agent 工作流与 `/plugin-add superpowers` 安装说明（可选）

## 🎯 项目目标

- **及时性**：核心信息延迟 ≤ 1 小时
- **精准性**：LLM 打分，每天 TOP 10
- **可读性**：中文摘要、标签、重要性评级
- **可追溯**：全文检索 + 语义搜索
- **低运维**：一键部署，自动运行

## 🚀 快速开始（Docker Compose）

### 1. 环境变量配置

在项目根目录复制模板并编辑：

```bash
cp .env.example .env
```

`.env` 已加入 `.gitignore`，请勿提交到 Git。完整变量说明见 [`.env.example`](./.env.example)，下表按类别列出常用项：

| 类别 | 变量 | 说明 | 是否必填 |
|------|------|------|----------|
| 应用 | `APP_ENV` | 运行环境：`dev` / `prod` | 否（默认 `dev`） |
| 应用 | `APP_PORT` | 后端宿主机映射端口；容器内固定 `8000` | 否（未设置时默认 `8000`） |
| 应用 | `LOG_LEVEL` | 日志级别：`DEBUG` / `INFO` / `WARNING` / `ERROR` | 否 |
| 应用 | `TIMEZONE` | 时区，如 `Asia/Shanghai` | 否 |
| 数据库 | `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | PostgreSQL 账号、密码、库名 | 否（有默认值） |
| 数据库 | `DATABASE_URL` | 连接串；**密码须与 `POSTGRES_PASSWORD` 一致** | 是 |
| Redis | `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Redis 与 Celery 连接 | 否（Compose 内默认指向 `redis` 服务） |
| LLM | `LLM_PROVIDER` / `LLM_MODEL` | 模型提供商与模型名（litellm） | 是 |
| LLM | `OPENAI_API_KEY` | OpenAI（或兼容 API）密钥 | **是**（采集分析、Embedding） |
| LLM | `OPENAI_BASE_URL` | 可选代理或 Ollama 地址 | 否 |
| Embedding | `EMBEDDING_MODEL` / `EMBEDDING_DIM` | 向量模型与维度 | 否 |
| 认证 | `ADMIN_PASSWORD` / `JWT_SECRET` / `AUTH_ENABLED` | Dashboard 登录与 JWT | 生产环境必改 |
| 飞书 | `FEISHU_WEBHOOK` | 飞书机器人 Webhook | **是**（需推送时） |
| 飞书 | `FEISHU_SECRET` | 机器人签名密钥 | 否（推荐） |
| 推送 | `COLLECT_CRON` / `DAILY_DIGEST_CRON` 等 | 采集与推送 Cron 表达式 | 否 |
| 偏好 | `USER_INTERESTS` | 兴趣标签权重，如 `LLM=1.0,Agent=0.9` | 否 |

**最小可运行配置**（启动后 API 可访问；采集/推送需补全密钥）：

```bash
OPENAI_API_KEY=sk-your-openai-key-here
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-id
# 若修改了 POSTGRES_PASSWORD，须同步修改 DATABASE_URL 中的密码
```

> **端口提示**：`.env.example` 中 `APP_PORT=8001` 仅为示例（宿主机 8000 被占用时使用）。未设置 `APP_PORT` 时，`docker-compose.yml` 默认映射 **8000:8000**。下文验证命令中的 `<APP_PORT>` 请替换为你 `.env` 中的实际值。

### 2. 启动命令

在项目根目录执行：

```bash
# 首次或 Dockerfile 变更后：构建并后台启动全部服务
docker compose up -d --build

# 日常启动（镜像已存在）
docker compose up -d

# 查看容器状态
docker compose ps

# 查看日志（全部 / 单个服务）
docker compose logs -f
docker compose logs -f backend

# 停止服务（保留数据卷）
docker compose down

# 停止并删除数据卷（会清空数据库）
docker compose down -v

# 仅启动数据库与 Redis（本地非 Docker 跑后端时使用）
docker compose up -d postgres redis
```

首次启动会构建 `backend` / `worker` / `beat` 镜像；`frontend` 容器内会执行 `npm install && npm run dev`，首次可能较慢。

### 3. 容器与端口

| Compose 服务 | 容器名 | 宿主机端口 | 容器内端口 | 说明 |
|--------------|--------|------------|------------|------|
| `postgres` | `ai-news-postgres` | **5432** | 5432 | PostgreSQL 16 + pgvector |
| `redis` | `ai-news-redis` | **6379** | 6379 | Redis 7 |
| `backend` | `ai-news-backend` | **`${APP_PORT:-8000}`** | 8000 | FastAPI（Uvicorn，`--reload`） |
| `worker` | `ai-news-worker` | — | — | Celery Worker（异步任务） |
| `beat` | `ai-news-beat` | — | — | Celery Beat（定时任务） |
| `frontend` | `ai-news-frontend` | **3000** | 3000 | Next.js 开发服务器 |

无对外端口的 `worker`、`beat` 通过 Docker 内网连接 `postgres` 与 `redis`。

**访问地址**（假设 `APP_PORT=8000`）：

- 后端健康检查 / API：`http://localhost:8000`
- Swagger 文档：`http://localhost:8000/docs`
- 前端 Dashboard：`http://localhost:3000`

### 4. 验证方法

**① 容器是否正常运行**

```bash
docker compose ps
```

期望：`postgres`、`redis`、`backend`、`worker`、`beat`、`frontend` 状态为 `running`；`postgres` / `redis` 健康检查为 `healthy` 后 `backend` 才会启动。

**② 后端健康检查**

```bash
curl http://localhost:<APP_PORT>/health
```

期望响应示例：

```json
{"status":"ok","version":"0.1.0", ...}
```

**③ API 文档（浏览器）**

```bash
# macOS
open http://localhost:<APP_PORT>/docs

# Linux（有 xdg-open 时）
xdg-open http://localhost:<APP_PORT>/docs
```

**④ 前端页面**

浏览器打开 `http://localhost:3000`；若白屏或报错，查看：

```bash
docker compose logs -f frontend
```

**⑤ 数据库与 Redis（可选）**

```bash
# PostgreSQL
docker exec ai-news-postgres pg_isready -U ainews -d ainews

# Redis
docker exec ai-news-redis redis-cli ping
# 期望：PONG
```

**⑥ 任务队列（可选）**

```bash
docker compose logs -f worker beat
```

日志中应能看到 Celery worker / beat 正常启动，无持续报错。

### 常见问题

- **缺少 `.env`**：`backend` / `worker` / `beat` 依赖 `env_file: .env`，须先执行 `cp .env.example .env`。
- **端口冲突**：本机已占用 5432、6379、8000、3000 时，修改 `.env` 中 `APP_PORT` 或在 `docker-compose.yml` 中调整 `ports` 映射。
- **健康检查失败**：先 `docker compose logs postgres redis backend` 排查数据库密码是否与 `DATABASE_URL` 一致。

## 🗂 项目结构

```
ai-news/
├── backend/               后端 Python 代码
│   ├── app/
│   │   ├── main.py        FastAPI 入口
│   │   ├── config.py      配置加载
│   │   ├── db/            ORM 与 Session
│   │   ├── collectors/    采集器（Step 1+）
│   │   ├── analyzers/     LLM 分析（Step 1+）
│   │   ├── notifiers/     推送通道（Step 1+）
│   │   ├── scheduler/     Celery 任务
│   │   ├── api/           REST 路由
│   │   └── utils/
│   └── tests/
├── frontend/              Next.js Dashboard（Step 2+）
├── scripts/               一次性脚本（迁移、种子、导出）
├── ops/                   部署相关（Dockerfile、Grafana）
├── docs/                  项目文档
└── docker-compose.yml
```

## 🛠 技术栈

| 层 | 选型 |
|----|------|
| 后端 | Python 3.11 + FastAPI + SQLAlchemy 2 |
| 任务队列 | Celery + Redis |
| 数据库 | PostgreSQL 16 + pgvector |
| LLM | litellm（OpenAI / Anthropic / DeepSeek / Ollama） |
| 前端 | Next.js + TailwindCSS + shadcn/ui（Step 2） |
| 部署 | Docker Compose |

## 🧪 本地开发（不用 Docker）

```bash
# 创建虚拟环境
python3.11 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e ".[dev]"

# 启动依赖服务（仅 DB 和 Redis）
docker compose up -d postgres redis

# 启动后端
cd backend
PYTHONPATH=. uvicorn app.main:app --reload

# 启动 worker（另一个终端）
cd backend
PYTHONPATH=. celery -A app.scheduler.celery_app worker --loglevel=INFO

# 跑测试
pytest backend/tests
```

## ✅ 代码质量

```bash
# Lint + 格式化
ruff check --fix .
ruff format .

# 类型检查
mypy backend/app

# 提交前 hook
pre-commit install
```

## 📅 迭代进度

当前阶段：**Step 0 - 项目骨架** ✅

详见 [开发进度](./docs/开发进度.md)。

## 📝 License

MIT
