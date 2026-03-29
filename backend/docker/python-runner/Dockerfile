FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 sandbox

WORKDIR /sandbox

COPY backend/app/modules/executions/infrastructure/runners/languages/python/sandbox_trace_runner.py /sandbox/sandbox_trace_runner.py

USER sandbox

ENTRYPOINT ["python", "/sandbox/sandbox_trace_runner.py"]
