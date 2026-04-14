"use client";

import { useCallback, useEffect, useMemo, useState, useTransition } from "react";
import { useAccount, useReadContract, useWriteContract } from "wagmi";
import { base, baseSepolia } from "wagmi/chains";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { REWARD_DISTRIBUTOR_ABI } from "@/lib/abis";
import { linkCreatorProfile, loadCreatorDashboard } from "@/app/dashboard/actions";

type DashboardState =
  | { status: "loading" }
  | { status: "unlinked" }
  | {
      status: "ready";
      rank: number;
      handle: string;
      score: number;
      phrases: number;
      lastPhrase: string | null;
    };

export function DashboardPanel() {
  const { address, isConnected, chain } = useAccount();
  const [handleInput, setHandleInput] = useState("");
  const [state, setState] = useState<DashboardState>({ status: "loading" });
  const [pending, startTransition] = useTransition();

  const distributor = process.env.NEXT_PUBLIC_REWARD_DISTRIBUTOR_ADDRESS as `0x${string}` | undefined;
  const originToken = process.env.NEXT_PUBLIC_ORIGIN_TOKEN_ADDRESS as `0x${string}` | undefined;

  const targetChainId = useMemo(() => {
    const raw = process.env.NEXT_PUBLIC_CHAIN_ID;
    if (!raw) return base.id;
    const parsed = Number(raw);
    return parsed === baseSepolia.id ? baseSepolia.id : base.id;
  }, []);

  const { data: claimable, refetch } = useReadContract({
    address: distributor,
    abi: REWARD_DISTRIBUTOR_ABI,
    functionName: "claimable",
    args: address ? [address] : undefined,
    query: { enabled: Boolean(distributor && address) }
  });

  const { writeContractAsync, isPending: isClaiming } = useWriteContract();

  const refresh = useCallback(async () => {
    if (!address) {
      setState({ status: "unlinked" });
      return;
    }

    setState({ status: "loading" });
    const res = await loadCreatorDashboard(address);
    if (!res.ok) {
      setState({ status: "unlinked" });
      return;
    }

    if (!res.linked || !res.creator) {
      setState({ status: "unlinked" });
      return;
    }

    setState({
      status: "ready",
      rank: res.rank,
      handle: res.creator.author_handle,
      score: Number(res.creator.total_originality_score),
      phrases: Number(res.creator.phrases_coined),
      lastPhrase: res.creator.last_phrase
    });
  }, [address]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function onLink() {
    if (!address) return;
    startTransition(async () => {
      const res = await linkCreatorProfile({ walletAddress: address, authorHandle: handleInput });
      if (!res.ok) {
        console.error(res.error);
        return;
      }
      await refresh();
    });
  }

  async function onClaim() {
    if (!distributor) return;
    if (chain?.id !== targetChainId) {
      console.error("Switch to the configured Base network before claiming.");
      return;
    }
    await writeContractAsync({
      address: distributor,
      abi: REWARD_DISTRIBUTOR_ABI,
      functionName: "claim"
    });
    await refetch();
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Wallet</CardTitle>
          <CardDescription>Connect on Base mainnet or Base Sepolia for demos.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p className="break-all text-muted-foreground">
            {isConnected && address ? address : "Wallet disconnected"}
          </p>
          {originToken ? (
            <p className="text-xs text-muted-foreground">
              $ORIGIN token: <span className="font-mono">{originToken}</span>
            </p>
          ) : null}
          {distributor ? (
            <p className="text-xs text-muted-foreground">
              Distributor: <span className="font-mono">{distributor}</span>
            </p>
          ) : (
            <p className="text-xs text-amber-700">
              Set `NEXT_PUBLIC_REWARD_DISTRIBUTOR_ADDRESS` after deploying contracts.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Creator profile</CardTitle>
          <CardDescription>Link your wallet to the X handle we should rank.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="handle">
              X handle
            </label>
            <input
              id="handle"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
              placeholder="creator"
              value={handleInput}
              onChange={(e) => setHandleInput(e.target.value)}
            />
          </div>
          <Button disabled={!address || pending} onClick={onLink}>
            Save link
          </Button>
        </CardContent>
      </Card>

      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle>Your rank</CardTitle>
          <CardDescription>Scores update live as novel phrases are indexed.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {state.status === "loading" ? (
            <p className="text-sm text-muted-foreground">Loading profile…</p>
          ) : state.status === "unlinked" ? (
            <p className="text-sm text-muted-foreground">
              Link your handle to see personalized stats. Global rankings remain public on the leaderboard page.
            </p>
          ) : (
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <p className="text-xs uppercase text-muted-foreground">Rank</p>
                <p className="text-2xl font-semibold">#{state.rank}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-muted-foreground">Score</p>
                <p className="text-2xl font-semibold">{state.score.toFixed(3)}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-muted-foreground">Phrases coined</p>
                <p className="text-2xl font-semibold">{state.phrases}</p>
              </div>
              <div className="md:col-span-3 text-sm text-muted-foreground">
                Last phrase: {state.lastPhrase ? `"${state.lastPhrase}"` : "—"}
              </div>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3 border-t pt-4">
            <div className="text-sm text-muted-foreground">
              Claimable:{" "}
              <span className="font-mono text-foreground">
                {claimable != null ? `${Number(claimable) / 1e18} ORIGIN` : "0 ORIGIN"}
              </span>
            </div>
            <Button disabled={!distributor || !address || isClaiming} onClick={onClaim}>
              Claim rewards
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
