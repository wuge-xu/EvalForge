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
