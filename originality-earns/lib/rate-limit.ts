type Bucket = { count: number; resetAt: number };

const buckets = new Map<string, Bucket>();

/**
 * Fixed-window rate limiter (in-memory). Suitable for MVP / single-instance.
 * For multi-node production, swap for Redis/Upstash.
 */
export function rateLimit(
  key: string,
  max: number,
  windowMs: number
): { ok: true } | { ok: false; retryAfterMs: number } {
  const now = Date.now();
  const existing = buckets.get(key);
  if (!existing || now >= existing.resetAt) {
    buckets.set(key, { count: 1, resetAt: now + windowMs });
    return { ok: true };
  }
  if (existing.count < max) {
    existing.count += 1;
    return { ok: true };
  }
  return { ok: false, retryAfterMs: Math.max(0, existing.resetAt - now) };
}
