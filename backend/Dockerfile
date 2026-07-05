# WHY THIS WAS CHOSEN:
# This Dockerfile uses a multi-stage build to compile dependencies and creates a minimal,
# secure final image based on Python 3.12-slim. It implements a non-root user for security
# and uses a built-in Python-based HEALTHCHECK to avoid installing curl/wget.
#
# WHY /install instead of --user:
# Using `pip install --prefix=/install` writes packages to a fixed, predictable path
# that can be cleanly copied to the runner stage. The `--user` flag writes to
# /root/.local in the builder, but copying that to /home/appuser/.local causes
# Python's site-packages resolver to miss the packages at runtime because the
# ownership transfer changes the expected path structure.

# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Final minimal runtime image
FROM python:3.12-slim AS runner

WORKDIR /app

# Install runtime system packages if any, and clean up cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for process isolation
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -d /app -s /sbin/nologin appuser

# Copy installed Python packages from builder stage into the system Python path
COPY --from=builder /install /usr/local

COPY --chown=appuser:appgroup src/ /app/src/
COPY --chown=appuser:appgroup data/ /app/data/

ENV PYTHONPATH=/app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Health check using python standard library to minimize tool dependency
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run FastAPI app with Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
