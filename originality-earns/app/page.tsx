import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-10 px-6 py-14">
      <div className="space-y-4">
        <p className="text-sm font-medium text-muted-foreground">Base-native rewards for novel language</p>
        <h1 className="text-4xl font-semibold tracking-tight md:text-5xl">
          Pay creators when they coin genuinely new phrases on X.
        </h1>
        <p className="max-w-2xl text-lg text-muted-foreground">
          Originality Earns listens to the public firehose (via TwitterAPI.io), extracts multi-word candidates,
          and stores the first original contextual use in a rolling 90-day embedding corpus. Scores compound into
          a public leaderboard; weekly $ORIGIN distributions settle on Base.
        </p>
        <div className="flex flex-wrap gap-3">
          <Button asChild size="lg">
            <Link href="/leaderboard">View leaderboard</Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href="/dashboard">Connect wallet</Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Semantic first-seen</CardTitle>
            <CardDescription>BGE-M3 embeddings + pgvector HNSW search.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            A phrase is novel when cosine similarity against the last 90 days stays below your configured
            threshold (default 0.85).
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Human signal</CardTitle>
            <CardDescription>Originality.ai scan on each candidate.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            We multiply novelty by an engagement-aware early virality term and a human-likeness bonus from
            Originality.ai.
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>On-chain weekly cadence</CardTitle>
            <CardDescription>Foundry contracts on Base.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            $ORIGIN is a simple ERC-20. The distributor contract transfers pre-minted rewards to ranked wallets
            each week (owner-gated for the MVP).
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
