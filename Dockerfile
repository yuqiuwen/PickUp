FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV TZ=Asia/Shanghai

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project


COPY pyproject.toml uv.lock .

RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

# COPY requirements.txt .
# RUN pip3 install -i https://mirrors.cloud.tencent.com/pypi/simple --no-cache-dir --upgrade -r requirements.txt

ENV PATH="/app/.venv/bin:$PATH"

COPY . .

RUN mkdir -p /data/logs && chmod -R 777 /data/logs

RUN chmod +x /app/docker-entrypoint.sh
ENTRYPOINT ["/app/docker-entrypoint.sh"]


CMD ["gunicorn", "-c", "gunicorn.conf.py", "manage:app"]
