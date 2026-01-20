# MCP Finance Backend - Environment Setup

## Using Mamba (Recommended)

### Prerequisites

Install mamba or micromamba:
```bash
# Option 1: Install mamba (if you have conda)
conda install -n base -c conda-forge mamba

# Option 2: Install micromamba (standalone, faster)
# macOS/Linux
curl -Ls https://micro.mamba.pm/install.sh | bash

# Or with Homebrew
brew install micromamba
```

### Create Environment

```bash
# Using mamba
mamba env create -f environment.yml

# Or using micromamba
micromamba create -f environment.yml

# Verify environment was created
mamba env list
```

### Activate Environment

```bash
# Using mamba
mamba activate mcp-finance-backend

# Or using micromamba
micromamba activate mcp-finance-backend

# Verify Python version and packages
python --version  # Should show Python 3.11.x
mamba list        # Show all installed packages
```

### Update Environment

When environment.yml changes:
```bash
# Using mamba
mamba env update -f environment.yml --prune

# Or using micromamba
micromamba update -f environment.yml --prune
```

## Using Conda-Lock (Reproducible Builds)

For exact reproducibility across different platforms:

### Generate Lock File

```bash
# Install conda-lock
mamba install -c conda-forge conda-lock

# Generate lock file for all platforms
conda-lock -f environment.yml --lockfile conda-lock.yml

# Or for specific platforms
conda-lock -f environment.yml -p linux-64 -p osx-64 -p osx-arm64
```

### Create Environment from Lock File

```bash
# Using mamba
mamba create -n mcp-finance-backend -f conda-lock.yml

# Or using micromamba
micromamba create -n mcp-finance-backend -f conda-lock.yml
```

**Important:** Commit both `environment.yml` and `conda-lock.yml` to git for team reproducibility.

## Running the Server

```bash
# Activate environment
mamba activate mcp-finance-backend

# Set required environment variables
export GCP_PROJECT_ID="your-project-id"
export BUCKET_NAME="your-bucket-name"

# Start the server
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Development Workflow

### Install Dev Dependencies

Already included in environment.yml:
- pytest - Testing framework
- pytest-asyncio - Async testing support
- black - Code formatter
- ruff - Fast linter
- mypy - Type checker

### Run Tests

```bash
mamba activate mcp-finance-backend
pytest tests/
```

### Format Code

```bash
black .
```

### Lint Code

```bash
ruff check .
```

### Type Check

```bash
mypy main.py
```

## Docker Integration

Using the environment in Docker (see Dockerfile):

```dockerfile
FROM mambaorg/micromamba:1.5.6 as builder

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

FROM mambaorg/micromamba:1.5.6
COPY --from=builder /opt/conda /opt/conda
WORKDIR /app
COPY --chown=$MAMBA_USER:$MAMBA_USER . /app
EXPOSE 8000
CMD ["python", "main.py"]
```

## Troubleshooting

### Environment Creation Fails

```bash
# Update mamba
mamba update mamba

# Clear cache
mamba clean --all

# Try with verbose output
mamba env create -f environment.yml -v
```

### Package Conflicts

```bash
# Remove environment and recreate
mamba env remove -n mcp-finance-backend
mamba env create -f environment.yml
```

### Slow Installation

```bash
# Use micromamba (faster)
micromamba create -f environment.yml

# Or use parallel downloads
mamba env create -f environment.yml --parallel
```

## Package Sources

### From conda-forge:
- Python 3.11
- FastAPI, Uvicorn, Pydantic
- NumPy, Pandas
- httpx
- Development tools (pytest, black, ruff, mypy)

### From PyPI (pip):
- google-cloud-* packages (GCP services)
- yfinance (financial data)

**Note:** Only packages not available in conda-forge are installed via pip.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Micromamba
        uses: mamba-org/setup-micromamba@v1
        with:
          environment-file: cloud-run/environment.yml
          cache-environment: true

      - name: Run Tests
        run: |
          micromamba activate mcp-finance-backend
          pytest tests/
```

## Environment Info

- **Name:** mcp-finance-backend
- **Python:** 3.11
- **Primary Channel:** conda-forge
- **Package Manager:** mamba/micromamba (2-5x faster than conda)
- **Reproducibility:** Use conda-lock.yml for exact versions

## Next Steps

1. ✅ Install mamba or micromamba
2. ✅ Create environment: `mamba env create -f environment.yml`
3. ✅ Activate environment: `mamba activate mcp-finance-backend`
4. ✅ Set environment variables (GCP_PROJECT_ID, etc.)
5. ✅ Run server: `python main.py`
6. ✅ Generate lock file: `conda-lock -f environment.yml`
7. ✅ Commit both environment.yml and conda-lock.yml

## Resources

- [Mamba Documentation](https://mamba.readthedocs.io/)
- [Micromamba Guide](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html)
- [Conda-lock](https://conda.github.io/conda-lock/)
- [Conda-forge](https://conda-forge.org/)
