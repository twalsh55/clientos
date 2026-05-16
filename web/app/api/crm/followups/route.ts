import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { getCrmFollowUpOverview } from "@/lib/api";
import { BRIVOLY_SESSION_COOKIE, LEGACY_TRADE_SESSION_COOKIE } from "@/lib/auth";

export async function GET() {
  const cookieStore = await cookies();
  const sessionToken =
    cookieStore.get(BRIVOLY_SESSION_COOKIE)?.value ?? cookieStore.get(LEGACY_TRADE_SESSION_COOKIE)?.value ?? null;

  if (!sessionToken) {
    return NextResponse.json({ error: "Authentication required." }, { status: 401 });
  }

  try {
    const overview = await getCrmFollowUpOverview({ sessionToken });
    return NextResponse.json(overview);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to load CRM follow-up queue.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
