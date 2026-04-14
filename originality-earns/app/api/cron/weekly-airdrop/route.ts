import { NextResponse } from "next/server";
import { encodeFunctionData, parseEther } from "viem";
import { getServiceSupabase } from "@/lib/supabase";
import { REWARD_DISTRIBUTOR_ABI } from "@/lib/abis";

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

/**
 * Computes the weekly payout list from linked wallets + top creators.
 * The MVP stops short of broadcasting transactions — it returns calldata for the owner wallet.
 */
export async function POST(req: Request) {
  const unauthorized = assertCronAuth(req);
  if (unauthorized) return unauthorized;

  const distributor = process.env.NEXT_PUBLIC_REWARD_DISTRIBUTOR_ADDRESS as `0x${string}` | undefined;
  if (!distributor) {
    return NextResponse.json({ error: "Missing NEXT_PUBLIC_REWARD_DISTRIBUTOR_ADDRESS" }, { status: 400 });
  }

  const topN = Number(process.env.WEEKLY_TOP_N ?? "25");
  const supabase = getServiceSupabase();

  const { data: creators, error } = await supabase
    .from("creators")
    .select("author_handle,total_originality_score")
    .order("total_originality_score", { ascending: false })
    .limit(topN);

  if (error || !creators) {
    return NextResponse.json({ error: error?.message ?? "query failed" }, { status: 500 });
  }

  const { data: links, error: linkError } = await supabase.from("dashboard_links").select("*");
  if (linkError || !links) {
    return NextResponse.json({ error: linkError?.message ?? "links failed" }, { status: 500 });
  }

  const handleToWallet = new Map<string, string>();
  for (const row of links) {
    handleToWallet.set(row.author_handle.toLowerCase(), row.wallet_address);
  }

  const recipients: `0x${string}`[] = [];
  const amounts: bigint[] = [];

  const perWinner = parseEther(process.env.WEEKLY_REWARD_PER_WINNER ?? "25");

  for (const c of creators) {
    const wallet = handleToWallet.get(c.author_handle.toLowerCase());
    if (!wallet) continue;
    recipients.push(wallet as `0x${string}`);
    amounts.push(perWinner);
  }

  const data =
    recipients.length > 0
      ? encodeFunctionData({
          abi: REWARD_DISTRIBUTOR_ABI,
          functionName: "distribute",
          args: [recipients, amounts]
        })
      : null;

  const { error: insertError } = await supabase.from("reward_runs").insert({
    week_start: new Date().toISOString().slice(0, 10),
    chain_id: Number(process.env.NEXT_PUBLIC_CHAIN_ID ?? "8453"),
    distributor_address: distributor,
    token_address: process.env.NEXT_PUBLIC_ORIGIN_TOKEN_ADDRESS ?? "",
    payload: { recipients, amounts: amounts.map((a) => a.toString()) }
  });

  if (insertError) {
    console.error("reward_runs insert failed:", insertError.message);
  }

  return NextResponse.json({
    ok: true,
    recipients,
    amounts: amounts.map((a) => a.toString()),
    calldata: data,
    distributor
  });
}
