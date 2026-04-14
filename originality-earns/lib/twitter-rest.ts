import { z } from "zod";
import { parseTweetPayload, type NormalizedTweet } from "@/lib/twitter";

const SearchResponseSchema = z.object({
  tweets: z.array(z.unknown()).optional(),
  data: z.array(z.unknown()).optional()
});

/**
 * REST fallback polling for recent English tweets.
 * Query string should follow TwitterAPI.io advanced search syntax.
 */
export async function fetchRecentTweets(query: string): Promise<NormalizedTweet[]> {
  const key = process.env.TWITTERAPI_IO_KEY;
  if (!key) throw new Error("Missing TWITTERAPI_IO_KEY");

  const url = new URL("https://api.twitterapi.io/twitter/tweet/advanced_search");
  url.searchParams.set("query", query);
  url.searchParams.set("count", "20");

  const res = await fetch(url.toString(), {
    headers: {
      "X-API-Key": key
    },
    next: { revalidate: 0 }
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`TwitterAPI.io REST error ${res.status}: ${body.slice(0, 500)}`);
  }

  const json: unknown = await res.json();
  const parsed = SearchResponseSchema.safeParse(json);
  if (!parsed.success) return [];

  const rawTweets = parsed.data.tweets ?? parsed.data.data ?? [];
  const normalized: NormalizedTweet[] = [];

  for (const raw of rawTweets) {
    normalized.push(...parseTweetPayload({ tweets: [raw] }));
  }

  return normalized;
}
