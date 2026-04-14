import "server-only";

import { pipeline, type FeatureExtractionPipeline } from "@xenova/transformers";

const MODEL_ID = "Xenova/bge-m3";

let extractorPromise: Promise<FeatureExtractionPipeline> | null = null;

/**
 * Lazy singleton for BGE-M3 feature extraction (1024-d embeddings).
 * Runs server-side only — do not import from Client Components.
 */
export async function getEmbeddingExtractor(): Promise<FeatureExtractionPipeline> {
  if (!extractorPromise) {
    extractorPromise = pipeline("feature-extraction", MODEL_ID);
  }
  return extractorPromise;
}

/**
 * L2-normalize a vector (required for stable cosine similarity via dot product).
 */
export function l2Normalize(values: number[]): number[] {
  let sumSq = 0;
  for (const v of values) sumSq += v * v;
  const norm = Math.sqrt(sumSq) || 1;
  return values.map((v) => v / norm);
}

/**
 * Embed a single string into a 1024-d L2-normalized vector.
 */
export async function embedText(text: string): Promise<number[]> {
  const extractor = await getEmbeddingExtractor();
  const output = await extractor(text, { pooling: "mean", normalize: true });
  const data = Array.from(output.data as Float32Array | number[]);
  return l2Normalize(data.map(Number));
}

/**
 * Cosine similarity for L2-normalized vectors equals dot product.
 */
export function cosineSimilarity(a: number[], b: number[]): number {
  const len = Math.min(a.length, b.length);
  let dot = 0;
  for (let i = 0; i < len; i++) dot += a[i] * b[i];
  return dot;
}
