# EvalForge

**RAG 与 Agent 评测回归平台**

EvalForge 是面向 RAG 系统和 Agent 工作流的实验管理、自动评测、配置对比与持续回归平台。

## 核心闭环

    数据集版本
    + Prompt 版本
    + 模型版本
    + RAG 配置版本
    + Agent 工作流版本
            ↓
    批量运行
            ↓
    自动评测
            ↓
    A/B 对比
            ↓
    失败案例
            ↓
    回归门禁

## 当前进度

阶段 0 和阶段 1 已完成。

当前已实现：

- Python 3.12 与标准 `src` 工程结构
- FastAPI 应用工厂
- Pydantic Settings 类型安全配置
- JSON 结构化日志
- `X-Request-ID` 请求关联
- Liveness 与 Readiness 探针
- 应用生命周期管理
- 统一服务启动入口
- 多阶段 Docker 镜像
- 非 root 容器运行
- Docker Healthcheck
- pytest、Ruff 和 mypy 质量检查

当前验证结果：

    16 tests passed
    Ruff passed
    Format check passed
    mypy strict passed
    Docker container healthy

## 项目目标

- 文档上传、解析、切片和不可变版本
- PostgreSQL 与 pgvector
- Elasticsearch BM25
- RRF 混合召回与重排序
- 测试问题集与批量实验
- Recall@K、MRR 和 Hit Rate
- 回答正确性和引用一致性
- Agent 工具调用轨迹评测
- Prompt、模型、RAG 和工作流版本管理
- Baseline 与 Candidate 配对对比
- 延迟、Token 和成本统计
- Trace、请求快照和请求回放
- 失败案例库和回归测试集
- CI 质量门禁
- JSON、Markdown 和 HTML 评测报告

## 当前接口

- `GET /health`
- `GET /health/live`
- `GET /health/ready`
- `GET /docs`

## 本地运行

    conda activate evalforge-py312
    python -m pip install -e ".[dev]"
    cp .env.example .env
    python -m evalforge

## Docker 运行

    docker build -t evalforge-api:0.1.0 .
    docker run --rm --name evalforge-api -p 18100:8000 evalforge-api:0.1.0

## 质量检查

    python -m pytest
    python -m ruff check src tests
    python -m ruff format --check src tests
    python -m mypy src/evalforge

## 开发路线

- [x] 阶段 0：项目定位、环境基线和架构决策
- [x] 阶段 1：API 工程骨架、日志、探针和 Docker
- [ ] 阶段 2：PostgreSQL、迁移系统和核心领域模型
- [ ] 阶段 3：最小实验与评测闭环
- [ ] 阶段 4：文档摄取和版本管理
- [ ] 阶段 5：pgvector 向量检索
- [ ] 阶段 6：Elasticsearch BM25
- [ ] 阶段 7：混合召回和重排序
- [ ] 阶段 8：RAG 与 Agent 自动评测
- [ ] 阶段 9：A/B 对比、失败案例和回归门禁
- [ ] 阶段 10：监控、Kubernetes 与故障演练

## 设计文档

- [项目范围](docs/project-scope.md)
- [环境基线](docs/environment-baseline.md)
- [架构决定记录](docs/architecture/decisions.md)
