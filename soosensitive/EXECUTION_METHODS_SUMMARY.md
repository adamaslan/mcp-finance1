# Beta1 Scan Execution Methods - Quick Reference

**Date**: 2026-01-20
**Status**: ✅ All methods implemented

---

## 🎯 Recommended Methods (In Priority Order)

### 1. ⭐ Makefile Method (BEST FOR MOST USERS)

```bash
cd "/Users/adamaslan/code/gcp app w mcp"
make beta1-scan
```

**Why this is best**:
- ✅ Fast (uses direct Python path - no activation overhead)
- ✅ Reliable (tested and verified working)
- ✅ Self-documenting (`make help` to see all commands)
- ✅ Team-friendly (committed to git)
- ✅ Multiple useful commands included

**Other useful commands**:
```bash
make verify-env    # Check environment setup
make test-python   # Test Python imports
make help          # See all available commands
```

---

### 2. 🚀 Direct Python Method (BEST FOR AUTOMATION)

```bash
cd "/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run"
/opt/homebrew/Caskroom/miniforge/base/envs/fin-ai1/bin/python3 run_beta1_scan.py
```

**Why this is best for automation**:
- ✅ Fastest (no initialization overhead)
- ✅ Most reliable (uses exact Python binary)
- ✅ Works in cron, CI/CD, and all contexts
- ✅ No shell dependencies

**Verified Working**:
- ✅ Python 3.10.17 from fin-ai1 environment
- ✅ All required packages available
- ✅ pandas 2.2.3, numpy 2.1.3, yfinance 0.2.65

---

### 3. 💻 zsh Function (MOST CONVENIENT)

**Setup** (one-time): Add to `~/.zshrc`:

```zsh
run-beta1() {
    local script_dir="/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run"
    local python_bin="/opt/homebrew/Caskroom/miniforge/base/envs/fin-ai1/bin/python3"
    cd "$script_dir" && "$python_bin" run_beta1_scan.py "$@"
}
```

Then: `source ~/.zshrc`

**Usage**:
```bash
run-beta1    # From anywhere!
```

**Why this is most convenient**:
- ✅ Run from any directory
- ✅ Short command to type
- ✅ Fast (no activation overhead)

---

### 4. 📜 Activation Script (ALTERNATIVE)

```bash
cd "/Users/adamaslan/code/gcp app w mcp"
./activate_and_run.sh
```

**Note**: This method has an issue with environment activation not working as expected. It activates the environment but doesn't switch Python versions correctly. **Use Makefile or Direct Python method instead.**

---

## 📊 Quick Comparison

| Method | Speed | Setup | Recommended For |
|--------|-------|-------|-----------------|
| **Makefile** | ⚡⚡⚡⚡ | ✅ Done | Most users, teams |
| **Direct Python** | ⚡⚡⚡⚡⚡ | ✅ Done | Automation, cron |
| **zsh Function** | ⚡⚡⚡⚡⚡ | Manual | Personal convenience |
| **Activation Script** | ⚡⚡⚡ | ✅ Done | Not recommended* |

*Activation script has environment switching issues

---

## 🔧 Troubleshooting

### Verify Everything Works

```bash
cd "/Users/adamaslan/code/gcp app w mcp"
make verify-env    # Check setup
make test-python   # Test imports
```

### Import Errors

If you see "No module named 'X'", the environment may not have the package:

```bash
# Check what's installed
/opt/homebrew/Caskroom/miniforge/base/envs/fin-ai1/bin/python3 -m pip list

# Or use Makefile
make test-python
```

### Firebase Errors

```bash
# Authenticate with gcloud
gcloud auth application-default login

# Set project ID
export GCP_PROJECT_ID=ttb-lang1

# Check configuration
make check-firestore
```

---

## 📝 Full Documentation

For complete details, see: `/Users/adamaslan/code/gcp app w mcp/SCRIPT_EXECUTION_REPORT.md`

---

## ⚡ Quick Start

**First Time Setup**:
```bash
cd "/Users/adamaslan/code/gcp app w mcp"
make verify-env
make test-python
```

**Run the Scan**:
```bash
make beta1-scan
```

**That's it!** 🎉

---

**Last Updated**: 2026-01-20
