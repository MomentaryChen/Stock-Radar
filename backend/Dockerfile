FROM python:3.12-slim

WORKDIR /app

COPY backend/pyproject.toml backend/pyproject.toml
RUN pip install --no-cache-dir -e "./backend[dev]"

COPY . .
