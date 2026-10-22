# Anima on Aiven Runtime. Runtime reads the port from EXPOSE; connect Postgres and Valkey as
# services and they arrive as DATABASE_URL and VALKEY_URL (never set them here).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONUTF8=1
WORKDIR /app

COPY requirements.txt ./
COPY demo/requirements.txt demo/
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd --create-home anima && chown -R anima /app
USER anima

EXPOSE 8080
# One worker: the demo replay keeps its state in process and resets the stores.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
