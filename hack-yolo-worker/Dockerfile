FROM python:3.13.3-bookworm

RUN apt-get update && apt-get install -y libgl1

WORKDIR /app

RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --locked

COPY src .

EXPOSE 8000

CMD ["uv", "run", "starter.py"]