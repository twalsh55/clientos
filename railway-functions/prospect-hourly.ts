const apiBaseUrl = (process.env.API_BASE_URL ?? "https://api.brivoly.com").replace(/\/+$/, "");
const telegramSecret = process.env.TELEGRAM_WEBHOOK_SECRET ?? "";
const telegramChatId = process.env.TELEGRAM_CHAT_ID ?? "";

async function main() {
  if (!telegramSecret || !telegramChatId) {
    console.error("Missing TELEGRAM_WEBHOOK_SECRET or TELEGRAM_CHAT_ID.");
    process.exit(1);
  }

  const response = await fetch(`${apiBaseUrl}/api/telegram/webhook`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Bot-Api-Secret-Token": telegramSecret,
    },
    body: JSON.stringify({
      message: {
        text: "/prospect",
        chat: { id: Number(telegramChatId) },
      },
    }),
  });

  const text = await response.text();
  console.log(`Prospect cron trigger status=${response.status} body=${text}`);

  if (!response.ok) {
    process.exit(1);
  }
}

main().catch((error) => {
  console.error("Prospect cron trigger failed", error);
  process.exit(1);
});
