import { NextResponse } from "next/server";
import { z } from "zod";
import { ingestTweetPhrases } from "@/lib/ingestion";

const TweetSchema = z.object({
  id: z.string(),
  text: z.string(),
  authorId: z.string(),
  authorHandle: z.string(),
  createdAt: z.string().optional(),
  likeCount: z.number().optional(),
  retweetCount: z.number().optional()
});

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

export async function POST(req: Request) {
  const unauthorized = assertCronAuth(req);
  if (unauthorized) return unauthorized;

  const json: unknown = await req.json().catch(() => null);
  const parsed = TweetSchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid tweet payload" }, { status: 400 });
  }

  try {
    const result = await ingestTweetPhrases({
      ...parsed.data,
      likeCount: parsed.data.likeCount ?? 0,
      retweetCount: parsed.data.retweetCount ?? 0
    });
    return NextResponse.json({ ok: true, ...result });
  } catch (e) {
    const message = e instanceof Error ? e.message : "Unknown error";
    console.error("ingest/tweet failed:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
