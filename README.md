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

## 🚀 快速开始（30 秒）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，至少填入 OPENAI_API_KEY 与 FEISHU_WEBHOOK

# 2. 启动服务
docker compose up -d

# 3. 验证
curl http://localhost:8000/health
# => {"status":"ok", "version":"0.1.0", ...}

# 4. 查看 API 文档
open http://localhost:8000/docs
```

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
