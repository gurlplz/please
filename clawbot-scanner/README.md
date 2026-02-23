# OpenClaw Insecure Instance Scanner

Custom crawler that discovers exposed OpenClaw (Clawbot) instances on the web **without** using Shodan, Censys, or other paid services.

## How It Works

1. **URL Discovery** (custom crawlers):
   - **Platform enumeration**: Generates candidate URLs from Railway, Render, Fly.io, Vercel, Heroku, etc.
   - **Certificate Transparency**: Queries crt.sh (free) for domains matching openclaw/clawbot
   - **GitHub**: Searches code for configs, docker-compose, deploy URLs

2. **Fingerprinting**: Fetches each URL and checks for OpenClaw signatures (content, headers)

3. **Output**: Writes matches to JSONL file

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Run full scan (all sources)
python main.py

# Discovery only (no HTTP scanning)
python main.py --discovery-only

# Use specific sources
python main.py --sources platforms ct

# With GitHub token (higher rate limits)
GITHUB_TOKEN=ghp_xxx python main.py
```

## Options

| Flag | Description |
|------|-------------|
| `--sources` | `platforms`, `ct`, `github` (default: all) |
| `--output`, `-o` | Output JSONL file |
| `--batch-size` | Concurrent requests (default: 50) |
| `--github-token` | GitHub token for 5k req/hr |
| `--discovery-only` | Only discover URLs, don't scan |
| `--limit` | Max URLs to scan (for testing) |

## Ethics

- **Discovery only** – no exploitation, no unauthorized access
- Report findings to OpenClaw and instance operators
- Use for responsible disclosure and security research

## License

MIT
