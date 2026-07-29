ARG PYTHON_VERSION=3.12-slim-bookworm

FROM python:${PYTHON_VERSION} AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

COPY pyproject.toml ./
COPY src ./src

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install --prefix=/install .

FROM python:${PYTHON_VERSION} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EVALFORGE_HOST=0.0.0.0 \
    EVALFORGE_PORT=8000 \
    EVALFORGE_LOG_LEVEL=INFO

WORKDIR /app

RUN groupadd --system --gid 10001 evalforge \
    && useradd \
        --system \
        --uid 10001 \
        --gid evalforge \
        --home-dir /app \
        --shell /usr/sbin/nologin \
        evalforge

COPY --from=builder /install /usr/local

USER evalforge

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=2)"]

CMD ["python", "-m", "evalforge"]
