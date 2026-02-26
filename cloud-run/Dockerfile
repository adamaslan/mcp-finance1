# Stage 1: Build - Install dependencies using micromamba
FROM mambaorg/micromamba:1.5.6 as builder

# Copy environment file with correct ownership (from cloud-run/)
COPY --chown=$MAMBA_USER:$MAMBA_USER cloud-run/environment.yml /tmp/environment.yml

# Create environment in base (faster than creating new named environment)
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

# Stage 2: Runtime - Minimal production image
FROM mambaorg/micromamba:1.5.6

# Copy installed environment from builder
COPY --from=builder /opt/conda /opt/conda

# Set working directory
WORKDIR /app

# Copy application code with correct ownership
# CRITICAL: --chown ensures non-root ownership

# Copy FastAPI wrapper (cloud-run specific)
COPY --chown=$MAMBA_USER:$MAMBA_USER cloud-run/main.py ./main.py

# Copy the SINGLE SOURCE OF TRUTH package (src/ is canonical)
COPY --chown=$MAMBA_USER:$MAMBA_USER src ./src

# Copy fibonacci (moved to project root)
COPY --chown=$MAMBA_USER:$MAMBA_USER fibonacci ./fibonacci

# Environment configuration
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Container runs as 'mambauser' (UID 1000) by default - NOT ROOT
# The mambaorg/micromamba base image already sets USER mambauser

# Expose port (non-privileged port)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run the application
# Using micromamba's shell initialization to ensure conda environment is active
CMD ["python", "main.py"]
