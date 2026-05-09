# 合同归档系统

内部使用的合同 PDF 批量解析归档系统。流程：上传 PDF → MinerU OCR → 本地大模型抽取字段 → Web 表格审阅 → 导出 Excel。

## 启动

```bash
cp .env.example .env
# 按需修改 MINERU_API_URL / OLLAMA_URL / LLM_MODEL
docker compose up -d --build
```

访问 http://localhost:3000

## 组件

- 前端：Next.js（端口 3000）
- 后端 API：FastAPI（端口 8000）
- 任务队列：Celery + Redis
- 数据库：PostgreSQL（端口 5432）
- 外部依赖：MinerU API、Ollama API

## 字段定义

在 `backend/app/config_files/fields.yaml` 调整。修改后需同步更新 `frontend/app/batches/[id]/review/page.tsx` 的 FIELDS 数组。
