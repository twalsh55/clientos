import { cookies } from "next/headers";

import { BRIVOLY_SESSION_COOKIE, LEGACY_TRADE_SESSION_COOKIE } from "@/lib/auth";

export async function getServerApiAuthOptions(): Promise<{ sessionToken: string | null; cookieHeader: string | null }> {
  const cookieStore = await cookies();
  const sessionToken =
    cookieStore.get(BRIVOLY_SESSION_COOKIE)?.value ?? cookieStore.get(LEGACY_TRADE_SESSION_COOKIE)?.value ?? null;
  const sessionCookie = cookieStore.get("__session")?.value ?? null;
  return {
    sessionToken,
    cookieHeader: sessionCookie ? `__session=${sessionCookie}` : null,
  };
}
