FROM public.ecr.aws/docker/library/node:22-bookworm-slim@sha256:f3a68cf41a855d227d1b0ab832bed9749469ef38cf4f58182fb8c893bc462383

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir --break-system-packages \
    pytest==8.3.5 \
    pytest-json-ctrf==0.3.5

WORKDIR /app
COPY package.json ./package.json
COPY bin ./bin
COPY src ./src
COPY docs ./docs
COPY config ./config
COPY data ./data
COPY scripts ./scripts
COPY fixtures ./fixtures
COPY README.md ./README.md
