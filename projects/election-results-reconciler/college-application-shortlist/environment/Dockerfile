FROM python:3.11-slim

RUN pip install --no-cache-dir pandas==2.0.3 numpy==1.24.3

RUN mkdir -p /app/data /app/skills

COPY data/ /app/data/
COPY skills/ /app/skills/

# Copy skills to agent-specific locations
COPY skills /root/.claude/skills
COPY skills /root/.codex/skills
COPY skills /root/.opencode/skill
COPY skills /root/.goose/skills
COPY skills /root/.factory/skills
COPY skills /root/.agents/skills
COPY skills /root/.gemini/skills
COPY skills /root/.github/skills

WORKDIR /app

CMD ["/bin/bash"]
