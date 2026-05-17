import { cookies } from "next/headers";

import { BRIVOLY_SESSION_COOKIE, LEGACY_TRADE_SESSION_COOKIE } from "@/lib/auth";

export async function getServerApiAuthOptions(): Promise<{ sessionToken: string | null; cookieHeader: string | null }> {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get("__session")?.value ?? null;
  const persistedSessionToken =
    cookieStore.get(BRIVOLY_SESSION_COOKIE)?.value ?? cookieStore.get(LEGACY_TRADE_SESSION_COOKIE)?.value ?? null;
  return {
    // Keep the app-persisted token in Authorization when available, and always forward
    // the live Clerk session cookie separately. The API can then prefer the fresher
    // cookie when both are present without forcing the raw cookie into Bearer auth.
    sessionToken: persistedSessionToken,
    cookieHeader: sessionCookie ? `__session=${sessionCookie}` : null,
  };
}
