import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

/**
 * Placeholder route group for future Supabase Auth / SIWE flows.
 * Wallet-based access currently lives on `/dashboard`.
 */
export default function LoginPage() {
  return (
    <div className="mx-auto flex max-w-lg flex-col gap-6 px-6 py-16">
      <Card>
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
          <CardDescription>
            This MVP uses wallet connection on the dashboard. Dedicated auth can be wired here later.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link href="/dashboard">Go to dashboard</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
