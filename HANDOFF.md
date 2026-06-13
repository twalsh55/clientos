# HANDOFF

## Current Project State

Brivoly Client OS is the active product surface in this repo.

- Backend: Python 3.12, FastAPI, `uv`, PostgreSQL via `psycopg`
- Frontend: Next.js, TypeScript, Tailwind, `shadcn/ui`
- Auth: Clerk sessions mapped to internal Postgres-backed users
- Billing: Stripe Checkout / Billing Portal groundwork
- AI: OpenAI API through backend-owned application services
- Notifications: Telegram and SMTP email paths exist
- Deploy targets: Railway for API, Vercel for web
- Primary app route: `/clientos`
- Compatibility route: `/crm`

The product is functionally broad but should be treated as pre-production until the checklist below is complete. The most important production gap is not one missing feature; it is hardening the full system around real auth, durable data, privacy, paid access, connected inbox/calendar reliability, and repeatable release verification.

## Completed In The Latest Session

- Confirmed local Node works through `nvm`.
- Fixed local dev startup so `scripts/dev.sh` sources `nvm` when needed.
- Changed local dev default to in-memory API storage unless `BRIVOLY_DEV_USE_DATABASE=true`, so a stale local Postgres URL does not break guest Client OS checks.
- Fixed the Client OS followups proxy so backend auth/status errors are preserved instead of flattened into a vague 500.
- Updated Playwright e2e mocks and tests to match the current guest Client OS flow.
- Fixed spreadsheet import file selection after the import workspace reset.
- Removed obsolete `web/pages/_document.tsx`, which conflicted with the current Next build.
- Made a broad Client OS layout pass to eliminate stacked/chopped text caused by narrow cards and `overflow-wrap:anywhere`.
- Started the production-readiness checklist by adding a `/readyz` launch guard for anonymous Client OS access:
  - readiness now reports `checks.anonymous_crm.enabled`
  - readiness reports `checks.anonymous_crm.production_safe`
  - readiness degrades in production-like environments when `ALLOW_ANONYMOUS_CRM=true`
- Added `scripts/audit_production_env.py` as a local staging/production preflight:
  - audits Railway API and Vercel web variables from env or dotenv files
  - blocks placeholder values, localhost URLs, and `ALLOW_ANONYMOUS_CRM=true`
  - requires live Clerk/Stripe key prefixes for production
- Tightened `/readyz` for production-like environments so it reports and requires Clerk server-side production readiness:
  - `CLERK_SECRET_KEY`
  - `CLERK_JWKS_URL`
  - `CLERK_ISSUER`
  - `CLERK_AUTHORIZED_PARTIES`
- Verified locally:
  - `uv run pytest`
  - `cd web && npm run typecheck`
  - `cd web && npm run build`
  - `cd web && PLAYWRIGHT_HOST_PLATFORM_OVERRIDE=ubuntu24.04-x64 npm run e2e`
- Pushed latest commits to `origin/master`, ending at:
  - `28b829c Fix Client OS text wrapping layouts`

## Production Readiness Definition

The application is production-ready only when all of these are true:

- Users can sign up, sign in, use Client OS, and sign out through Clerk without guest-mode dependence.
- All relationship memory, settings, imports, connected mailbox/calendar state, notes, drafts, and privacy actions persist in production Postgres.
- Anonymous access is either intentionally disabled in production or explicitly limited to a safe public/demo surface.
- Billing can create, enforce, and manage paid access through Stripe without blocking legitimate users.
- Gmail, Outlook, Google Calendar, and Microsoft Calendar connection paths are either production-configured and tested or hidden behind clear beta/fallback behavior.
- OpenAI usage is configured, observable, rate-limited enough for launch, and respects the user AI-processing setting.
- Export, erase, retention, and consent controls work against real production data.
- API and web deploys are repeatable from clean checkouts.
- `/readyz` catches unsafe production guest-mode configuration before a production smoke check passes.
- `/readyz` catches incomplete production Clerk configuration before a production smoke check passes.
- Hosted smoke tests pass after deploy.
- There is a rollback path for both Railway and Vercel.

## Production Checklist

### 1. Freeze Scope For First Production Release

- Decide the first shipped surface:
  - recommended: `/clientos` relationship memory, Today, Relationships, Inbox memory, Attention, Import, Dropzones, Settings.
- Decide whether guest access is launch behavior:
  - recommended for real production: set `ALLOW_ANONYMOUS_CRM=false`.
  - keep guest mode only for demo/staging if needed.
- Hide or clearly mark any unfinished beta paths:
  - mailbox provider OAuth
  - calendar provider OAuth
  - manual mailbox fallback
  - automation/prospecting surfaces that are not part of Client OS launch

### 2. Production Environments

Create or confirm distinct environments:

- Local development
- Staging API on Railway
- Staging web on Vercel
- Production API on Railway
- Production web on Vercel

Each environment should have its own:

- `DATABASE_URL`
- Clerk app/instance
- Stripe mode and keys
- OAuth app credentials
- webhook secrets
- `APP_BASE_URL`
- `BRIVOLY_API_BASE_URL`

Do not reuse production secrets in local or staging.

### 3. Railway API Configuration

Set required API variables on Railway:

```bash
DATABASE_URL=...
APP_BASE_URL=https://www.brivoly.com
ALLOW_ANONYMOUS_CRM=false
CLERK_SECRET_KEY=...
CLERK_JWKS_URL=...
CLERK_ISSUER=...
CLERK_AUTHORIZED_PARTIES=https://www.brivoly.com
STRIPE_SECRET_KEY=...
STRIPE_PRICE_ID=...
STRIPE_PORTAL_CONFIGURATION_ID=...
APP_OPENAI_API_KEY=...
MAILBOX_WATCH_WEBHOOK_SECRET=...
```

Set optional API variables as needed:

```bash
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
TELEGRAM_WEBHOOK_SECRET=...
SMTP_HOST=...
SMTP_PORT=...
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_FROM_EMAIL=...
SMTP_USE_TLS=true
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
```

Use `APP_OPENAI_API_KEY` for application automation before falling back to `OPENAI_API_KEY`.

### 4. Vercel Web Configuration

Set required Vercel variables:

```bash
BRIVOLY_API_BASE_URL=https://api.brivoly.com
APP_BASE_URL=https://www.brivoly.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/clientos
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/clientos
```

Confirm Vercel project settings:

- Project root: `web/`
- Install command: `npm install`
- Build command: `npm run build`
- Production domain points at the intended Vercel project.
- `www.brivoly.com` and any apex redirect behavior are intentional.

### 5. Clerk Production Setup

- Create or verify the production Clerk application.
- Configure allowed origins and redirect URLs:
  - `https://www.brivoly.com`
  - `https://www.brivoly.com/sign-in`
  - `https://www.brivoly.com/sign-up`
  - `https://www.brivoly.com/clientos`
- Confirm backend token validation uses the production issuer/JWKS.
- Confirm user creation maps Clerk identities into internal Postgres users.
- Test:
  - new signup
  - existing signin
  - signout
  - expired session
  - unauthorized API request

### 6. Postgres Durability

- Provision production Postgres.
- Confirm SSL requirements and Railway connection limits.
- Run the app against production-like Postgres before launch.
- Verify persistence for:
  - account settings
  - imported relationships
  - followups
  - notes
  - timeline entries
  - inbox-ingested threads
  - connected mailbox records
  - connected calendar records
  - privacy export / erase
- Add backup expectations:
  - daily automated backups
  - point-in-time restore if available
  - documented restore drill before public launch
- Confirm no production path depends on process memory for user data.

### 7. Billing And Access

- Configure Stripe production keys and price IDs.
- Confirm Checkout creates the expected subscription.
- Confirm Billing Portal opens for active users.
- Decide exact free/paid boundaries for launch.
- Confirm unpaid/canceled users see calm, useful product messaging.
- Test Stripe webhooks if webhook handling is used for entitlement updates.
- Test:
  - checkout success
  - checkout cancel
  - billing portal return
  - subscription cancellation
  - missing Stripe config

### 8. Inbox And Calendar Integrations

For Gmail / Google Calendar:

- Create production Google Cloud OAuth client.
- Add redirect URIs used by the app.
- Configure scopes for the minimum needed mailbox/calendar behavior.
- Complete Google OAuth verification requirements if external users will connect accounts.

For Outlook / Microsoft Calendar:

- Create production Azure app registration.
- Add redirect URIs used by the app.
- Configure Graph permissions with least privilege.
- Confirm token refresh behavior.

For both providers:

- Test connect, reconnect, disconnect, pause/resume, manual sync, and provider-backed send.
- Test watch/webhook callback handling with `MAILBOX_WATCH_WEBHOOK_SECRET`.
- Confirm provider failures degrade into clear reconnect guidance.
- Hide provider buttons if production credentials or verification are incomplete.

### 9. AI Readiness

- Set `APP_OPENAI_API_KEY` in production.
- Confirm all OpenAI calls happen through backend application services.
- Confirm the frontend does not duplicate core AI/business logic.
- Respect `allow_ai_processing` in account settings.
- Add operational guardrails:
  - request timeout behavior
  - clear fallback copy when AI fails
  - logging without storing sensitive prompt bodies unnecessarily
  - cost visibility
- Test:
  - spreadsheet mapping assist
  - note/image intake
  - reconnect draft generation
  - inbox thread summary/draft paths
  - disabled AI-processing account

### 10. Privacy, GDPR, And Data Controls

- Verify production export:
  - `GET /api/account/privacy/export`
  - settings export action in UI
- Verify production erase:
  - `POST /api/account/privacy/erase`
  - settings erase action in UI
- Confirm erase scope:
  - relationship memory
  - connected mailbox links
  - uploaded context records
  - timeline entries
- Add or confirm:
  - privacy policy
  - terms of service
  - data processor disclosure
  - retention policy
  - user consent copy/versioning
  - support contact path for deletion/export requests
- Confirm logs do not retain sensitive customer data longer than intended.

### 11. Security Hardening

- Confirm CORS only allows intended web origins.
- Confirm auth is required for private API routes.
- Confirm anonymous mode cannot expose another user’s data.
- Confirm secrets are not logged.
- Confirm upload routes enforce:
  - size limits
  - content-type expectations
  - safe storage behavior
  - non-guessable links
- Confirm webhook routes validate secrets/signatures.
- Confirm dependency audit is acceptable:

```bash
cd web && npm audit
uv run pip-audit
```

If `pip-audit` is not installed, install/run it in a temporary dev context or equivalent CI job.

### 12. Observability And Support

- Confirm API request IDs are emitted and useful.
- Add/confirm hosted log access for Railway and Vercel.
- Decide error monitoring:
  - Sentry or equivalent for web and API is recommended before real users.
- Add support visibility for:
  - import failures
  - mailbox sync failures
  - OAuth reconnect-needed states
  - privacy erase/export failures
  - Stripe entitlement issues
- Confirm founder/operator alerts for critical failures through Telegram or email.

### 13. UX Production Pass

- Continue removing stacked/narrow card text before launch.
- Test core flows at:
  - 375px mobile
  - 390px mobile
  - 768px tablet
  - 1280px desktop
  - 1440px desktop
- Core flows to manually inspect:
  - unauthenticated visit
  - sign in/up
  - `/clientos`
  - Today
  - Relationships
  - relationship detail
  - Inbox
  - Attention
  - Import
  - Dropzones / client upload
  - Settings
  - billing actions
  - privacy export/erase
- Keep the product direction:
  - calm relationship memory
  - fewer dashboard-like counters
  - no CRM-heavy language
  - strong defaults over configuration
  - no unnecessary copy/paste or typing

### 14. Verification Before Any Production Deploy

Run from repo root:

```bash
uv sync
./scripts/audit_production_env.py --env-file .env.production --target production
uv run pytest
```

Run from `web/`:

```bash
export NVM_DIR="$HOME/.nvm"
. "$NVM_DIR/nvm.sh"
npm install
npm run typecheck
npm run build
PLAYWRIGHT_HOST_PLATFORM_OVERRIDE=ubuntu24.04-x64 npm run e2e
```

If testing the full local app:

```bash
./scripts/dev.sh
```

Local dev defaults to in-memory storage. Use Postgres explicitly with:

```bash
BRIVOLY_DEV_USE_DATABASE=true ./scripts/dev.sh
```

### 15. Staging Deploy

Deploy to staging before production:

```bash
./scripts/deploy_api.sh
cd web && npx vercel deploy --yes
```

Staging smoke checks:

```bash
curl https://staging-api.example.com/healthz
curl https://staging-api.example.com/readyz
```

Then manually verify:

- Clerk auth round trip
- settings load/save
- Client OS home load
- import preview/import
- relationship detail load
- note draft/send path
- privacy export/erase on test account
- Stripe test checkout if staging uses Stripe test mode
- OAuth connect/disconnect if staging credentials exist

### 16. Production Deploy

Only deploy production when explicitly requested in the current session.

Recommended production flow:

```bash
uv run pytest
cd web && npm run typecheck
cd web && npm run build
cd web && PLAYWRIGHT_HOST_PLATFORM_OVERRIDE=ubuntu24.04-x64 npm run e2e
cd ..
./scripts/deploy_prod.sh
```

Or deploy separately:

```bash
./scripts/deploy_api.sh
./scripts/deploy_web.sh
```

Hosted smoke checks:

```bash
./scripts/smoke_hosted.sh https://api.brivoly.com
curl -I https://www.brivoly.com
```

Post-deploy manual checks:

- Open `https://www.brivoly.com/clientos`.
- Sign up as a new production test user.
- Confirm dashboard/Today shell loads.
- Save settings.
- Import a tiny spreadsheet.
- Open a relationship page.
- Generate or edit a draft.
- Test billing portal/checkout.
- Test privacy export.
- Confirm Railway logs show no unexpected 500s.
- Confirm Vercel logs show no repeated rendering/API errors.

### 17. Rollback Plan

Before deploy:

- Note current Railway deployment ID.
- Note current Vercel production deployment URL.
- Confirm previous Git commit hash.

If API deploy fails:

- Roll back to previous Railway deployment from Railway dashboard.
- Re-run hosted API smoke checks.

If web deploy fails:

- Promote previous Vercel deployment from Vercel dashboard.
- Re-run browser smoke checks.

If database migration/data issue appears:

- Stop deploy/traffic if needed.
- Preserve logs.
- Restore from backup only after identifying the affected time window.

## Known Issues And Risks

- Production readiness depends heavily on correct Clerk, Stripe, OAuth, and database secrets.
- Guest mode is useful for local/demo flows but should not be assumed safe for production private data.
- OAuth provider verification may block public Gmail/Google Calendar launch if not completed early.
- Inbox/calendar sync and provider-backed sending need real-account testing, especially Outlook thread continuity.
- Privacy export/erase exists as groundwork but needs a production legal/privacy review before broad launch.
- UI density has improved, but narrow-card regressions should be checked manually on mobile and tablet before launch.
- Railway CLI can return transient control-plane errors; the deploy script retries known failures, but hosted smoke checks are still required.
- Next route type generation may update `web/next-env.d.ts`; include it only when it is part of a coherent web toolchain change.

## Current Git State

At the time this handoff was updated:

- Branch: `master`
- Latest pushed production-readiness/layout commit: `28b829c Fix Client OS text wrapping layouts`
- `HANDOFF.md` has been rewritten with this production checklist and should be committed if accepted.

## Important Commands

Local verification:

```bash
uv run pytest
cd web && npm run typecheck
cd web && npm run build
cd web && PLAYWRIGHT_HOST_PLATFORM_OVERRIDE=ubuntu24.04-x64 npm run e2e
```

Local dev:

```bash
./scripts/dev.sh
BRIVOLY_DEV_USE_DATABASE=true ./scripts/dev.sh
```

Deploy:

```bash
./scripts/deploy_api.sh
./scripts/deploy_web.sh
./scripts/deploy_prod.sh
```

Railway:

```bash
npx @railway/cli@latest status
npx @railway/cli@latest variable set KEY=value
printf '%s' "$VALUE" | npx @railway/cli@latest variable set KEY --stdin
```

Vercel:

```bash
cd web
npx vercel deploy --yes
npx vercel deploy --prod --yes
```
