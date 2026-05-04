FROM python:3.10-slim

ARG NATS_SERVER_VERSION=2.10.16
RUN apt-get update && apt-get install -y curl tar && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL -o /tmp/nats-server.tar.gz \
  https://github.com/nats-io/nats-server/releases/download/v${NATS_SERVER_VERSION}/nats-server-v${NATS_SERVER_VERSION}-linux-amd64.tar.gz \
  && tar -xzf /tmp/nats-server.tar.gz -C /tmp \
  && mv /tmp/nats-server-v${NATS_SERVER_VERSION}-linux-amd64/nats-server /usr/local/bin/nats-server \
  && chmod +x /usr/local/bin/nats-server

WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
