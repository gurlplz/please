# Originality Earns

Real-time semantic novelty scoring for X (Twitter) posts with a Supabase-backed leaderboard and Base-native $ORIGIN rewards.

## What ships in this MVP

- **Ingestion**: TwitterAPI.io WebSocket worker (`scripts/twitter-stream.mjs`) plus REST batch cron (`POST /api/ingest/batch`).
- **NLP**: `compromise`-powered candidate phrases (3–8 tokens) with lightweight cleanup.
- **Embeddings**: `Xenova/bge-m3` via `@xenova/transformers` (server-side).
- **Corpus search**: Supabase `pgvector` + `max_phrase_similarity` RPC over a rolling **90-day** window.
- **Human filter**: Originality.ai scan (`ORIGINALITY_AI_KEY`).
- **Leaderboard**: Next.js page + Supabase Realtime on `creators`.
- **Contracts (Foundry)**: `OriginToken` ($ORIGIN) + `RewardDistributor` (`distribute` for weekly pushes, `setWeeklyClaims` + `claim` for pull-based payouts).
- **Dashboard**: wagmi wallet connect + Server Actions for profile linking + on-chain `claim`.

## Prerequisites

- Node.js **20+**
- Supabase CLI (`supabase`) for local Postgres + Realtime
- Foundry (`forge`, `cast`) for smart contracts (install from https://book.getfoundry.sh)

## Local development

### 1) Supabase

```bash
cd originality-earns
supabase start
supabase db reset
```

Apply migrations from `supabase/migrations` (the reset command runs them automatically).

Copy `.env.example` → `.env.local` and fill in Supabase keys from `supabase status`.

### 2) Smart contracts

```bash
cd contracts
forge install --no-git OpenZeppelin/openzeppelin-contracts@v5.3.0 foundry-rs/forge-std@v1.11.0
forge build
forge test
```

`contracts/lib/` is gitignored; run `forge install` once per clone so remappings resolve.

### 3) Next.js

```bash
cd originality-earns
npm install
npm run dev
```

### 4) Stream tweets (optional)

Configure **active** filter rules in the TwitterAPI.io dashboard, then:

```bash
TWITTERAPI_IO_KEY=... CRON_SECRET=... NEXT_URL=http://localhost:3000 node ./scripts/twitter-stream.mjs
```

## API routes (cron / workers)

All privileged routes expect:

`Authorization: Bearer $CRON_SECRET`

- `POST /api/ingest/tweet` — process a single normalized tweet payload.
- `POST /api/ingest/batch` — REST poll + phrase scoring (`query` optional; defaults to English minus replies/retweets).
- `POST /api/cron/weekly-airdrop` — builds a `distribute` calldata payload from linked wallets + top creators (does not broadcast txs in MVP).

## Deploying contracts to Base

1. Export `PRIVATE_KEY`, `BASE_RPC_URL`, and (for testnet) `BASE_SEPOLIA_RPC_URL`.
2. `cd contracts && forge script script/Deploy.s.sol --rpc-url base --broadcast`
3. Paste deployed addresses into `.env` / Vercel:

- `NEXT_PUBLIC_ORIGIN_TOKEN_ADDRESS`
- `NEXT_PUBLIC_REWARD_DISTRIBUTOR_ADDRESS`

Fund the distributor with $ORIGIN, then call `distribute` from the owner wallet each week (or use `setWeeklyClaims` + `claim` for pull-based payouts).

## API keys

- **TwitterAPI.io**: dashboard API key (`TWITTERAPI_IO_KEY`). Create WebSocket filter rules before streaming.
- **Originality.ai**: API key (`ORIGINALITY_AI_KEY`). If responses differ by version, adjust `lib/originality-ai.ts`.
- **Supabase**: project URL + anon key for the browser; service role key for ingestion (server-only).

## Vercel + Supabase notes

- Deploy the Next.js app to Vercel and set the same environment variables as `.env.example`.
- Run Supabase migrations against the hosted database (`supabase db push` or SQL editor).
- Prefer a **queue** (Inngest, Cloud Tasks, etc.) instead of long WebSocket processes on Vercel serverless. This repo uses a Node worker script for streaming and cron routes for batching.

## Security notes (read before mainnet)

- Wallet ↔ handle linking is **trusted** in the MVP (no cryptographic proof of X ownership).
- `SUPABASE_SERVICE_ROLE_KEY` must never ship to the browser.
- Rotate `CRON_SECRET` if leaked.

## License

MIT
