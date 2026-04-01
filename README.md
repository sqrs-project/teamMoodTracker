# Pre-push Hook Installation

This pre-push hook blocks `git push` if your code fails quality checks with **flake8**.

## 1. Add hook

```bash
mkdir -p .git/hooks
nano .git/hooks/pre-push
```
Paste:

```bash
#!/bin/bash

poetry run flake8 src/ || { echo "Fix flake8 issues"; exit 1; }

echo "All pre-push checks passed."
exit 0
```

## 2. Make it executable

```bash
chmod +x .git/hooks/pre-push
```
