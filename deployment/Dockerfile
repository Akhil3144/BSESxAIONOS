FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt && useradd --uid 10001 --create-home pilot
COPY backend backend
COPY frontend frontend
COPY alembic.ini .
RUN mkdir -p /app/data && chown -R pilot:pilot /app
USER pilot
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
