# Use uv's ARM64 Python base image
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Copy uv files
COPY pyproject.toml uv.lock ./

# Install dependencies (including strands-agents)
RUN uv sync --frozen --no-cache

# Signal that this is running in Docker for host binding logic
ENV DOCKER_CONTAINER=1

# Copy agent files
COPY agent.py ./
COPY prompt_selector ./prompt_selector
COPY structured_output ./structured_output

# Create non-root user
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

# Expose port
EXPOSE 8080

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/ping || exit 1

# Run application
CMD ["uv", "run", "uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "8080"]