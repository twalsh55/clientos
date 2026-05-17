import { NextRequest, NextResponse } from "next/server";

import { ApiError, deleteCrmMailboxConnection, updateCrmMailboxConnection } from "@/lib/api";
import { getServerApiAuthOptions } from "@/lib/server-auth";

type RouteContext = {
  params: Promise<{ id: string }>;
};

export async function PATCH(request: NextRequest, context: RouteContext) {
  const { sessionToken, cookieHeader } = await getServerApiAuthOptions();
  const { id } = await context.params;
  const payload = (await request.json().catch(() => null)) as { background_sync_enabled?: boolean } | null;

  if (typeof payload?.background_sync_enabled !== "boolean") {
    return NextResponse.json({ error: "background_sync_enabled is required." }, { status: 422 });
  }

  try {
    const result = await updateCrmMailboxConnection(id, { background_sync_enabled: payload.background_sync_enabled }, { sessionToken, cookieHeader });
    return NextResponse.json(result);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json({ error: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : "Unable to update the mailbox right now.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function DELETE(_request: NextRequest, context: RouteContext) {
  const { sessionToken, cookieHeader } = await getServerApiAuthOptions();
  const { id } = await context.params;

  try {
    const result = await deleteCrmMailboxConnection(id, { sessionToken, cookieHeader });
    return NextResponse.json(result);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json({ error: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : "Unable to disconnect the mailbox right now.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
