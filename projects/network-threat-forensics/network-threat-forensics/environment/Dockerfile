FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root

COPY netflow.csv /root/
COPY dns_queries.csv /root/
COPY investigation_config.json /root/

COPY skills /root/.claude/skills
COPY skills /root/skills
#COPY skills /root/.codex/skills
#COPY skills /root/.opencode/skill
#COPY skills /root/.goose/skills
#COPY skills /root/.factory/skills
#COPY skills /root/.agents/skills
#COPY skills /root/.gemini/skills

RUN pip3 install --break-system-packages \
    pandas==2.3.3 \
    numpy==2.3.0
