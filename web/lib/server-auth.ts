import { cookies } from "next/headers";

import { BRIVOLY_SESSION_COOKIE, LEGACY_TRADE_SESSION_COOKIE } from "@/lib/auth";

export async function getServerApiAuthOptions(): Promise<{ sessionToken: string | null; cookieHeader: string | null }> {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get("__session")?.value ?? null;
  const persistedSessionToken =
    cookieStore.get(BRIVOLY_SESSION_COOKIE)?.value ?? cookieStore.get(LEGACY_TRADE_SESSION_COOKIE)?.value ?? null;
  return {
    // Prefer the live Clerk session cookie when it exists. The API authenticates the
    // Authorization header before the forwarded cookie, so sending an older persisted
    // token here can incorrectly override a fresh __session value.
    sessionToken: sessionCookie ?? persistedSessionToken,
    cookieHeader: sessionCookie ? `__session=${sessionCookie}` : null,
  };
}
