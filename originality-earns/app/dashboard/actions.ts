"use server";

import "server-only";

import { z } from "zod";
import { getAddress, isAddress } from "viem";
import { getServiceSupabase } from "@/lib/supabase";

const LinkSchema = z.object({
  walletAddress: z.string(),
  authorHandle: z.string().min(1).max(64)
});

/**
 * Persists a wallet ↔ X handle mapping for leaderboard personalization.
 * MVP note: this does not prove X ownership — add SIWE + OAuth for production hardening.
 */
export async function linkCreatorProfile(input: z.infer<typeof LinkSchema>) {
  const parsed = LinkSchema.safeParse(input);
  if (!parsed.success) {
    return { ok: false as const, error: "Invalid input" };
  }

  if (!isAddress(parsed.data.walletAddress)) {
    return { ok: false as const, error: "Invalid wallet address" };
  }

  const wallet = getAddress(parsed.data.walletAddress).toLowerCase();
  const handle = parsed.data.authorHandle.replace(/^@/, "");

  const supabase = getServiceSupabase();
  const { error } = await supabase.from("dashboard_links").upsert(
    {
      wallet_address: wallet,
      author_handle: handle
    },
    { onConflict: "wallet_address" }
  );

  if (error) {
    console.error("linkCreatorProfile failed:", error.message);
    return { ok: false as const, error: error.message };
  }

  return { ok: true as const };
}

export async function loadCreatorDashboard(walletAddress: string) {
  if (!isAddress(walletAddress)) {
    return { ok: false as const, error: "Invalid wallet" };
  }

  const wallet = getAddress(walletAddress).toLowerCase();
  const supabase = getServiceSupabase();

  const { data: link, error: linkError } = await supabase
    .from("dashboard_links")
    .select("author_handle,author_id")
    .eq("wallet_address", wallet)
    .maybeSingle();

  if (linkError) {
    return { ok: false as const, error: linkError.message };
  }

  if (!link) {
    return { ok: true as const, linked: false as const };
  }

  const { data: creator, error: creatorError } = await supabase
    .from("creators")
    .select("author_handle,total_originality_score,phrases_coined,last_phrase,updated_at")
    .eq("author_handle", link.author_handle)
    .maybeSingle();

  if (creatorError) {
    return { ok: false as const, error: creatorError.message };
  }

  const score = Number(creator?.total_originality_score ?? 0);

  const { count: betterCreators } = await supabase
    .from("creators")
    .select("author_id", { count: "exact", head: true })
    .gt("total_originality_score", score);

  return {
    ok: true as const,
    linked: true as const,
    author_handle: link.author_handle,
    author_id: link.author_id,
    creator,
    rank: (betterCreators ?? 0) + 1
  };
}
