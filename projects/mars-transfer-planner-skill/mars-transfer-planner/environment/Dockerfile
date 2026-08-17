FROM python:3.11-slim

# Install PostgreSQL
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql postgresql-client && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir psycopg2-binary==2.9.9 pandas==2.0.3 numpy==1.24.3

RUN mkdir -p /app/data /app/skills /app/output

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

# Initialize PostgreSQL and seed data
USER postgres
RUN /usr/lib/postgresql/*/bin/initdb -D /var/lib/postgresql/data
RUN /usr/lib/postgresql/*/bin/pg_ctl -D /var/lib/postgresql/data -l /tmp/pg.log start && \
    psql -c "CREATE DATABASE mission_db;" && \
    psql -d mission_db -f /app/data/seed.sql && \
    /usr/lib/postgresql/*/bin/pg_ctl -D /var/lib/postgresql/data stop
USER root

# Script to start postgres before agent runs
RUN printf '#!/bin/bash\nsu - postgres -c "/usr/lib/postgresql/*/bin/pg_ctl -D /var/lib/postgresql/data -l /tmp/pg.log start"\nsleep 2\nexec "$@"\n' > /app/start.sh && chmod +x /app/start.sh

WORKDIR /app

ENTRYPOINT ["/app/start.sh"]
CMD ["/bin/bash"]
