FROM rust:1.86-bookworm

RUN apt-get update && apt-get install -y \
    build-essential curl git ca-certificates gnupg \
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest==8.4.1 pytest-json-ctrf==0.3.5 --break-system-packages --quiet

# Pin to exact commits for reproducibility.
# MAIN_COMMIT: the full working implementation (oracle solution).
# SKELETON_COMMIT: SQL method bodies replaced with todo!().
ARG MAIN_COMMIT=473afbdb4aea5e5403896359b5dee31ec8ae5ccf
ARG SKELETON_COMMIT=9c03c5ee0f233996fe750445b848fa9688fccd4d

# ==========================================================================
# Phase 1: Clone at MAIN commit (full working implementation).
# ==========================================================================
RUN git clone https://github.com/Semrin-mena/toydb.git /app && \
    cd /app && git checkout ${MAIN_COMMIT}

WORKDIR /app

# ==========================================================================
# Phase 2: Build and verify the full implementation passes tests.
# This also pre-downloads and caches all Cargo dependencies.
# ==========================================================================
RUN cargo build --release 2>&1 | tail -20
RUN cargo test --no-fail-fast 2>&1 | tail -50

# ==========================================================================
# Phase 2b: Apply MEDIAN / STRING_AGG difficulty patches, then verify the
# patched implementation still passes all tests (including the new ones).
# ==========================================================================
COPY patch_main.py /patch_main.py
RUN python3 /patch_main.py
RUN cargo test --lib --no-fail-fast -- --test-threads=1

# ==========================================================================
# Phase 3: Back up the solution SQL source and test infrastructure
# to /private, then encrypt it.
# ==========================================================================
RUN mkdir -p /private/solution && \
    # Save the full SQL implementation (10 files the agent must rewrite)
    cp src/sql/parser/lexer.rs       /private/solution/ && \
    cp src/sql/parser/parser.rs      /private/solution/ && \
    cp src/sql/planner/planner.rs    /private/solution/ && \
    cp src/sql/planner/plan.rs       /private/solution/ && \
    cp src/sql/planner/optimizer.rs  /private/solution/ && \
    cp src/sql/execution/executor.rs /private/solution/ && \
    cp src/sql/execution/session.rs  /private/solution/ && \
    cp src/sql/execution/aggregator.rs /private/solution/ && \
    cp src/sql/execution/join.rs     /private/solution/ && \
    cp src/sql/engine/local.rs       /private/solution/ && \
    # Save all test scripts (goldenscripts) for tamper-proof restoration
    cp -r src/sql/testscripts        /private/sql_testscripts && \
    # Save raft and storage testscripts too
    cp -r src/raft/testscripts       /private/raft_testscripts && \
    # Save integration tests
    cp -r tests                      /private/integration_tests && \
    # Save the test runner module (sql/mod.rs has SQLRunner/ExpressionRunner)
    cp src/sql/mod.rs                /private/sql_mod.rs

# Encrypt /private and delete the plaintext so the agent cannot access it.
RUN tar czf - -C / private | \
    gpg --batch --yes --passphrase uci --pinentry-mode loopback \
    -c -o /private.enc && \
    rm -rf /private

# ==========================================================================
# Phase 4: Switch to the SKELETON branch.
# This replaces the 10 SQL implementation files with todo!() stubs,
# while preserving all type definitions, signatures, and infrastructure.
# ==========================================================================
RUN cd /app && git checkout --force ${SKELETON_COMMIT}

# ==========================================================================
# Phase 4b: Apply skeleton patches to add MEDIAN / STRING_AGG enum variants
# (no implementations — those are left as todo!() for the agent to fill in).
# ==========================================================================
COPY patch_skeleton.py /patch_skeleton.py
RUN python3 /patch_skeleton.py

# ==========================================================================
# Phase 5: Clean up to prevent cheating.
# ==========================================================================
# Remove .git so the agent cannot checkout the main branch.
RUN rm -rf /app/.git

# Clean build artifacts — agent will rebuild from the skeleton.
RUN rm -rf target
WORKDIR /app

# ==========================================================================
# Phase 6: Add host resolution for the vLLM inference server.
# /etc/hosts is reset at container start, so this must run via an entrypoint.
# ==========================================================================
# RUN printf '#!/bin/bash\nset -e\necho "100.119.248.99 friend-llm" >> /etc/hosts\nexec "$@"\n' \
#     > /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

# WORKDIR /app
# ENTRYPOINT ["/docker-entrypoint.sh"]
# CMD ["bash"]
