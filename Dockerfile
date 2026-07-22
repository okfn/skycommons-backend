# Build stage: install dependencies with uv into a project-local venv.
FROM python:3.13-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Runtime stage.
FROM python:3.13-slim-bookworm AS runtime

RUN useradd wagtail

EXPOSE 8000
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DJANGO_SETTINGS_MODULE=skycommons.settings.production \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --chown=wagtail:wagtail . .
RUN mkdir -p /app/static /app/media && chown wagtail:wagtail /app/static /app/media

USER wagtail

# Manifest static files are environment-independent, so collect at build
# time (requires no DB; dummy values satisfy production settings imports).
RUN SECRET_KEY=build-only ALLOWED_HOSTS=build POSTGRES_PASSWORD=build \
    python manage.py collectstatic --noinput --clear

# Waits for the DB, migrates, loads fixtures on first run, serves.
CMD ["./docker-entrypoint.sh"]
