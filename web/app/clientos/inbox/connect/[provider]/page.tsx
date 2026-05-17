"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";

type ConnectionState = {
  status: "working" | "error";
  message: string;
};

export default function MailboxOAuthCallbackPage() {
  const router = useRouter();
  const params = useParams<{ provider: string }>();
  const searchParams = useSearchParams();
  const [state, setState] = useState<ConnectionState>({
    status: "working",
    message: "Finishing the mailbox connection and bringing you back into relationship memory...",
  });

  useEffect(() => {
    let cancelled = false;

    async function completeMailboxConnection() {
      const provider = params?.provider ?? "";
      const code = searchParams?.get("code") ?? "";
      const oauthState = searchParams?.get("state") ?? "";
      const providerError = searchParams?.get("error");

      if (providerError) {
        if (!cancelled) {
          setState({
            status: "error",
            message: searchParams?.get("error_description") || "The mailbox provider declined the connection.",
          });
        }
        return;
      }

      if (!provider || !code || !oauthState) {
        if (!cancelled) {
          setState({
            status: "error",
            message: "The mailbox provider did not return a usable connection code.",
          });
        }
        return;
      }

      try {
        const response = await fetch("/api/crm/inbox/mailboxes/oauth/complete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider,
            code,
            state: oauthState,
          }),
        });
        const body = (await response.json().catch(() => null)) as { error?: string } | null;
        if (!response.ok) {
          throw new Error(body?.error || "Unable to finish mailbox connection.");
        }
        router.replace("/clientos/inbox?mailbox=connected");
      } catch (error) {
        if (!cancelled) {
          setState({
            status: "error",
            message: error instanceof Error ? error.message : "Unable to finish mailbox connection.",
          });
        }
      }
    }

    void completeMailboxConnection();
    return () => {
      cancelled = true;
    };
  }, [params?.provider, router, searchParams]);

  return (
    <main className="mx-auto flex min-h-[70vh] max-w-3xl items-center justify-center px-6 py-20">
      <section className="w-full rounded-[2rem] border border-slate-200 bg-white/95 p-8 shadow-sm">
        <p className="ui-eyebrow">Mailbox connection</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
          {state.status === "working" ? "Linking your inbox..." : "Mailbox connection hit a snag."}
        </h1>
        <p className="mt-4 text-sm leading-7 text-slate-600">{state.message}</p>
        {state.status === "error" ? (
          <button
            type="button"
            onClick={() => router.replace("/clientos/inbox")}
            className="mt-6 rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-900 transition hover:border-slate-500"
          >
            Back to inbox
          </button>
        ) : null}
      </section>
    </main>
  );
}
