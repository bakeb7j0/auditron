# Seed Prompt

This repository uses the **mash-it workflow** to apply all file changes.

## Workflow Rules
- **Repo-root only**: Scripts must refuse to run unless executed at `git rev-parse --show-toplevel`.
- **Preflight before writes**: Verify repo root before touching files.
- **Ignore the tool**: Ensure `.gitignore` contains `mash-it.sh`.
- **Plain heredocs only**: No encoding, no base64/gzip.
- **One prompt per file**: Each file written by a dedicated heredoc.
- **README.md auto-lists prompt files**.
- **Commit style**: `git add -A && git commit -s -m "<message>"`.

## Delivery of mash-it
Every mash-it script must be delivered:
1. Full `mash-it.sh` in chat.  
2. Paste-once one-liner in Canvas.  
3. As a downloadable file.  

Invocation:
```bash
cd ~/sandbox/github/myrepo && ./mash-it.sh
```

## Absolutes
- Never use placeholders or fake content.  
- No directory guessing.  
- Refuse if not at repo root.  

## Engineering Standards
- **All changes must pass linters and type checkers**: Ruff, Black, isort, Flake8, Pylint, Pyright.  
- **All changes must pass unit + integration tests** in the CI pipeline.  
- **Every commit must run cleanly with `pre-commit run --all-files` before push**.  
- **Follow GitHub flow branching model**:
  - `feature/*` branches fork from `release/*`.  
  - `release/*` branches fork from `main`.  
- Code must be **self-contained, readable, and maintainable**.

