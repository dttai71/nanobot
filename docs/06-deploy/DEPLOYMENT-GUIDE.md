# Deployment Guide — Nanobot

**Date**: February 16, 2026
**Stage**: 06 - DEPLOY

---

## Deployment Options

### 1. PyPI (Recommended for users)

```bash
pip install nanobot-ai
# or with uv
uv tool install nanobot-ai
```

### 2. From Source (Development)

```bash
git clone https://github.com/HKUDS/nanobot.git
cd nanobot
pip install -e ".[dev]"
```

### 3. Docker

```bash
docker build -t nanobot .
docker run -v ~/.nanobot:/root/.nanobot nanobot onboard
docker run -v ~/.nanobot:/root/.nanobot nanobot agent -m "Hello"
```

## First-Time Setup

```bash
nanobot onboard
# Follow prompts to configure LLM provider API keys
# Config saved to ~/.nanobot/config.json
```

## Running Modes

| Mode | Command | Use Case |
|------|---------|----------|
| Single message | `nanobot agent -m "Hello"` | Quick interaction |
| Interactive chat | `nanobot agent` | Terminal chat session |
| Multi-channel gateway | `nanobot gateway` | Telegram, Discord, Slack, etc. |
| Status check | `nanobot status` | Verify configuration |

## Configuration

Config file: `~/.nanobot/config.json`

Key sections: providers (API keys), channels (platform tokens), tools (MCP servers, workspace restrictions), agents (model, temperature).

See `nanobot/config/schema.py` for full schema reference.

## Release Process

1. Update version in `pyproject.toml`
2. Run tests: `pytest tests/`
3. Run lint: `ruff check nanobot/`
4. Build: `python -m build`
5. Publish: `twine upload dist/*`
