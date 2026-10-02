FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY workshop ./workshop
COPY static ./static
RUN useradd --uid 10001 --create-home workshop
USER workshop
CMD ["sh", "-c", "exec uvicorn workshop.server:app --host 0.0.0.0 --port ${PORT:-8080}"]
