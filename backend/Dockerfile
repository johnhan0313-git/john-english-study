FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG PIP_INDEX_URL
ARG PIP_HTTP_PROXY
ARG PIP_HTTPS_PROXY

COPY requirements.txt .
RUN if [ -n "${PIP_HTTP_PROXY}" ]; then export HTTP_PROXY="${PIP_HTTP_PROXY}" HTTPS_PROXY="${PIP_HTTPS_PROXY}"; fi; \
    pip install --no-cache-dir --default-timeout=300 \
    ${PIP_INDEX_URL:+--index-url "$PIP_INDEX_URL"} \
    -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
