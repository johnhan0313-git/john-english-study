FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
RUN uv pip install --system .

COPY app ./app

RUN mkdir -p /app/data/media

ENV DATABASE_URL=sqlite:///./data/app.db
ENV MEDIA_DIR=/app/data/media

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
