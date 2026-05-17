import { NextResponse } from "next/server";

import { getAlertHistory } from "@/lib/api";
import { getServerApiAuthOptions } from "@/lib/server-auth";

export async function GET(request: Request) {
  const { sessionToken, cookieHeader } = await getServerApiAuthOptions();
  if (!sessionToken) {
    return NextResponse.json({ error: "Authentication required." }, { status: 401 });
  }

  const url = new URL(request.url);
  const limit = Number(url.searchParams.get("limit") ?? "20");

  try {
    const alerts = await getAlertHistory({ sessionToken, cookieHeader });
    return NextResponse.json({
      items: alerts.items.slice(0, Number.isFinite(limit) ? limit : 20),
      count: Math.min(alerts.count, Number.isFinite(limit) ? limit : 20),
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to load alert history.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
