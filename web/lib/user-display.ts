import type { AccountSettings, AuthenticatedUser } from "@/lib/types";

export function resolveUserDisplayName(
  user: AuthenticatedUser | null | undefined,
  settings: AccountSettings | null | undefined = null,
): string | null {
  const authSubject = user?.auth_subject?.trim();
  const alias = settings?.profile_alias?.trim();
  if (alias) {
    return alias;
  }

  const displayName = user?.display_name?.trim();
  if (displayName && displayName !== authSubject) {
    return displayName;
  }

  const givenName = user?.given_name?.trim();
  if (givenName) {
    return givenName;
  }

  const email = user?.email?.trim();
  if (email) {
    return email.split("@")[0] || email;
  }

  return null;
}
