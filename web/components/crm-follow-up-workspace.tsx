"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import type { CRMFollowUpOverview } from "@/lib/types";

export function CRMFollowUpWorkspace({ initialOverview }: { initialOverview: CRMFollowUpOverview }) {
  const router = useRouter();
  const [overview, setOverview] = useState(initialOverview);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function runAction(followUpId: string, payload: { action: "complete" | "snooze"; snooze_hours?: number }) {
    setPendingId(followUpId);
    setError(null);
    startTransition(async () => {
      try {
        const response = await fetch(`/api/crm/followups/${followUpId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        const data = (await response.json().catch(() => null)) as CRMFollowUpOverview | { error?: string } | null;
        if (!response.ok || !data || !("items" in data)) {
          throw new Error((data && "error" in data && data.error) || "Unable to update follow-up.");
        }

        setOverview(data);
        router.refresh();
      } catch (actionError) {
        setError(actionError instanceof Error ? actionError.message : "Unable to update follow-up.");
      } finally {
        setPendingId(null);
      }
    });
  }

  return (
    <>
      <section className="mt-6 grid gap-6 md:grid-cols-4">
        <MetricCard label="Open follow-ups" value={String(overview.total_open)} tone="neutral" />
        <MetricCard label="Due today" value={String(overview.due_today)} tone="warning" />
        <MetricCard label="Overdue" value={String(overview.overdue)} tone={overview.overdue > 0 ? "critical" : "positive"} />
        <MetricCard label="High priority" value={String(overview.high_priority)} tone="neutral" />
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <section className="rounded-[1.75rem] border bg-white/80 p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Lead Follow-Up Queue</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">Who needs a follow-up next.</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Work the queue directly: close a follow-up when it is done, or push it forward when the right next touch is later.
          </p>
          {error ? <p className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p> : null}
          <div className="mt-6 space-y-4">
            {overview.items.map((item) => {
              const rowPending = pendingId === item.id && isPending;
              return (
                <article key={item.id} className="rounded-[1.5rem] border bg-slate-50/80 p-5">
                  <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                        {item.stage} · {item.contact_channel}
                      </p>
                      <h3 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{item.lead_name}</h3>
                      <p className="mt-1 text-sm text-slate-600">{item.company_name}</p>
                    </div>
                    <PriorityBadge priority={item.priority} />
                  </div>
                  <p className="mt-4 text-sm font-medium text-slate-700">Next step</p>
                  <p className="mt-1 text-sm leading-6 text-slate-600">{item.next_step}</p>
                  <p className="mt-4 text-sm font-medium text-slate-700">Context</p>
                  <p className="mt-1 text-sm leading-6 text-slate-600">{item.notes}</p>
                  <div className="mt-5 grid gap-3 md:grid-cols-2">
                    <TimelineTile label="Last touched" value={formatDateTime(item.last_contacted_at)} />
                    <TimelineTile label="Next follow-up" value={formatDateTime(item.next_follow_up_at)} />
                  </div>
                  <div className="mt-5 flex flex-wrap gap-3">
                    <Button disabled={rowPending} onClick={() => runAction(item.id, { action: "complete" })}>
                      {rowPending ? "Updating..." : "Complete"}
                    </Button>
                    <Button
                      variant="outline"
                      disabled={rowPending}
                      onClick={() => runAction(item.id, { action: "snooze", snooze_hours: 24 })}
                    >
                      Snooze 1 day
                    </Button>
                    <Button
                      variant="outline"
                      disabled={rowPending}
                      onClick={() => runAction(item.id, { action: "snooze", snooze_hours: 72 })}
                    >
                      Snooze 3 days
                    </Button>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section className="rounded-[1.75rem] border bg-slate-950 p-6 text-slate-50 shadow-[0_24px_90px_-55px_rgba(15,23,42,0.9)]">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-300">Why This Slice</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight">Lead follow-up first.</h2>
          <ul className="mt-5 space-y-3 text-sm leading-6 text-slate-300">
            <li>It creates recurring value every day instead of being a one-time CRM setup screen.</li>
            <li>It surfaces pipeline risk in the simplest possible form: who needs attention right now.</li>
            <li>It gives us a natural foundation for adding contacts, deals, reminders, and notes next.</li>
          </ul>
        </section>
      </section>
    </>
  );
}

function MetricCard({ label, value, tone }: { label: string; value: string; tone: "neutral" | "warning" | "critical" | "positive" }) {
  const toneClass =
    tone === "positive"
      ? "border-emerald-200 bg-emerald-50 text-emerald-900"
      : tone === "warning"
        ? "border-amber-200 bg-amber-50 text-amber-900"
        : tone === "critical"
          ? "border-rose-200 bg-rose-50 text-rose-900"
          : "border-slate-200 bg-white text-slate-900";

  return (
    <div className={`rounded-[1.4rem] border p-5 shadow-sm ${toneClass}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.2em]">{label}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight">{value}</p>
    </div>
  );
}

function PriorityBadge({ priority }: { priority: string }) {
  const className =
    priority === "high"
      ? "border-rose-200 bg-rose-50 text-rose-700"
      : priority === "medium"
        ? "border-amber-200 bg-amber-50 text-amber-700"
        : "border-slate-200 bg-white text-slate-700";

  return (
    <div className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${className}`}>
      {priority} priority
    </div>
  );
}

function TimelineTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border bg-white px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">{label}</p>
      <p className="mt-2 text-sm text-slate-700">{value}</p>
    </div>
  );
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "Not logged yet";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}
