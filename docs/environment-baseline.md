# EvalForge 开发环境基线

## 记录日期

2026-07-29

## 操作系统

- Windows 11
- WSL2
- Linux Kernel：6.6.87.2-microsoft-standard-WSL2
- CPU 架构：x86_64

## 计算资源

- CPU：8 核
- WSL 内存：约 7.6 GiB
- Swap：2 GiB
- 可用磁盘：约 922 GiB

## Python

- Conda 环境：evalforge-py312
- Python：3.12.13
- pip：26.1.2
- setuptools：83.0.0
- wheel：0.47.0

## Docker

- Docker Desktop：4.75.0
- Docker Engine：29.5.2
- Docker Compose：5.1.3
- Storage Driver：overlayfs
- WSL Integration：已启用

## Kubernetes

- K3s：v1.35.5+k3s1

## Git

- Git：2.43.0
- 默认分支：main

## 资源约束

当前 WSL 总内存约为 7.6 GiB，因此本地环境采用按需启动策略。

计划使用以下 Docker Compose Profiles：

- core：PostgreSQL/pgvector、Redis、API
- search：Elasticsearch、MinIO
- observability：Prometheus、Grafana、Trace 后端

日常开发时不默认同时启动所有基础设施组件。

## Python 版本策略

本地开发、Docker 镜像和 GitHub Actions 均固定使用 Python 3.12。

不使用全局 Python 3.13 作为 EvalForge 的运行环境。
