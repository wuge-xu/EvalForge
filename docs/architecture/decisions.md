# EvalForge 架构决定记录

## ADR-001：采用 Evaluation-first 设计

状态：Accepted

平台中心对象是数据集、实验、指标、失败案例和质量门禁，而不是聊天会话。

## ADR-002：核心配置使用不可变版本

状态：Accepted

文档、数据集、Prompt、模型、Embedding、RAG 配置、重排序器、Agent 工作流和 Evaluator Suite 均采用版本对象。

已经被实验引用的版本不能原地修改。

## ADR-003：实验绑定完整配置快照

状态：Accepted

实验启动时必须保存所有参与运行的版本引用和关键配置快照，防止配置变化导致历史实验不可解释。

## ADR-004：PostgreSQL 作为主数据源

状态：Accepted

项目、版本、数据集、测试样例、实验、运行结果、指标、失败案例和质量门禁等结构化数据统一存储在 PostgreSQL。

## ADR-005：pgvector 负责稠密向量检索

状态：Accepted

文档切片的向量表示保存在 pgvector 中，初始索引方案采用 HNSW。

## ADR-006：Elasticsearch 负责 BM25 词法检索

状态：Accepted

Elasticsearch 负责关键词、专有名词、编号和精确文本相关的 BM25 召回。

## ADR-007：应用层自行实现混合融合

状态：Accepted

项目自行实现 Reciprocal Rank Fusion，并保存 dense rank、lexical rank、RRF score、rerank score 和 final rank。

## ADR-008：重排序器采用可插拔接口

状态：Accepted

支持 Noop、Cross Encoder、远程模型和 LLM Reranker 等不同实现。

初期使用确定性实现保证测试稳定。

## ADR-009：核心评测能力自行实现

状态：Accepted

Recall@K、Hit Rate@K、MRR、实验聚合、A/B 配对比较、失败案例提取和质量门禁引擎由 EvalForge 自行实现。

## ADR-010：第三方评测框架不作为平台核心

状态：Accepted

Ragas、DeepEval、Promptfoo、Phoenix 等工具只作为指标参考、插件或兼容格式，不替代核心领域模型和执行引擎。

## ADR-011：Trace 与请求快照双轨记录

状态：Accepted

OpenTelemetry 用于标准化可观测 Trace。

EvalForge 自有 Request Snapshot 用于保存实验输入、渲染 Prompt、检索结果、模型参数、工具调用和回放所需数据。

## ADR-012：CI 使用确定性测试环境

状态：Accepted

CI 默认使用固定数据集、Mock LLM、Fake Embedding 和确定性工具，不依赖真实付费模型或外部不稳定服务。

## ADR-013：统一使用 Python 3.12

状态：Accepted

本地开发、测试、Docker 和 GitHub Actions 均使用 Python 3.12。

## ADR-014：先同步闭环，后异步化

状态：Accepted

第一版先同步打通：

数据集 → 实验 → 批量运行 → 指标 → 报告 → 质量门禁。

核心闭环稳定后，再引入 Redis Streams、消费者组、ACK、重试和故障恢复。

## ADR-015：本地基础设施按 Profile 启动

状态：Accepted

考虑到 WSL 内存约为 7.6 GiB，Docker Compose 将基础设施划分为 core、search 和 observability 三组，避免日常开发同时运行全部组件。

## ADR-016：Python 包采用 src 布局

状态：Accepted

项目代码统一放置在 `src/evalforge` 中。

该布局可以避免测试时意外导入项目根目录中的源码，并使本地开发、可编辑安装和打包后的导入行为保持一致。

## ADR-017：使用 pyproject.toml 统一管理工程配置

状态：Accepted

项目元数据、Python 版本约束、运行依赖、开发依赖、pytest、Ruff 和 mypy 配置统一保存在 `pyproject.toml`。

当前阶段使用 setuptools 作为构建后端，并通过 pip 进行可编辑安装。

## ADR-018：使用类型安全的集中配置系统

状态：Accepted

API、Worker 和基础设施组件统一通过 Pydantic Settings 获取运行配置。

环境变量统一使用 `EVALFORGE_` 前缀，并支持开发环境的 `.env` 文件。端口、布尔值、运行环境和日志级别在应用启动阶段完成解析与校验。

配置对象在单个进程中进行缓存，测试可以显式清除缓存，避免不同测试用例之间共享旧配置。

## ADR-019：FastAPI 使用应用工厂创建

状态：Accepted

通过 `create_app` 创建 FastAPI 应用，并允许测试或不同运行环境显式注入 Settings。

全局 `app` 仅作为 ASGI 服务入口，核心应用初始化逻辑保留在应用工厂中。

## ADR-020：健康检查使用非版本化稳定路径

状态：Accepted

基础健康检查固定使用 `/health`，供 Docker、Kubernetes、负载均衡器和外部探针调用。

健康检查不属于业务领域 API，因此不放入 `/api/v1` 前缀。后续业务接口统一使用版本化路径。

## ADR-021：使用 JSON 结构化日志和请求关联 ID

状态：Accepted

应用日志采用单行 JSON 格式，基础字段包含时间、级别、Logger、消息和 request_id。

HTTP 请求优先使用合法的 `X-Request-ID` 请求头；不存在或格式不合法时生成新的 UUID。该标识通过 ContextVar 在当前异步请求上下文中传播，并写回响应头。

请求中间件记录请求开始、完成、状态码和耗时。后续数据库、检索、模型、Worker 和 Evaluator 日志可以继续附加 experiment_id、case_id、trace_id 等领域标识。

## ADR-022：区分 Liveness 与 Readiness

状态：Accepted

`/health/live` 只判断 API 进程是否能够响应，不检查外部依赖。

`/health/ready` 判断应用是否已经完成启动并能够接收业务流量。应用生命周期启动前和关闭后均将 Readiness 设置为 false。

后续接入 PostgreSQL、Redis 和其他关键基础设施时，依赖检查将加入 Readiness，而不会加入 Liveness，避免外部依赖短暂故障导致容器被无意义地反复重启。

## ADR-023：统一使用 Python 模块入口启动 API

状态：Accepted

本地、Docker 和 Kubernetes 统一通过 `python -m evalforge` 或安装后的 `evalforge-api` 命令启动服务。

启动入口读取类型安全的 Settings，并将 host、port 和日志级别传递给 Uvicorn，避免不同部署环境维护重复的启动参数。

## ADR-024：API 镜像使用多阶段构建和非 root 用户

状态：Accepted

Docker 镜像采用 Python 3.12 slim 基础镜像。Builder 阶段负责安装项目及运行依赖，Runtime 阶段只复制安装结果，减少构建缓存和无关文件进入最终镜像。

容器内部统一监听 8000 端口，并以 UID 10001 的非 root 用户运行。

镜像内置基于 `/health/ready` 的 Docker HEALTHCHECK。宿主机端口映射由运行环境决定，不要求固定使用 8000。

## ADR-025：持久化层首先采用同步 SQLAlchemy

状态：Accepted

EvalForge 当前使用 SQLAlchemy 2.x 同步 Engine、Psycopg 3 和显式 SessionFactory 访问 PostgreSQL。

当前阶段优先保证事务边界、Session 生命周期和领域模型设计清晰，不为了形式上的异步提前引入 AsyncSession。后续如果实际压测证明数据库访问成为并发瓶颈，再评估迁移到异步持久化层。

数据库连接统一通过 Pydantic Settings 配置，并启用 pool_pre_ping 检测失效连接。

## ADR-026：使用 Alembic 管理数据库 Schema

状态：Accepted

PostgreSQL Schema、pgvector 扩展和后续表结构变化统一通过 Alembic migration 管理，不允许依赖人工执行 SQL 维护环境状态。

Alembic 与 API 共用 EvalForge Settings 中的数据库连接配置，不在 alembic.ini 中保存数据库密码。

SQLAlchemy Declarative Base 使用稳定的约束命名规则，降低不同环境自动生成约束名称造成的迁移差异。

ORM Metadata 属于基础设施持久化层，不直接作为领域模型本身。

## ADR-027：评测数据集采用显式不可变版本层

状态：Accepted

EvalForge 将 Project、Dataset、DatasetVersion、TestCase 建模为明确的层级关系。

Dataset 表示逻辑数据集，DatasetVersion 表示具体、可复现的数据快照。后续 Experiment 必须绑定 DatasetVersion，而不是直接绑定可持续变化的 Dataset，从而保证历史实验结果能够追溯和复现。

DatasetVersion 使用单调正整数 version_number，并通过数据库唯一约束保证同一 Dataset 内版本不可重复。content_hash 用于记录版本内容指纹。

TestCase 属于具体 DatasetVersion，external_id 仅要求在同一版本内唯一；扩展属性使用 PostgreSQL JSONB 保存。

当前阶段使用 UUID 主键、带时区时间戳和数据库级唯一/检查/外键约束。Project 到 TestCase 的生命周期暂时采用 ON DELETE CASCADE；后续 Experiment 开始引用 DatasetVersion 后，将重新评估生产环境删除策略。

## ADR-028：实验运行数据采用不可变配置快照和受保护的数据引用

状态：Accepted

Experiment 表示一次可复现的评测运行，并固定 project_id、dataset_version_id、config_snapshot 和 config_hash。后续即使 Prompt、Model、RAG 或 Agent 配置继续演进，历史实验仍保留运行时完整配置快照。

Experiment 和 ExperimentCase 对 DatasetVersion、TestCase 使用 ON DELETE RESTRICT，避免已参与历史实验的评测数据被直接删除而破坏可复现性。

ExperimentCase、MetricResult 和 GateResult 属于实验运行结果，其生命周期跟随 Experiment，通过 ON DELETE CASCADE 清理。

MetricResult 区分 experiment 和 case 两种 scope，并通过数据库 Check Constraint 与 PostgreSQL partial unique index保证同一作用域、指标名和 evaluator 不产生重复结果。

Experiment 与 ExperimentCase 的状态、延迟非负、Gate operator 等基础运行时不变量由 PostgreSQL 约束兜底。涉及跨多张表的语义一致性将在后续 application service 层继续校验。
