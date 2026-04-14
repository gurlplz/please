import { z } from "zod";

const ScanResponseSchema = z
  .object({
    score: z
      .object({
        human: z.number().optional(),
        ai: z.number().optional()
      })
      .optional(),
    // Some API versions return flat fields
    human: z.number().optional(),
    ai: z.number().optional()
  })
  .passthrough();

/**
 * Calls Originality.ai to estimate how human-like the text is.
 * Returns a 0–1 "human bonus" multiplier where 1 means very likely human.
 *
 * Docs evolve across versions — this client is intentionally defensive.
 */
export async function originalityHumanBonus(text: string): Promise<number> {
  const apiKey = process.env.ORIGINALITY_AI_KEY;
  if (!apiKey) {
    // Dev-friendly fallback when the key is absent
    return 0.85;
  }

  const baseUrl = process.env.ORIGINALITY_AI_API_URL ?? "https://api.originality.ai/api/v1";
  const res = await fetch(`${baseUrl.replace(/\/$/, "")}/scan/ai-scan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      content: text.slice(0, 8000)
    })
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Originality.ai error ${res.status}: ${body.slice(0, 500)}`);
  }

  const json: unknown = await res.json();
  const parsed = ScanResponseSchema.safeParse(json);
  if (!parsed.success) return 0.75;

  const humanScore =
    parsed.data.score?.human ??
    parsed.data.human ??
    (parsed.data.score?.ai != null ? 1 - parsed.data.score.ai : undefined) ??
    (parsed.data.ai != null ? 1 - parsed.data.ai : undefined);

  if (humanScore == null || Number.isNaN(humanScore)) return 0.75;

  // Clamp into [0.2, 1.0] so downstream math stays stable
  return Math.min(1, Math.max(0.2, humanScore));
}
