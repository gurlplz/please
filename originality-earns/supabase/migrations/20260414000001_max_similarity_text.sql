-- Allow max_phrase_similarity to accept pgvector literals as text (Supabase JS friendly)
drop function if exists public.max_phrase_similarity(vector, timestamptz);
drop function if exists public.max_phrase_similarity(text, timestamptz);

create or replace function public.max_phrase_similarity(
  query_embedding text,
  since timestamptz
)
returns numeric
language sql
stable
as $$
  select coalesce(
    max(1 - (ph.embedding <=> query_embedding::vector)),
    0::numeric
  )
  from public.phrase_history ph
  where ph.first_seen >= since;
$$;
