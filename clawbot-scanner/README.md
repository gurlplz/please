# OpenClaw Insecure Instance Scanner

Custom crawler that discovers exposed OpenClaw (Clawbot) instances on the web **without** using Shodan, Censys, or other paid services.

## How It Works

1. **URL Discovery** (parallel custom crawlers):
   - **Platform enumeration**: Railway, Render, Fly.io, Vercel, Netlify, Heroku, ngrok, Replit, Glitch, Streamlit, Modal, Cloudflare Pages, Deno Deploy, AWS Amplify, Azure, Surge, GitHub/GitLab/Codeberg Pages, Koyeb, PythonAnywhere, CodeSandbox, StackBlitz, Observable, Gradio, Hugging Face Spaces
   - **Certificate Transparency**: crt.sh for openclaw/clawbot/claw-assistant domains
   - **GitHub**: Code + repo search (READMEs) for configs, deploy URLs
   - **Index sites**: Crawl OpenClaw directories (openclawdirectory.dev, awesome-openclaw, etc.)
   - **Zoomeye**: Shodan alternative - set ZOOMEYE_API_KEY (free tier)
   - **Community**: Reddit, Hacker News - extract URLs from discussions
   - **IP discovery**: Direct IP addresses via `--ip-file` or `--fetch-cloud-ips` (AWS ranges)
   - **Custom**: `--wordlist`, `--url-file` for user-provided seeds

2. **Fingerprinting** (Shodan-style): favicon hash (mmh3), http.title, product (Server/X-Powered-By), http.html, API liveness

3. **Security assessment**: Flags instances with no auth or exposed API

4. **Enumeration**: `--enumerate` probes insecure instances for endpoints, config, title, headers

5. **Output**: JSONL (results) + enumerated.jsonl (from insecure instances)

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
| `--no-progress` | Disable progress bar |
| `--platforms` | Limit to specific platforms (e.g. railway render) |
| `--wordlist` | Custom subdomain wordlist file |
| `--url-file` | File with custom URLs to scan |
| `--ip-file` | File with IPs (expands to IP:3000,18789,8080,5000,80,443) |
| `--fetch-cloud-ips` | Fetch AWS IP ranges, sample & scan |
| `--enumerate` | Enumerate data from insecure instances after scan |
| `--enumerate-from` | Enumerate from existing results file (skip scan) |
| `--enum-output` | Output file for enumerated data |

## Ethics

- **Discovery only** – no exploitation, no unauthorized access
- Report findings to OpenClaw and instance operators
- Use for responsible disclosure and security research

## License

MIT
