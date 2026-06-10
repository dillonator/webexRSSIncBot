FROM python:3.14-slim
# bring in the uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./
# Install dependencies into a portable virtual environment
RUN uv sync --frozen --no-dev --no-install-project
COPY bot.py .
ENV STATE_FILE=/data/seen.json POLL_SECONDS=600
VOLUME ["/data"]
CMD ["python", "-u", "bot.py"]