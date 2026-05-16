const apiBaseUrl = (process.env.API_BASE_URL ?? "https://api.brivoly.com").replace(/\/+$/, "");
const internalCronSecret = process.env.INTERNAL_CRON_SECRET ?? "";

async function main() {
  if (!internalCronSecret) {
    console.error("Missing INTERNAL_CRON_SECRET.");
    process.exit(1);
  }

  const response = await fetch(`${apiBaseUrl}/api/internal/operator-briefing`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Internal-Cron-Secret": internalCronSecret,
    },
    body: JSON.stringify({ trigger: "railway-cron" }),
  });

  const text = await response.text();
  console.log(`Operator daily trigger status=${response.status} body=${text}`);

  if (!response.ok) {
    process.exit(1);
  }
}

main().catch((error) => {
  console.error("Operator daily trigger failed", error);
  process.exit(1);
});
