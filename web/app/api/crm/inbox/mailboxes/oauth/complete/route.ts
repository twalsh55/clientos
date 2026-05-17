import { NextRequest, NextResponse } from "next/server";

import { ApiError, completeCrmMailboxOAuth } from "@/lib/api";
import { getServerApiAuthOptions } from "@/lib/server-auth";

export async function POST(request: NextRequest) {
  const { sessionToken, cookieHeader } = await getServerApiAuthOptions();
  const payload = (await request.json().catch(() => null)) as
    | {
        provider?: "gmail" | "outlook";
        code?: string;
        state?: string;
      }
    | null;

  if (!payload?.provider || !payload?.code || !payload?.state) {
    return NextResponse.json({ error: "provider, code, and state are required." }, { status: 422 });
  }

  try {
    const result = await completeCrmMailboxOAuth(
      {
        provider: payload.provider,
        code: payload.code,
        state: payload.state,
      },
      { sessionToken, cookieHeader },
    );
    return NextResponse.json(result);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json({ error: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : "Unable to finish mailbox connection right now.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
