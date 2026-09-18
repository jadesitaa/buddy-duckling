FROM python:3.14-slim

# Never write .pyc files, never buffer stdout - both make container logs behave.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first, so rebuilding after a code change reuses this layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini pytest.ini ./
COPY migrations ./migrations
COPY app ./app

# Run as a non-root user.
RUN useradd --create-home duckling && chown -R duckling /app
USER duckling

EXPOSE 8000

# Bring the schema up to date, then serve. Running migrations here means a new
# deployment never starts against an old schema.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
