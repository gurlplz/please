# AGENTS.md

## Cursor Cloud specific instructions

### Repository structure

This is a multi-branch repository where each branch contains an independent project. The `main` branch is a stub (`test.md` only). There is no monorepo tooling, shared build system, or CI/CD.

| Branch | Project | Stack | Run command |
|--------|---------|-------|-------------|
| `cursor/profile-picture-traits-5257` | Profile Picture Generator | JS/HTML/SVG | `npx serve -l 3000` |
| `cursor/replicated-pin-module-3dc1` | Replicated Pin Module | Node.js (CommonJS) | `node src/ReplicatedPinModule.test.js` |
| `cursor/income-generation-ideas-8952` | Clawbot Scanner | Python (async) | `python3 clawbot-scanner/main.py --help` |
| `cursor/income-generation-ideas-8952` | Money Law | Python/Streamlit | `streamlit run money-law/app.py --server.port 8501 --server.headless true` |
| `cursor/derc20-inflation-bug-8e5a` | DERC20 Inflation Bug PoC | Python | `python3 derc20-inflation-bug-proof/poc_inflation_compounding.py` |

### Working across branches

Use `git worktree` to test multiple branches simultaneously without switching context:

```bash
git worktree add /tmp/<name> <branch-name>
```

### Dependencies

- **Node.js**: Pre-installed via nvm. Used by Profile Picture Generator (`npx serve`) and Replicated Pin Module.
- **Python 3**: Pre-installed. Pip packages needed: `httpx`, `aiohttp`, `aiofiles`, `aiosqlite`, `tqdm`, `mmh3`, `streamlit`.
- `~/.local/bin` must be on `PATH` for `streamlit` CLI.

### Gotchas

- The Profile Picture Generator has no `node_modules` — it uses `npx serve` directly (no `npm install` needed).
- The Replicated Pin Module has zero external dependencies; tests run with plain `node`.
- The Clawbot Scanner requires network access to actually scan; use `--discovery-only` or `--limit 1` for quick local testing.
- Money Law Streamlit app: use `--server.headless true` to avoid browser-open prompt.
- DERC20 PoC is pure Python stdlib — no pip dependencies.
- The Foundry/Solidity PoC on the derc20 branch is optional; the Python PoC is self-contained.

### Lint / Test / Build

No shared lint or test infrastructure exists. Each project is standalone:

- **Replicated Pin Module**: `npm test` (runs `node src/ReplicatedPinModule.test.js`)
- **Other projects**: No formal test suites; verify by running the main entry point.
