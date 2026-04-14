import { z } from "zod";

export const TWITTER_WS_URL = "wss://ws.twitterapi.io/twitter/tweet/websocket";

const TweetAuthorSchema = z.object({
  id: z.union([z.string(), z.number()]).optional(),
  username: z.string().optional(),
  name: z.string().optional()
});

const TweetSchema = z.object({
  id: z.union([z.string(), z.number()]),
  text: z.string(),
  author: TweetAuthorSchema.optional(),
  createdAt: z.string().optional(),
  lang: z.string().optional(),
  isRetweet: z.boolean().optional(),
  isReply: z.boolean().optional(),
  inReplyToUserId: z.union([z.string(), z.number(), z.null()]).optional(),
  retweetCount: z.number().optional(),
  likeCount: z.number().optional()
});

const TweetEventSchema = z.object({
  event_type: z.string().optional(),
  tweets: z.array(TweetSchema).optional(),
  tweet: TweetSchema.optional()
});

export type NormalizedTweet = {
  id: string;
  text: string;
  authorId: string;
  authorHandle: string;
  createdAt?: string;
  likeCount: number;
  retweetCount: number;
};

/**
 * Normalize TwitterAPI.io payloads (WebSocket or REST) into a stable shape.
 */
export function parseTweetPayload(raw: unknown): NormalizedTweet[] {
  const parsed = TweetEventSchema.safeParse(raw);
  if (!parsed.success) return [];

  const items: z.infer<typeof TweetSchema>[] = [];
  if (parsed.data.tweets?.length) items.push(...parsed.data.tweets);
  if (parsed.data.tweet) items.push(parsed.data.tweet);

  return items
    .map((t) => {
      const authorId = t.author?.id != null ? String(t.author.id) : "";
      const authorHandle = t.author?.username ?? "unknown";
      return {
        id: String(t.id),
        text: t.text,
        authorId,
        authorHandle,
        createdAt: t.createdAt,
        likeCount: t.likeCount ?? 0,
        retweetCount: t.retweetCount ?? 0
      } satisfies NormalizedTweet;
    })
    .filter((t) => t.text.trim().length > 0);
}

/**
 * MVP filters: English-only, skip retweets and replies when flags exist.
 */
export function shouldProcessTweet(tweet: NormalizedTweet, raw: unknown): boolean {
  const obj = raw as Record<string, unknown>;
  const nestedTweet = (obj?.tweet ?? obj) as Record<string, unknown>;

  const lang =
    (nestedTweet.lang as string | undefined) ??
    (nestedTweet.language as string | undefined);

  if (lang && lang.toLowerCase() !== "en") return false;

  if (nestedTweet.isRetweet === true) return false;
  if (nestedTweet.isReply === true) return false;
  if (nestedTweet.inReplyToStatusId != null) return false;
  if (nestedTweet.inReplyToUserId != null) return false;

  // Heuristic: replies often start with @handle
  if (/^@\w+/.test(tweet.text.trim())) return false;

  return true;
}
