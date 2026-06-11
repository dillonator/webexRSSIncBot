FROM python:3.14-slim
# bring in the uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
# deps first for layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# put the venv on PATH so `python` IS the venv interpreter
ENV PATH="/app/.venv/bin:$PATH"

# app code only — NO bot.env (secrets come in at runtime)
COPY webexIncBot.py ./

ENV STATE_FILE=/data/seen.json POLL_SECONDS=60
VOLUME ["/data"]

CMD ["python", "-u", "webexIncBot.py"]