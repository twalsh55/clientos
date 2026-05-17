import { NextResponse } from "next/server";

import { exportAccountPrivacyData } from "@/lib/api";
import { getServerApiAuthOptions } from "@/lib/server-auth";

export async function GET() {
  const { sessionToken, cookieHeader } = await getServerApiAuthOptions();

  try {
    const payload = await exportAccountPrivacyData({ sessionToken, cookieHeader });
    return NextResponse.json(payload);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to export account data.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
