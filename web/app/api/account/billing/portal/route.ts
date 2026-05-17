import { NextResponse } from "next/server";

import { createBillingPortalSession } from "@/lib/api";
import { getServerApiAuthOptions } from "@/lib/server-auth";

export async function POST(request: Request) {
  const { sessionToken, cookieHeader } = await getServerApiAuthOptions();
  if (!sessionToken && !cookieHeader) {
    return NextResponse.json({ error: "Authentication required." }, { status: 401 });
  }

  const payload = (await request.json().catch(() => null)) as { return_url?: string | null } | null;

  try {
    const session = await createBillingPortalSession(payload ?? {}, { sessionToken, cookieHeader });
    return NextResponse.json(session);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to create billing portal session.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
