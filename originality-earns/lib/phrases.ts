import nlp from "compromise";

const STOP = new Set([
  "the",
  "a",
  "an",
  "and",
  "or",
  "but",
  "if",
  "then",
  "to",
  "of",
  "in",
  "on",
  "for",
  "with",
  "at",
  "by",
  "from",
  "as",
  "is",
  "was",
  "are",
  "were",
  "be",
  "been",
  "being",
  "it",
  "this",
  "that",
  "these",
  "those",
  "i",
  "you",
  "we",
  "they",
  "he",
  "she",
  "them",
  "my",
  "your",
  "our",
  "their",
  "not",
  "no",
  "so",
  "just",
  "like",
  "rt",
  "https",
  "http"
]);

function cleanToken(t: string): string | null {
  const s = t
    .toLowerCase()
    .replace(/^[@#]+/, "")
    .replace(/https?:\/\/\S+/g, "")
    .replace(/[^a-z0-9']/g, "");
  if (!s || s.length < 2) return null;
  if (STOP.has(s)) return null;
  return s;
}

function windowNgrams(tokens: string[], min: number, max: number): string[][] {
  const grams: string[][] = [];
  for (let n = min; n <= max; n++) {
    for (let i = 0; i + n <= tokens.length; i++) {
      grams.push(tokens.slice(i, i + n));
    }
  }
  return grams;
}

/**
 * spaCy-style phrase mining using compromise signals + bounded n-grams.
 * Produces 3–8 word candidate phrases suitable for semantic novelty scoring.
 */
export function extractCandidatePhrases(text: string): string[] {
  const doc = nlp(text);
  const phrases = new Set<string>();

  // Multi-word noun surfaces are strong phrase candidates (lightweight vs spaCy)
  for (const surface of doc.nouns().out("array") as string[]) {
    const words = surface
      .split(/\s+/)
      .map((w) => cleanToken(w))
      .filter(Boolean) as string[];
    if (words.length >= 3 && words.length <= 8) {
      phrases.add(words.join(" "));
    }
  }

  // Sliding n-grams on cleaned sentence tokens
  const terms = (doc.terms().out("array") as string[])
    .map((w) => cleanToken(w))
    .filter(Boolean) as string[];

  for (const gram of windowNgrams(terms, 3, 8)) {
    phrases.add(gram.join(" "));
  }

  return [...phrases].filter((p) => p.split(/\s+/).length >= 3);
}
