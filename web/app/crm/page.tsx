import Link from "next/link";
import { cookies } from "next/headers";

import { BrandLockup } from "@/components/brand-lockup";
import { Button } from "@/components/ui/button";
import { BRIVOLY_SESSION_COOKIE, LEGACY_TRADE_SESSION_COOKIE } from "@/lib/auth";
import { getCrmFollowUpOverview, getSession, getSettingsBootstrap } from "@/lib/api";

export default async function CRMPortalPage() {
  const cookieStore = await cookies();
  const sessionToken =
    cookieStore.get(BRIVOLY_SESSION_COOKIE)?.value ?? cookieStore.get(LEGACY_TRADE_SESSION_COOKIE)?.value ?? null;
  const sessionCookie = cookieStore.get("__session")?.value;
  const cookieHeader = sessionCookie ? `__session=${sessionCookie}` : null;

  const [bootstrap, session] = await Promise.all([
    getSettingsBootstrap().catch(() => null),
    getSession({ sessionToken, cookieHeader }).catch(() => null),
  ]);

  const user = session?.user;
  const followUps = user ? await getCrmFollowUpOverview({ sessionToken, cookieHeader }).catch(() => null) : null;

  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl px-4 py-6 lg:px-8">
      <section className="overflow-hidden rounded-[2rem] border bg-white/85 p-6 shadow-[0_30px_100px_-55px_rgba(15,23,42,0.4)] backdrop-blur md:p-8">
        <div className="flex flex-col gap-8 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <div className="flex items-center gap-4">
              <BrandLockup size="lg" priority />
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-rose-500">CRM Portal</p>
                <h1 className="mt-2 text-4xl font-semibold tracking-tight text-slate-950 md:text-5xl">
                  Relationship ops, pipeline visibility, and follow-up memory.
                </h1>
              </div>
            </div>
            <p className="mt-6 max-w-2xl text-base leading-7 text-slate-600">
              This portal gives the CRM product its own destination now, even before the full workflow surface lands.
              It is the place to grow deal tracking, notes, customer follow-up, and operator context without cluttering
              the crash-monitor experience.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link href="/">Back to portal hub</Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/crash-monitor">Open crash monitor</Link>
              </Button>
              {!user && bootstrap?.clerk_sign_in_url ? (
                <Button asChild size="lg" variant="outline">
                  <Link href="/sign-in?redirectTo=%2Fcrm">Sign in</Link>
                </Button>
              ) : null}
            </div>
          </div>

          <div className="w-full max-w-md rounded-[1.75rem] border bg-slate-950 p-5 text-slate-50 shadow-[0_24px_80px_-50px_rgba(15,23,42,0.9)]">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-300">Portal Status</p>
            <div className="mt-4 space-y-3">
              <CRMStatusRow label="Session" value={user ? "Signed in" : "Guest mode"} />
              <CRMStatusRow label="Product state" value={followUps ? "Follow-up queue live" : "Sign in to load queue"} />
              <CRMStatusRow label="Next focus" value="Lead follow-up discipline" />
            </div>
          </div>
        </div>
      </section>

      {followUps ? (
        <>
          <section className="mt-6 grid gap-6 md:grid-cols-4">
            <MetricCard label="Open follow-ups" value={String(followUps.total_open)} tone="neutral" />
            <MetricCard label="Due today" value={String(followUps.due_today)} tone="warning" />
            <MetricCard label="Overdue" value={String(followUps.overdue)} tone={followUps.overdue > 0 ? "critical" : "positive"} />
            <MetricCard label="High priority" value={String(followUps.high_priority)} tone="neutral" />
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <section className="rounded-[1.75rem] border bg-white/80 p-6 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Lead Follow-Up Queue</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">Who needs a follow-up next.</h2>
              <div className="mt-6 space-y-4">
                {followUps.items.map((item) => (
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
                  </article>
                ))}
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
      ) : (
        <section className="mt-6 grid gap-6 lg:grid-cols-3">
          <FeatureCard
            title="Pipeline"
            body="Track active deals, stages, blockers, and next actions in one operational queue."
          />
          <FeatureCard
            title="Relationship Memory"
            body="Keep notes, conversations, and context close to the account instead of scattered across inboxes."
          />
          <FeatureCard
            title="Follow-up Rhythm"
            body="Use reminders and lightweight workflows to keep opportunities warm without manual sprawl."
          />
        </section>
      )}
    </main>
  );
}

function CRMStatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">{label}</p>
      <p className="text-right text-sm text-slate-100">{value}</p>
    </div>
  );
}

function FeatureCard({ title, body }: { title: string; body: string }) {
  return (
    <section className="rounded-[1.6rem] border bg-white/80 p-6 shadow-sm">
      <h2 className="text-2xl font-semibold tracking-tight text-slate-950">{title}</h2>
      <p className="mt-3 text-sm leading-7 text-slate-600">{body}</p>
    </section>
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
