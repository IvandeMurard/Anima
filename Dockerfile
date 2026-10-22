# Anima on Aiven Runtime: FastAPI app + demo runner. Connect Aiven Postgres -> DATABASE_URL, Valkey -> VALKEY_URL.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app
COPY requirements.txt ./
COPY demo/requirements.txt demo/
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
