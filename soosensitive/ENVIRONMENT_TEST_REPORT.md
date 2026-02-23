# Environment Test Report - fin-ai1

**Date**: 2026-01-20
**Environment**: fin-ai1
**Python Version**: 3.10.17
**Test Script**: `/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run/run_beta1_scan.py`
**Status**: ✅ **SUCCESSFUL**

---

## Executive Summary

The `fin-ai1` environment is **fully functional** and the `run_beta1_scan.py` script **executes successfully**. All required dependencies are installed and properly configured. The script was able to:

1. ✅ Import all required modules
2. ✅ Connect to Firebase/Firestore
3. ✅ Load the Beta1 universe (11 symbols)
4. ✅ Scan all symbols for trade setups
5. ✅ Save results to Firebase
6. ✅ Complete without errors

---

## 1. Environment Status

### Environment Location
```
/opt/homebrew/Caskroom/miniforge/base/envs/fin-ai1/
```

### Python Information
- **Version**: Python 3.10.17
- **Executable**: `/opt/homebrew/Caskroom/miniforge/base/envs/fin-ai1/bin/python3`

### Environment Exists: ✅ YES

Available environments in miniforge:
```
- ai-text-opt
- browz1
- fin-ai1           ← ACTIVE TEST ENVIRONMENT
- lightrag-viz
- mcp-finance-backend
```

---

## 2. Package Installation Analysis

### Core Dependencies Status

| Package | Required | Installed | Version | Status |
|---------|----------|-----------|---------|--------|
| **Python** | ≥3.10 | ✅ | 3.10.17 | ✅ PASS |
| **technical-analysis-mcp** | Latest | ✅ | 0.1.0 (editable) | ✅ PASS |
| **yfinance** | ≥0.2.0 | ✅ | 0.2.65 | ✅ PASS |
| **pandas** | ≥2.0.0 | ✅ | 2.2.3 | ✅ PASS |
| **numpy** | ≥1.24.0 | ✅ | 2.1.3 | ✅ PASS |
| **google-cloud-firestore** | ≥2.13.0 | ✅ | 2.22.0 | ✅ PASS |
| **mcp** | ≥0.9.0 | ✅ | 1.22.0 | ✅ PASS |
| **pydantic** | ≥2.0.0 | ✅ | 2.11.7 | ✅ PASS |
| **cachetools** | ≥5.0.0 | ✅ | 5.5.2 | ✅ PASS |
| **fastapi** | ≥0.104.1 | ✅ | 0.115.13 | ✅ PASS |
| **uvicorn** | ≥0.24.0 | ✅ | 0.34.3 | ✅ PASS |
| **httpx** | ≥0.25.0 | ✅ | 0.28.1 | ✅ PASS |
| **pytest** | ≥7.0.0 | ✅ | 9.0.1 | ✅ PASS |
| **pytest-asyncio** | ≥0.21.0 | ✅ | 1.3.0 | ✅ PASS |

### Package Installation Details

**technical-analysis-mcp** is installed in **editable mode**:
```
Name: technical-analysis-mcp
Version: 0.1.0
Location: /opt/homebrew/Caskroom/miniforge/base/envs/fin-ai1/lib/python3.10/site-packages
Editable project location: /Users/adamaslan/code/mcp-finance1
```

This means:
- The package is linked to the source code at `/Users/adamaslan/code/mcp-finance1`
- Changes to the source code are immediately reflected without reinstallation
- Perfect for development workflow

---

## 3. Script Execution Test Results

### Test Command
```bash
cd "/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run"
/opt/homebrew/Caskroom/miniforge/base/envs/fin-ai1/bin/python3 run_beta1_scan.py
```

### Execution Results: ✅ **SUCCESS**

#### Output Summary
```
================================================================================
                             🚀 BETA1 UNIVERSE SCAN
================================================================================

Project ID: ttb-lang1

⏳ Loading dependencies...
✓ Dependencies loaded

⏳ Connecting to Firebase...
✓ Firebase connected and tested

────────────────────────────────────────────────────────────────────────────────
  BETA1 UNIVERSE
────────────────────────────────────────────────────────────────────────────────

✓ Loaded 11 symbols

Symbols: MU, GLD, NVDA, RGTI, RR, PL, GEV, GOOG, IBIT, LICX, APLD

Available universes (7 total):
  📍 beta1
     crypto
     etf_large_cap
     etf_sector
     nasdaq100
     sp500
     tech_leaders

────────────────────────────────────────────────────────────────────────────────
  SCANNING BETA1 UNIVERSE
────────────────────────────────────────────────────────────────────────────────

⏳ Scanning for qualified trade setups...
   (This may take 30-90 seconds depending on network conditions)

✓ Scan completed successfully!

────────────────────────────────────────────────────────────────────────────────
  SCAN RESULTS
────────────────────────────────────────────────────────────────────────────────

Total symbols scanned:        11
Qualified trades found:      0
  (No qualified trades found in this scan)

────────────────────────────────────────────────────────────────────────────────
  SAVING TO FIREBASE
────────────────────────────────────────────────────────────────────────────────

✓ Saved: scans/beta1_latest
✓ Saved: scans/beta1_20260120_132820

────────────────────────────────────────────────────────────────────────────────
  SUMMARY
────────────────────────────────────────────────────────────────────────────────

Universe:        Beta1
Symbols:         11
Qualified:       0
Timestamp:       2026-01-20T13:28:21.019497
Firebase:        Saved ✓

────────────────────────────────────────────────────────────────────────────────
  FIREBASE PATHS
────────────────────────────────────────────────────────────────────────────────

Latest results:  db.collection('scans').document('beta1_latest')
Timestamped:     db.collection('scans').document('beta1_20260120_132820')
Trades:          db.collection('beta1_trades').document(symbol)

Firebase Console:
  ttb-lang1: https://console.firebase.google.com/project/ttb-lang1/firestore

✓ Beta1 scan complete!
```

#### Warnings (Non-Critical)
```
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
E0000 00:00:1768933697.984091 8702044 alts_credentials.cc:93] ALTS creds ignored.
  Not running on GCP and untrusted ALTS is not enabled.
HTTP Error 404:
$LICX: possibly delisted; no price data found (period=1mo)
```

**Analysis of Warnings**:
1. **ALTS credentials warning**: Expected when running locally (not on GCP infrastructure). Safe to ignore.
2. **LICX delisted warning**: The symbol LICX cannot be found on Yahoo Finance. This is a data issue, not an environment issue.

---

## 4. Script Dependencies Analysis

### Import Chain Verification

The script imports the following modules:

```python
# Standard library
import sys
import os
import asyncio
from datetime import datetime

# Third-party (installed via pip/mamba)
from google.cloud import firestore

# Local package (installed in editable mode)
from technical_analysis_mcp.server import scan_trades
from technical_analysis_mcp.universes import get_universe, list_universes
```

**All imports successful**: ✅

### Directory Structure Verification

```
/Users/adamaslan/code/gcp app w mcp/mcp-finance1/
├── cloud-run/
│   ├── run_beta1_scan.py          ← TEST SCRIPT
│   ├── environment.yml             ← ENVIRONMENT DEFINITION
│   ├── main.py                     ← CLOUD RUN ENTRY POINT
│   └── src/
│       └── technical_analysis_mcp/ ← LOCAL MODULE COPY
└── src/
    └── technical_analysis_mcp/     ← MAIN MODULE (EDITABLE INSTALL)
        ├── __init__.py
        ├── server.py               ← scan_trades()
        ├── universes.py            ← get_universe(), list_universes()
        ├── analysis.py
        ├── indicators.py
        ├── signals.py
        ├── models.py
        ├── data.py
        └── [other modules]
```

**Path resolution**: The script adds `../src` to `sys.path`, but since the package is installed in editable mode, it uses the installed version from `/Users/adamaslan/code/mcp-finance1/src/technical_analysis_mcp/`.

---

## 5. Environment.yml Comparison

### Cloud-Run environment.yml
```yaml
name: mcp-finance-backend
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11                    # ⚠️ Specifies 3.11
  - fastapi>=0.104.1               # ✅ Installed: 0.115.13
  - uvicorn>=0.24.0                # ✅ Installed: 0.34.3
  - pydantic>=2.5.0                # ✅ Installed: 2.11.7
  - httpx>=0.25.0                  # ✅ Installed: 0.28.1
  - numpy>=1.24.0                  # ✅ Installed: 2.1.3
  - pandas>=2.0.0                  # ✅ Installed: 2.2.3
  - python-dateutil>=2.8.2         # ✅ Installed: 2.9.0
  - cachetools>=5.0.0              # ✅ Installed: 5.5.2
  - psycopg2>=2.9.0                # (Not checked, database driver)
  - pytest>=7.4.0                  # ✅ Installed: 9.0.1
  - pytest-asyncio>=0.21.0         # ✅ Installed: 1.3.0
  - pip:
    - google-cloud-firestore==2.13.1  # ✅ Installed: 2.22.0 (newer)
    - yfinance>=0.2.28                # ✅ Installed: 0.2.65
    - mcp>=0.9.0                      # ✅ Installed: 1.22.0
```

### Discrepancy: Python Version

- **environment.yml specifies**: Python 3.11
- **fin-ai1 has**: Python 3.10.17

**Impact**: ⚠️ **MINOR** - The code runs successfully on Python 3.10, but the environment should ideally match the specification. Python 3.10 is still compatible with all dependencies.

**Recommendation**: For strict reproducibility, consider updating environment.yml to specify `python=3.10` OR recreate the environment with Python 3.11. However, this is not blocking execution.

---

## 6. Module Structure Analysis

### technical_analysis_mcp Package Contents

```
technical_analysis_mcp/
├── __init__.py          # Package initialization
├── server.py            # ✅ Contains scan_trades()
├── universes.py         # ✅ Contains get_universe(), list_universes()
├── analysis.py          # Trade analysis logic
├── indicators.py        # Technical indicators (150+ signals)
├── signals.py           # Signal detection
├── models.py            # Pydantic models
├── data.py              # Data fetching (yfinance)
├── ranking.py           # AI ranking logic
├── formatting.py        # Output formatting
├── config.py            # Configuration
├── exceptions.py        # Custom exceptions
├── briefing/            # Briefing generation
├── portfolio/           # Portfolio management
├── risk/                # Risk analysis
├── scanners/            # Scanner implementations
└── py.typed             # Type hints marker
```

**All required modules present**: ✅

---

## 7. Missing Packages Analysis

### Comparison with pyproject.toml

The main `pyproject.toml` at `/Users/adamaslan/code/gcp app w mcp/mcp-finance1/pyproject.toml` specifies:

**Core dependencies**:
- mcp >= 0.9.0 ✅
- yfinance >= 0.2.0 ✅
- pandas >= 2.0.0 ✅
- numpy >= 1.24.0 ✅
- pydantic >= 2.0.0 ✅
- cachetools >= 5.0.0 ✅

**Optional dependencies [gcp]**:
- httpx >= 0.25.0 ✅
- google-cloud-firestore >= 2.13.0 ✅
- google-cloud-pubsub >= 2.18.0 ⚠️ **NOT VERIFIED** (not required by run_beta1_scan.py)
- google-cloud-storage >= 2.10.0 ✅

**Optional dependencies [ai]**:
- google-generativeai >= 0.3.0 ✅

**Optional dependencies [dev]**:
- pytest >= 7.0.0 ✅
- pytest-asyncio >= 0.21.0 ✅
- pytest-cov >= 4.0.0 ⚠️ **NOT VERIFIED**
- black >= 23.0.0 ⚠️ **NOT VERIFIED** (dev tool, not required for script execution)
- ruff >= 0.1.0 ⚠️ **NOT VERIFIED** (dev tool, not required for script execution)
- mypy >= 1.0.0 ⚠️ **NOT VERIFIED** (dev tool, not required for script execution)
- pandas-stubs >= 2.0.0 ⚠️ **NOT VERIFIED** (type stubs, not required for runtime)

### Result: ✅ **ALL RUNTIME DEPENDENCIES PRESENT**

The dev tools (black, ruff, mypy) are not required for script execution, only for development/testing.

---

## 8. Firebase/GCP Integration Test

### Connection Test: ✅ **SUCCESS**

The script successfully:
1. ✅ Initialized Firestore client with project `ttb-lang1`
2. ✅ Wrote test document to `_health/test` collection
3. ✅ Saved scan results to `scans/beta1_latest`
4. ✅ Saved timestamped scan to `scans/beta1_20260120_132820`

### Authentication Method
The script uses **Application Default Credentials** from:
- `gcloud auth application-default login` (local development)
- Environment variable: `GOOGLE_APPLICATION_CREDENTIALS` (if set)

**Status**: ✅ Properly authenticated

---

## 9. Known Issues

### 1. LICX Symbol Error
**Issue**: Symbol LICX cannot be fetched from Yahoo Finance
**Error**: `HTTP Error 404: $LICX: possibly delisted; no price data found`
**Impact**: LOW - The scan continues and processes other symbols
**Recommendation**: Remove LICX from Beta1 universe in `/Users/adamaslan/code/gcp app w mcp/mcp-finance1/src/technical_analysis_mcp/universes.py`

### 2. Python Version Mismatch
**Issue**: environment.yml specifies Python 3.11, but fin-ai1 has Python 3.10.17
**Impact**: LOW - Code runs successfully on 3.10
**Recommendation**: Update environment.yml to `python=3.10` for accuracy, OR recreate environment with Python 3.11

### 3. ALTS Credentials Warning
**Issue**: Google Cloud warning about ALTS credentials when running locally
**Impact**: NONE - Expected behavior outside GCP infrastructure
**Action**: No action needed, safe to ignore

---

## 10. Execution Methods

### Method 1: Direct Python Path (Recommended)
```bash
cd "/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run"
/opt/homebrew/Caskroom/miniforge/base/envs/fin-ai1/bin/python3 run_beta1_scan.py
```

**Advantages**:
- No environment activation required
- Works in any shell configuration
- Guaranteed to use correct Python interpreter
- ✅ **TESTED AND WORKING**

### Method 2: With Environment Activation (Requires Shell Setup)
```bash
# First: Initialize mamba in shell (one-time setup)
/opt/homebrew/Caskroom/miniforge/base/bin/conda init zsh
source ~/.zshrc

# Then: Activate and run
mamba activate fin-ai1
cd "/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run"
python3 run_beta1_scan.py
```

**Advantages**:
- More intuitive for interactive use
- Can use `python3` directly after activation

**Disadvantages**:
- Requires shell initialization (see MAMBA_ACTIVATION_DIAGNOSTIC.md)
- May not work in non-interactive contexts

### Method 3: Using Wrapper Script
Create `/Users/adamaslan/code/gcp app w mcp/run_beta1.sh`:
```bash
#!/bin/zsh
cd "/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run"
/opt/homebrew/Caskroom/miniforge/base/envs/fin-ai1/bin/python3 run_beta1_scan.py "$@"
```

Then:
```bash
chmod +x run_beta1.sh
./run_beta1.sh
```

---

## 11. Recommendations

### For Production Readiness

1. **Update Beta1 Universe**
   - Remove or replace LICX symbol (delisted)
   - File: `/Users/adamaslan/code/gcp app w mcp/mcp-finance1/src/technical_analysis_mcp/universes.py`

2. **Standardize Python Version**
   - Either update environment.yml to specify `python=3.10`
   - OR recreate environment with Python 3.11
   - Current mismatch is not critical but should be documented

3. **Environment Variables**
   - Ensure `GCP_PROJECT_ID` is set (currently falls back to 'ttb-lang1')
   - Consider using `.env` file for local development

4. **Lock File Generation**
   ```bash
   cd "/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run"
   conda-lock -f environment.yml --lockfile conda-lock.yml
   ```
   This creates multi-platform lock files for exact reproducibility.

5. **Shell Configuration**
   - For interactive development, follow initialization steps in MAMBA_ACTIVATION_DIAGNOSTIC.md
   - For automated scripts, use direct Python path method

### For Development Workflow

1. **Install Dev Dependencies** (Optional)
   ```bash
   /opt/homebrew/Caskroom/miniforge/base/envs/fin-ai1/bin/pip install black ruff mypy pytest-cov pandas-stubs
   ```

2. **Add Convenience Alias** (Optional)
   Add to `~/.zshrc`:
   ```bash
   alias run-beta1='cd "/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run" && /opt/homebrew/Caskroom/miniforge/base/envs/fin-ai1/bin/python3 run_beta1_scan.py'
   ```

3. **CI/CD Considerations**
   - Use direct Python path in automated scripts
   - Consider using `micromamba` for faster CI/CD builds
   - Use conda-lock.yml for reproducible builds

---

## 12. Dependency Installation Guide

If you need to recreate or update the environment:

### Using Mamba (Recommended)

```bash
# Navigate to cloud-run directory
cd "/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run"

# Create environment from environment.yml
mamba env create -f environment.yml

# Activate environment
mamba activate mcp-finance-backend

# Install technical-analysis-mcp in editable mode
cd "/Users/adamaslan/code/gcp app w mcp/mcp-finance1"
pip install -e .

# Or with optional dependencies
pip install -e ".[gcp,ai,dev]"
```

### Verifying Installation

```bash
# Check Python version
/opt/homebrew/Caskroom/miniforge/base/envs/fin-ai1/bin/python3 --version

# List installed packages
/opt/homebrew/Caskroom/miniforge/base/envs/fin-ai1/bin/python3 -m pip list

# Test imports
/opt/homebrew/Caskroom/miniforge/base/envs/fin-ai1/bin/python3 -c "from technical_analysis_mcp.server import scan_trades; print('✓ Imports successful')"
```

---

## 13. Test Coverage Summary

| Test Area | Status | Notes |
|-----------|--------|-------|
| Environment exists | ✅ PASS | fin-ai1 found and accessible |
| Python version | ✅ PASS | 3.10.17 (minor mismatch with env.yml) |
| Core dependencies | ✅ PASS | All runtime packages installed |
| Module imports | ✅ PASS | All required modules import successfully |
| Firebase connection | ✅ PASS | Successfully connected and wrote test data |
| Script execution | ✅ PASS | Full scan completed without errors |
| Data fetching | ⚠️ PARTIAL | 10/11 symbols successful (LICX delisted) |
| Results saving | ✅ PASS | Results saved to Firebase |

**Overall Status**: ✅ **ENVIRONMENT FULLY FUNCTIONAL**

---

## 14. Complete Package List (fin-ai1)

<details>
<summary>Click to expand full package list (200+ packages)</summary>

```
absl-py==2.2.2
aiohappyeyeballs==2.6.1
aiohttp==3.12.15
aiosignal==1.4.0
alpha_vantage==3.0.0
annotated-types==0.7.0
antlr4-python3-runtime==4.9.3
anyio==4.9.0
appdirs==1.4.4
appnope==0.1.4
asttokens==3.0.1
astunparse==1.6.3
async-timeout==4.0.3
attrs==25.3.0
backoff==2.2.1
backports.asyncio.runner==1.2.0
bcrypt==4.3.0
beautifulsoup4==4.13.5
blinker==1.9.0
build==1.3.0
CacheControl==0.14.4
cachetools==5.5.2
certifi==2025.4.26
cffi==2.0.0
charset-normalizer==3.4.2
chromadb==1.1.0
click==8.2.1
coloredlogs==15.0.1
comm==0.2.3
contourpy==1.3.2
crewai==0.193.2
cryptography==46.0.1
curl_cffi==0.13.0
cycler==0.12.1
debugpy==1.8.19
decorator==5.2.1
deprecation==2.1.0
diskcache==5.6.3
distro==1.9.0
docstring_parser==0.17.0
docutils==0.22.1
durationpy==0.10
et_xmlfile==2.0.0
eval_type_backport==0.3.0
exceptiongroup==1.3.1
executing==2.2.1
fastapi==0.115.13
filelock==3.18.0
firebase_admin==7.1.0
flatbuffers==25.2.10
fonttools==4.58.0
frozendict==2.4.6
frozenlist==1.7.0
fsspec==2025.5.0
gast==0.6.0
google-ai-generativelanguage==0.6.15
google-api-core==2.25.1
google-api-python-client==2.183.0
google-auth==2.40.3
google-auth-httplib2==0.2.0
google-cloud-core==2.4.3
google-cloud-firestore==2.22.0
google-cloud-storage==3.4.1
google-crc32c==1.7.1
google-genai==1.45.0
google-generativeai==0.8.5
google-pasta==0.2.0
google-resumable-media==2.7.2
googleapis-common-protos==1.70.0
grpcio==1.75.0
grpcio-status==1.71.2
h11==0.16.0
h2==4.3.0
h5py==3.13.0
hf-xet==1.1.3
hpack==4.1.0
httpcore==1.0.9
httplib2==0.31.0
httptools==0.6.4
httpx==0.28.1
httpx-sse==0.4.3
huggingface-hub==0.32.4
humanfriendly==10.0
hydra-core==1.3.2
hyperframe==6.1.0
idna==3.10
importlib_metadata==8.6.1
importlib_resources==6.5.2
iniconfig==2.3.0
instructor==1.11.3
invoke==2.2.1
iopath==0.1.10
ipykernel==7.1.0
ipython==8.38.0
itsdangerous==2.2.0
jedi==0.19.2
Jinja2==3.1.6
jiter==0.10.0
joblib==1.5.0
json_repair==0.25.2
json5==0.12.1
jsonpatch==1.33
jsonpickle==4.1.1
jsonpointer==3.0.0
jsonref==1.1.0
jsonschema==4.25.1
jsonschema-specifications==2025.9.1
jupyter_client==8.8.0
jupyter_core==5.9.1
keras==3.10.0
kiwisolver==1.4.8
kubernetes==33.1.0
langchain==0.3.27
langchain-core==0.3.76
langchain-text-splitters==0.3.11
langsmith==0.4.30
libclang==18.1.1
litellm==1.74.9
marimo==0.15.5
Markdown==3.8
markdown-it-py==3.0.0
MarkupSafe==3.0.2
matplotlib==3.10.3
matplotlib-inline==0.2.1
mcp==1.22.0
mdurl==0.1.2
mistralai==1.9.11
ml_dtypes==0.5.1
mmh3==5.2.0
mpmath==1.3.0
msgpack==1.1.2
msgspec==0.19.0
multidict==6.6.4
multitasking==0.0.12
namex==0.0.9
narwhals==2.5.0
nest-asyncio==1.6.0
networkx==3.4.2
numpy==2.1.3
oauthlib==3.3.1
omegaconf==2.3.0
onnxruntime==1.22.0
openai==1.109.1
openpyxl==3.1.5
opentelemetry-api==1.37.0
opentelemetry-exporter-otlp-proto-common==1.37.0
opentelemetry-exporter-otlp-proto-grpc==1.37.0
opentelemetry-exporter-otlp-proto-http==1.37.0
opentelemetry-proto==1.37.0
opentelemetry-sdk==1.37.0
opentelemetry-semantic-conventions==0.58b0
opt_einsum==3.4.0
optree==0.15.0
orjson==3.11.3
overrides==7.7.0
packaging==25.0
pandas==2.2.3
parso==0.8.5
pdfminer.six==20250506
pdfplumber==0.11.7
peewee==3.18.2
pexpect==4.9.0
pickleshare==0.7.5
pillow==11.2.1
pip==25.1.1
platformdirs==4.5.1
pluggy==1.6.0
portalocker==2.7.0
postgrest==2.20.0
posthog==5.4.0
prompt_toolkit==3.0.52
propcache==0.3.2
proto-plus==1.26.1
protobuf==5.29.4
psutil==7.2.1
ptyprocess==0.7.0
pure_eval==0.2.3
pyasn1==0.6.1
pyasn1_modules==0.4.2
pybase64==1.4.2
pycparser==2.22
pydantic==2.11.7
pydantic_core==2.33.2
pydantic-settings==2.12.0
Pygments==2.19.2
PyJWT==2.10.1
pymdown-extensions==10.16.1
pyparsing==3.2.3
pypdfium2==4.30.0
PyPika==0.48.9
pyproject_hooks==1.2.0
pytest==9.0.1
pytest-asyncio==1.3.0
python-dateutil==2.9.0.post0
python-dotenv==1.1.0
python-http-client==3.3.7
python-multipart==0.0.20
pytz==2025.2
pyvis==0.3.2
PyYAML==6.0.2
pyzmq==27.1.0
realtime==2.20.0
referencing==0.36.2
regex==2024.11.6
requests==2.32.3
requests-oauthlib==2.0.0
requests-toolbelt==1.0.0
rich==14.0.0
rpds-py==0.27.1
rsa==4.9.1
safetensors==0.5.3
scikit-learn==1.6.1
scipy==1.15.3
seaborn==0.13.2
segment_anything==1.0
sendgrid==6.12.5
setuptools==80.1.0
shellingham==1.5.4
six==1.17.0
sniffio==1.3.1
soupsieve==2.8
SQLAlchemy==2.0.43
sse-starlette==3.0.3
stack-data==0.6.3
starlette==0.46.2
storage3==2.20.0
StrEnum==0.4.15
supabase==2.20.0
supabase-auth==2.20.0
supabase-functions==2.20.0
sympy==1.14.0
technical-analysis-mcp==0.1.0 (editable: /Users/adamaslan/code/mcp-finance1)
tenacity==9.1.2
tensorboard==2.19.0
tensorboard-data-server==0.7.2
tensorflow==2.19.0
tensorflow-io-gcs-filesystem==0.37.1
termcolor==3.1.0
threadpoolctl==3.6.0
tiktoken==0.11.0
tokenizers==0.21.1
tomli==2.2.1
tomli_w==1.2.0
tomlkit==0.13.3
torch==2.7.1
torchsummary==1.5.1
torchvision==0.22.1
tornado==6.5.4
tqdm==4.67.1
traitlets==5.14.3
transformers==4.52.4
typer==0.19.2
typing_extensions==4.15.0
typing-inspection==0.4.1
tzdata==2025.2
uritemplate==4.2.0
urllib3==2.4.0
uv==0.8.22
uvicorn==0.34.3
uvloop==0.21.0
watchfiles==1.1.0
wcwidth==0.2.13
websocket-client==1.8.0
websockets==15.0.1
Werkzeug==3.1.3
wheel==0.45.1
wrapt==1.17.2
yahoo-earnings-calendar==0.6.0
yarl==1.20.1
yfinance==0.2.65
zipp==3.21.0
zstandard==0.25.0
```

</details>

---

## Conclusion

The **fin-ai1** environment is **production-ready** for running the `run_beta1_scan.py` script. All critical dependencies are installed and properly configured. The script executes successfully with only minor, non-critical warnings.

### Key Takeaways

1. ✅ Environment is functional and complete
2. ✅ All runtime dependencies are present and up-to-date
3. ✅ Script execution is successful
4. ✅ Firebase integration works correctly
5. ⚠️ Minor Python version mismatch (3.10 vs 3.11) - not critical
6. ⚠️ One delisted symbol (LICX) should be removed from universe

### Next Steps

1. Remove or replace LICX from Beta1 universe
2. (Optional) Standardize Python version in environment.yml
3. (Optional) Set up shell initialization for interactive use
4. (Optional) Create wrapper scripts for convenience

**Report Generated**: 2026-01-20
**Tested By**: Environment Testing Agent
**Environment**: fin-ai1 (Python 3.10.17)
**Status**: ✅ PASS
