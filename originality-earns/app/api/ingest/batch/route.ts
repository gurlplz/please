import { NextResponse } from "next/server";
import { z } from "zod";
import { fetchRecentTweets } from "@/lib/twitter-rest";
import { shouldProcessTweet, parseTweetPayload } from "@/lib/twitter";
import { ingestTweetPhrases } from "@/lib/ingestion";

function assertCronAuth(req: Request) {
  const secret = process.env.CRON_SECRET;
  if (!secret) {
    throw new Error("CRON_SECRET is not configured");
  }
  const header = req.headers.get("authorization");
  const token = header?.startsWith("Bearer ") ? header.slice("Bearer ".length) : null;
  if (token !== secret) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  return null;
}

const BodySchema = z
  .object({
    query: z.string().optional(),
    rawTweets: z.array(z.unknown()).optional()
  })
  .default({});

/**
 * Cron-friendly batch processor: REST poll + optional raw tweet array.
 */
export async function POST(req: Request) {
  const unauthorized = assertCronAuth(req);
  if (unauthorized) return unauthorized;

  const json: unknown = await req.json().catch(() => ({}));
  const body = BodySchema.parse(json);

  let processed = 0;
  let stored = 0;
  let skipped = 0;

  const tweets =
    body.rawTweets?.flatMap((raw) => parseTweetPayload({ tweets: [raw] })) ??
    (await fetchRecentTweets(body.query ?? "lang:en -is:retweet -is:reply"));

  for (const tweet of tweets) {
    if (!shouldProcessTweet(tweet, tweet)) {
      skipped += 1;
      continue;
    }
    processed += 1;
    const res = await ingestTweetPhrases(tweet);
    stored += res.stored;
    skipped += res.skipped;
  }

  return NextResponse.json({ ok: true, processed, stored, skipped });
}
