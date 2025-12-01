FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /app
COPY . /app

ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
RUN uv sync --frozen

# CMD ["tail", "-f", "/dev/null"]
CMD ["sh", "-c", "uv run main.py"]
