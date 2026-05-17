import { NextRequest, NextResponse } from "next/server";

import { ApiError, startCrmMailboxOAuth } from "@/lib/api";
import { getServerApiAuthOptions } from "@/lib/server-auth";

export async function POST(request: NextRequest) {
  const { sessionToken, cookieHeader } = await getServerApiAuthOptions();
  const payload = (await request.json().catch(() => null)) as
    | {
        provider?: "gmail" | "outlook";
      }
    | null;

  if (!payload?.provider) {
    return NextResponse.json({ error: "provider is required." }, { status: 422 });
  }

  try {
    const result = await startCrmMailboxOAuth({ provider: payload.provider }, { sessionToken, cookieHeader });
    return NextResponse.json(result);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json({ error: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : "Unable to begin mailbox connection right now.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
