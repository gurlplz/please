import { Suspense } from "react";
import { ConnectWallet } from "@/components/connect-wallet";
import { DashboardPanel } from "@/components/dashboard-panel";

export default function DashboardPage() {
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-12">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
          <p className="mt-2 max-w-2xl text-muted-foreground">
            Connect your Base wallet, link the X handle you want ranked, and claim any weekly rewards assigned
            by the distributor contract.
          </p>
        </div>
        <ConnectWallet />
      </div>

      <Suspense fallback={<p className="text-sm text-muted-foreground">Loading…</p>}>
        <DashboardPanel />
      </Suspense>
    </div>
  );
}
