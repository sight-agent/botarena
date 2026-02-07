FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY runner/runner /app/runner

# No third-party deps. We run with `python -I` in the sandbox.

