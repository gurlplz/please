"""Configuration for OpenClaw scanner."""

# OpenClaw fingerprints - used to identify instances (Shodan-style)
FINGERPRINTS = {
    "content": ["openclaw", "clawbot", "clawctl", "control-ui", "gateway"],
    "paths": ["/", "/v1/chat/completions", "/v1/responses", "/openclaw"],
    "headers": ["x-openclaw", "x-clawbot"],
    # Product names in Server, X-Powered-By, etc.
    "product": ["openclaw", "clawbot", "clawctl", "moltbot"],
}

# Shodan-style favicon hashes (mmh3 of base64 favicon)
# Computed from learn.openclaw.academy, openclaw.academy
FAVICON_HASHES = [-318086011]

# Default ports OpenClaw runs on
DEFAULT_PORTS = [3000, 18789, 8080, 5000]

# Platform subdomain patterns for enumeration
PLATFORMS = {
    "railway": "*.railway.app",
    "render": "*.onrender.com",
    "fly": "*.fly.dev",
    "vercel": "*.vercel.app",
    "heroku": "*.herokuapp.com",
    "cloudflare": "*.trycloudflare.com",
    "ngrok": "*.ngrok-free.app",
}

# HTTP client settings
REQUEST_TIMEOUT = 10
MAX_CONCURRENT = 50
RATE_LIMIT_DELAY = 0.5  # seconds between requests per domain

# Output
RESULTS_FILE = "results.jsonl"
