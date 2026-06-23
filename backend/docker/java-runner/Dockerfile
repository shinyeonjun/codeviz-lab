FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10001 sandbox

WORKDIR /sandbox

COPY app/modules/executions/infrastructure/runners/languages/java/java_execute_runner.py /sandbox/java_execute_runner.py

USER sandbox

ENTRYPOINT ["python", "/sandbox/java_execute_runner.py"]
