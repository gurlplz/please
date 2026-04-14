#!/usr/bin/env node
/**
 * Long-running TwitterAPI.io WebSocket worker.
 *
 * Usage:
 *   TWITTERAPI_IO_KEY=... CRON_SECRET=... NEXT_URL=http://localhost:3000 node ./scripts/twitter-stream.mjs
 *
 * Configure filter rules in the TwitterAPI.io dashboard before streaming.
 */
import WebSocket from "ws";

const apiKey = process.env.TWITTERAPI_IO_KEY;
const cronSecret = process.env.CRON_SECRET;
const baseUrl = process.env.NEXT_URL ?? "http://localhost:3000";

if (!apiKey || !cronSecret) {
  console.error("Missing TWITTERAPI_IO_KEY or CRON_SECRET");
  process.exit(1);
}

const ws = new WebSocket("wss://ws.twitterapi.io/twitter/tweet/websocket", {
  headers: { "x-api-key": apiKey }
});

function shouldProcessTweet(tweet, raw) {
  const lang = raw?.lang ?? raw?.language;
  if (lang && String(lang).toLowerCase() !== "en") return false;
  if (raw?.isRetweet === true) return false;
  if (raw?.isReply === true) return false;
  if (raw?.inReplyToUserId != null) return false;
  if (typeof tweet?.text === "string" && /^@\w+/.test(tweet.text.trim())) return false;
  return true;
}

async function ingestTweet(tweet) {
  const res = await fetch(`${baseUrl.replace(/\/$/, "")}/api/ingest/tweet`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${cronSecret}`
    },
    body: JSON.stringify({
      id: String(tweet.id),
      text: tweet.text,
      authorId: String(tweet.authorId ?? ""),
      authorHandle: tweet.authorHandle ?? "unknown",
      createdAt: tweet.createdAt,
      likeCount: tweet.likeCount ?? 0,
      retweetCount: tweet.retweetCount ?? 0
    })
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    console.error("ingest failed:", res.status, body.slice(0, 500));
  }
}

ws.on("open", () => {
  console.log("Connected to TwitterAPI.io websocket");
});

ws.on("message", async (data) => {
  let payload;
  try {
    payload = JSON.parse(String(data));
  } catch {
    return;
  }

  if (payload?.event_type && payload.event_type !== "tweet") {
    return;
  }

  const tweets = payload?.tweets ?? (payload?.tweet ? [payload.tweet] : []);
  for (const rawTweet of tweets) {
    const tweet = {
      id: rawTweet.id,
      text: rawTweet.text,
      authorId: rawTweet.author?.id != null ? String(rawTweet.author.id) : "",
      authorHandle: rawTweet.author?.username ?? "unknown",
      createdAt: rawTweet.createdAt,
      likeCount: rawTweet.likeCount ?? 0,
      retweetCount: rawTweet.retweetCount ?? 0
    };

    if (!tweet.text || !tweet.authorId) continue;
    if (!shouldProcessTweet(tweet, rawTweet)) continue;

    try {
      await ingestTweet(tweet);
    } catch (e) {
      console.error("ingest error:", e);
    }
  }
});

ws.on("error", (err) => {
  console.error("WebSocket error:", err);
});

ws.on("close", (code) => {
  console.log("WebSocket closed:", code);
  process.exit(0);
});
