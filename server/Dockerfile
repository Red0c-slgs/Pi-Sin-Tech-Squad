FROM python:3.13.3-bookworm

RUN apt-get update

ARG USER=oleg
ARG UID=1230
ARG GID=1230

WORKDIR /app

RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

COPY src .
COPY migrations ./migrations

EXPOSE 5300

CMD ["uv", "run", "--no-dev", "starter.py"]
