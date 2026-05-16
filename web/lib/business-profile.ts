import type { AccountSettings } from "@/lib/types";

export function isBusinessProfileComplete(settings: AccountSettings | null): boolean {
  if (!settings) {
    return false;
  }
  return Boolean(settings.business_name.trim() && settings.outbound_sender_name.trim());
}

export function shouldPromptForBusinessProfile(settings: AccountSettings | null): boolean {
  if (!settings) {
    return false;
  }
  return !settings.onboarding_profile_deferred && !isBusinessProfileComplete(settings);
}
