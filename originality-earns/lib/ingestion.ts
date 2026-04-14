import "server-only";

import { embedText } from "@/lib/embeddings";
import { getServiceSupabase } from "@/lib/supabase";
import { extractCandidatePhrases } from "@/lib/phrases";
import { originalityHumanBonus } from "@/lib/originality-ai";
import type { NormalizedTweet } from "@/lib/twitter";

const NOVELTY_THRESHOLD = Number(process.env.NOVELTY_SIMILARITY_THRESHOLD ?? "0.85");
const HUMAN_FLOOR = Number(process.env.HUMAN_SCORE_FLOOR ?? "0.55");

function vectorLiteral(values: number[]): string {
  return `[${values.map((v) => Number(v).toFixed(8)).join(",")}]`;
}

function clamp01(n: number) {
  return Math.min(1, Math.max(0, n));
}

/**
 * End-to-end novelty pipeline for a single tweet.
 * Idempotent per (tweet_id, phrase) via unique index.
 */
export async function ingestTweetPhrases(tweet: NormalizedTweet): Promise<{
  stored: number;
  skipped: number;
}> {
  if (!tweet.authorId) {
    return { stored: 0, skipped: 0 };
  }

  const supabase = getServiceSupabase();
  const candidates = extractCandidatePhrases(tweet.text);
  if (!candidates.length) return { stored: 0, skipped: 0 };

  const since = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString();
  let stored = 0;
  let skipped = 0;

  for (const phrase of candidates) {
    const embedding = await embedText(phrase);
    const literal = vectorLiteral(embedding);

    const { data: simRaw, error: rpcError } = await supabase.rpc("max_phrase_similarity", {
      query_embedding: literal,
      since
    });

    if (rpcError) {
      // If RPC fails (e.g. migration not applied), fail loud in logs but keep worker alive
      console.error("max_phrase_similarity RPC failed:", rpcError.message);
      skipped += 1;
      continue;
    }

    const maxSimilarity = Number(simRaw ?? 0);
    if (maxSimilarity > NOVELTY_THRESHOLD) {
      skipped += 1;
      continue;
    }

    const novelty = clamp01(1 - maxSimilarity);
    const engagement = tweet.likeCount + tweet.retweetCount;
    const earlyVirality = Math.min(1, Math.log1p(engagement) / 8);

    let humanBonus: number;
    try {
      humanBonus = await originalityHumanBonus(phrase);
    } catch (e) {
      console.error("Originality.ai human check failed:", e);
      skipped += 1;
      continue;
    }

    if (humanBonus < HUMAN_FLOOR) {
      skipped += 1;
      continue;
    }

    const score = novelty * (1 + earlyVirality) * humanBonus;

    const { error: insertError } = await supabase.from("phrase_history").insert({
      phrase,
      embedding: literal,
      author_id: tweet.authorId,
      author_handle: tweet.authorHandle,
      tweet_id: tweet.id,
      first_seen: tweet.createdAt ? new Date(tweet.createdAt).toISOString() : undefined,
      score,
      human_score: humanBonus
    });

    if (insertError) {
      // Unique violation = already processed
      if (!insertError.message.includes("duplicate") && insertError.code !== "23505") {
        console.error("phrase_history insert failed:", insertError.message);
      }
      skipped += 1;
      continue;
    }

    stored += 1;
  }

  return { stored, skipped };
}
