FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev gdb \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10001 sandbox

WORKDIR /sandbox

COPY app/modules/executions/infrastructure/runners/languages/c/c_trace_runner.py /sandbox/c_trace_runner.py

USER sandbox

ENTRYPOINT ["python", "/sandbox/c_trace_runner.py"]
