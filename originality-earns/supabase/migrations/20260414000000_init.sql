-- Originality Earns — core schema (PostgreSQL + pgvector)
-- BGE-M3 embeddings are 1024-dimensional.

create extension if not exists "pgcrypto";
create extension if not exists "vector";

-- ---------------------------------------------------------------------------
-- Phrase ledger: first-seen novel phrases with embeddings for similarity search
-- ---------------------------------------------------------------------------
create table if not exists public.phrase_history (
  id uuid primary key default gen_random_uuid(),
  phrase text not null,
  embedding vector(1024) not null,
  author_id text not null,
  author_handle text not null,
  tweet_id text not null,
  first_seen timestamptz not null default now(),
  score numeric not null,
  human_score numeric,
  created_at timestamptz not null default now()
);

-- One row per (tweet, phrase) to avoid double-counting on retries
create unique index if not exists phrase_history_tweet_phrase_uidx
  on public.phrase_history (tweet_id, phrase);

create index if not exists phrase_history_author_idx
  on public.phrase_history (author_id);

create index if not exists phrase_history_first_seen_idx
  on public.phrase_history (first_seen desc);

-- HNSW index for fast cosine-similarity search over the rolling corpus window
create index if not exists phrase_history_embedding_hnsw
  on public.phrase_history
  using hnsw (embedding vector_cosine_ops);

-- ---------------------------------------------------------------------------
-- Creator rollups (Realtime-friendly): updated via trigger on new phrases
-- ---------------------------------------------------------------------------
create table if not exists public.creators (
  author_id text primary key,
  author_handle text not null,
  total_originality_score numeric not null default 0,
  phrases_coined bigint not null default 0,
  last_phrase text,
  updated_at timestamptz not null default now()
);

create index if not exists creators_score_idx
  on public.creators (total_originality_score desc);

-- Convenience view for ordered leaderboard + rank
create or replace view public.leaderboard_view as
select
  row_number() over (
    order by c.total_originality_score desc, c.phrases_coined desc, c.author_handle asc
  )::bigint as rank,
  c.author_id,
  c.author_handle,
  c.total_originality_score,
  c.phrases_coined,
  c.last_phrase,
  c.updated_at
from public.creators c;

-- ---------------------------------------------------------------------------
-- Weekly reward runs (owner-signed txs from off-chain cron for MVP)
-- ---------------------------------------------------------------------------
create table if not exists public.reward_runs (
  id uuid primary key default gen_random_uuid(),
  week_start date not null,
  chain_id integer not null,
  distributor_address text not null,
  token_address text not null,
  payload jsonb not null,
  tx_hash text,
  created_at timestamptz not null default now()
);

create index if not exists reward_runs_week_idx
  on public.reward_runs (week_start desc);

-- ---------------------------------------------------------------------------
-- Trigger: keep creator rollups in sync for live leaderboard subscriptions
-- ---------------------------------------------------------------------------
create or replace function public.apply_phrase_to_creator_stats()
returns trigger
language plpgsql
as $$
begin
  insert into public.creators (
    author_id,
    author_handle,
    total_originality_score,
    phrases_coined,
    last_phrase,
    updated_at
  )
  values (
    new.author_id,
    new.author_handle,
    new.score,
    1,
    new.phrase,
    now()
  )
  on conflict (author_id) do update
    set author_handle = excluded.author_handle,
        total_originality_score = public.creators.total_originality_score + excluded.total_originality_score,
        phrases_coined = public.creators.phrases_coined + 1,
        last_phrase = excluded.last_phrase,
        updated_at = now();

  return new;
end;
$$;

drop trigger if exists trg_phrase_history_creator_stats on public.phrase_history;
create trigger trg_phrase_history_creator_stats
after insert on public.phrase_history
for each row
execute procedure public.apply_phrase_to_creator_stats();

-- ---------------------------------------------------------------------------
-- RPC: max cosine similarity vs corpus in last 90 days (for novelty gating)
-- Cosine similarity = 1 - cosine_distance under vector_cosine_ops
-- ---------------------------------------------------------------------------
create or replace function public.max_phrase_similarity(
  query_embedding vector(1024),
  since timestamptz
)
returns numeric
language sql
stable
as $$
  select coalesce(
    max(1 - (ph.embedding <=> query_embedding)),
    0::numeric
  )
  from public.phrase_history ph
  where ph.first_seen >= since;
$$;

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------
alter table public.phrase_history enable row level security;
alter table public.creators enable row level security;
alter table public.reward_runs enable row level security;

-- Public read for leaderboard surfaces (anon + authenticated)
create policy "phrase_history_select_public"
  on public.phrase_history
  for select
  to anon, authenticated
  using (true);

create policy "creators_select_public"
  on public.creators
  for select
  to anon, authenticated
  using (true);

create policy "reward_runs_select_public"
  on public.reward_runs
  for select
  to anon, authenticated
  using (true);

-- Optional wallet ↔ creator linkage for the dashboard (server-side writes only)
create table if not exists public.dashboard_links (
  wallet_address text primary key,
  author_handle text not null,
  author_id text,
  created_at timestamptz not null default now()
);

alter table public.dashboard_links enable row level security;

-- Writes are expected via service role (server-side) — no insert policies for anon

-- ---------------------------------------------------------------------------
-- Realtime: replicate creator + phrase inserts to listeners
-- (Safe if tables are already part of the publication.)
-- ---------------------------------------------------------------------------
do $$
begin
  begin
    execute 'alter publication supabase_realtime add table public.creators';
  exception
    when duplicate_object then null;
  end;

  begin
    execute 'alter publication supabase_realtime add table public.phrase_history';
  exception
    when duplicate_object then null;
  end;
end;
$$;
