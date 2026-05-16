import { cookies } from "next/headers";

import { AppShell } from "@/components/app-shell";
import { BRIVOLY_SESSION_COOKIE, LEGACY_TRADE_SESSION_COOKIE } from "@/lib/auth";
import { getShellData } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CrashMonitorPage() {
  const cookieStore = await cookies();
  const sessionToken =
    cookieStore.get(BRIVOLY_SESSION_COOKIE)?.value ?? cookieStore.get(LEGACY_TRADE_SESSION_COOKIE)?.value ?? null;
  const sessionCookie = cookieStore.get("__session")?.value;
  const cookieHeader = sessionCookie ? `__session=${sessionCookie}` : null;
  const data = await getShellData({ sessionToken, cookieHeader });

  return <AppShell data={data} />;
}
