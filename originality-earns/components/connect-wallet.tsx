"use client";

import { useMemo } from "react";
import { useAccount, useConnect, useDisconnect } from "wagmi";
import { Button } from "@/components/ui/button";

export function ConnectWallet() {
  const { address, isConnected } = useAccount();
  const { connect, connectors, isPending } = useConnect();
  const { disconnect } = useDisconnect();

  const injected = useMemo(
    () => connectors.find((c) => c.id === "injected" || c.name.toLowerCase().includes("injected")),
    [connectors]
  );

  return (
    <div className="flex flex-wrap items-center gap-2">
      {isConnected ? (
        <>
          <span className="text-xs text-muted-foreground break-all">{address}</span>
          <Button variant="outline" size="sm" onClick={() => disconnect()}>
            Disconnect
          </Button>
        </>
      ) : (
        <Button
          size="sm"
          disabled={!injected || isPending}
          onClick={() => injected && connect({ connector: injected })}
        >
          {isPending ? "Connecting…" : "Connect wallet"}
        </Button>
      )}
    </div>
  );
}
