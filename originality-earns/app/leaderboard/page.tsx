import { createClient } from "@supabase/supabase-js";
import { LeaderboardTable, type LeaderboardRow } from "@/components/leaderboard-table";

async function loadInitialLeaderboard(): Promise<LeaderboardRow[]> {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return [];

  const supabase = createClient(url, key);
  const { data, error } = await supabase
    .from("creators")
    .select("author_handle,total_originality_score,phrases_coined,last_phrase,updated_at")
    .order("total_originality_score", { ascending: false })
    .limit(100);

  if (error || !data) return [];

  return data.map((row, idx) => ({
    rank: idx + 1,
    author_handle: row.author_handle,
    total_originality_score: Number(row.total_originality_score),
    phrases_coined: Number(row.phrases_coined),
    last_phrase: row.last_phrase,
    updated_at: row.updated_at
  }));
}

export default async function LeaderboardPage() {
  const initialRows = await loadInitialLeaderboard();

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-12">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Leaderboard</h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Live rankings powered by Supabase Realtime on the `creators` rollup table. Each novel phrase updates
          totals immediately after insertion into `phrase_history`.
        </p>
      </div>
      <LeaderboardTable initialRows={initialRows} />
    </div>
  );
}
