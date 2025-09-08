FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONFAULTHANDLER=1

ARG APP_UID=10001
ARG APP_GID=10001
RUN groupadd -g $APP_GID appuser \
 && useradd -m -u $APP_UID -g $APP_GID appuser

WORKDIR /app


RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY --chown=$APP_UID:$APP_GID alembic/ ./alembic/
COPY --chown=$APP_UID:$APP_GID alembic.ini ./alembic.ini
COPY --chown=$APP_UID:$APP_GID src/ ./src/


RUN mkdir -p /data/in /data/out \
 && chown -R $APP_UID:$APP_GID /data

USER appuser
EXPOSE 8000


ENTRYPOINT ["uvicorn", "src.main:app"]
CMD ["--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
