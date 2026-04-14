"use client";

import { useEffect, useState } from "react";
import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

export type LeaderboardRow = {
  rank: number;
  author_handle: string;
  total_originality_score: number;
  phrases_coined: number;
  last_phrase: string | null;
  updated_at: string;
};

export function LeaderboardTable({ initialRows }: { initialRows: LeaderboardRow[] }) {
  const [rows, setRows] = useState<LeaderboardRow[]>(initialRows);
  const [supabase, setSupabase] = useState<SupabaseClient | null>(null);

  useEffect(() => {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    if (!url || !key) return;

    const client = createBrowserClient(url, key);
    setSupabase(client);
  }, []);

  useEffect(() => {
    if (!supabase) return;

    const channel = supabase
      .channel("creators-leaderboard")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "creators" },
        async () => {
          const { data, error } = await supabase
            .from("creators")
            .select("author_handle,total_originality_score,phrases_coined,last_phrase,updated_at")
            .order("total_originality_score", { ascending: false })
            .limit(100);

          if (error || !data) return;

          const next: LeaderboardRow[] = data.map((row, idx) => ({
            rank: idx + 1,
            author_handle: row.author_handle,
            total_originality_score: Number(row.total_originality_score),
            phrases_coined: Number(row.phrases_coined),
            last_phrase: row.last_phrase,
            updated_at: row.updated_at
          }));

          setRows(next);
        }
      )
      .subscribe();

    return () => {
      void supabase.removeChannel(channel);
    };
  }, [supabase]);

  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="w-full min-w-[720px] text-sm">
        <thead className="bg-muted/40 text-left text-xs uppercase tracking-wide text-muted-foreground">
          <tr>
            <th className="px-4 py-3 font-medium">Rank</th>
            <th className="px-4 py-3 font-medium">Creator</th>
            <th className="px-4 py-3 font-medium">Score</th>
            <th className="px-4 py-3 font-medium">Phrases</th>
            <th className="px-4 py-3 font-medium">Last phrase</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={5} className="px-4 py-10 text-center text-muted-foreground">
                No creators yet. Start the ingestion worker to populate scores.
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={`${row.rank}-${row.author_handle}`} className="border-t">
                <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{row.rank}</td>
                <td className="px-4 py-3 font-medium">@{row.author_handle}</td>
                <td className="px-4 py-3">{row.total_originality_score.toFixed(3)}</td>
                <td className="px-4 py-3">{row.phrases_coined}</td>
                <td className="px-4 py-3 text-muted-foreground">
                  {row.last_phrase ? `“${row.last_phrase}”` : "—"}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
