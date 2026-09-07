import { storageService, STORAGE_KEYS } from './storageService';
import { DEMO_TEACHER, DEMO_PASSWORD } from '@/data/account';
import { authApi, tokenStore, ApiError } from './apiClient';
import type { Credentials, RegistrationInput, TeacherProfile } from '@/types';

/**
 * Authentication service.
 *
 * Strategy:
 *  1. Try the real FastAPI backend first.
 *  2. On network error, fall back to the local mock store so the demo works
 *     fully offline (spec: offline-first).
 *  3. On successful backend login the JWT tokens are kept in memory and the
 *     profile is persisted to AsyncStorage so `getCurrent()` works across
 *     screen navigations without re-fetching.
 */

interface StoredAccount {
  profile: TeacherProfile;
  password: string;
}

export interface AuthResult {
  ok: boolean;
  profile?: TeacherProfile;
  error?: string;
}

// ─── Local (offline) helpers ──────────────────────────────────────────────────

async function loadAccounts(): Promise<StoredAccount[]> {
  const accounts = await storageService.getItem<StoredAccount[]>(STORAGE_KEYS.accounts, []);
  if (!accounts.some((a) => a.profile.email.toLowerCase() === DEMO_TEACHER.email.toLowerCase())) {
    accounts.push({ profile: { ...DEMO_TEACHER }, password: DEMO_PASSWORD });
    await storageService.setItem(STORAGE_KEYS.accounts, accounts);
  }
  return accounts;
}

async function saveAccounts(accounts: StoredAccount[]): Promise<void> {
  await storageService.setItem(STORAGE_KEYS.accounts, accounts);
}

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/** Map a backend user response to the frontend TeacherProfile shape. */
function backendUserToProfile(
  user: { id: string; username: string; full_name: string | null; school_id: string | null },
  email: string,
  extra?: Partial<TeacherProfile>,
): TeacherProfile {
  return {
    id: user.id,
    name: user.full_name ?? user.username,
    email,
    school: user.school_id ?? '',
    teachingLanguage: extra?.teachingLanguage ?? 'hin',
    classroomLanguage: extra?.classroomLanguage ?? 'sat',
    preferredLanguage: extra?.preferredLanguage ?? 'sat',
    onboarded: extra?.onboarded ?? false,
  };
}

// ─── Auth service ─────────────────────────────────────────────────────────────

export const authService = {
  async login({ email, password }: Credentials): Promise<AuthResult> {
    // 1. Try backend (username = email for the backend login endpoint).
    try {
      const res = await authApi.login(email.trim(), password);
      tokenStore.setTokens(res.access_token, res.refresh_token);

      // Fetch full profile to get email field (login response omits it).
      let profile: TeacherProfile;
      try {
        const me = await authApi.getMe();
        profile = backendUserToProfile(
          { id: me.id, username: me.username, full_name: me.full_name, school_id: me.school_id },
          me.email,
          { preferredLanguage: me.preferred_language ?? 'sat', onboarded: true },
        );
      } catch {
        profile = backendUserToProfile(res.user, email.trim(), { onboarded: true });
      }

      await storageService.setItem(STORAGE_KEYS.session, profile);
      return { ok: true, profile };
    } catch (err) {
      if (err instanceof ApiError && !err.isNetworkError) {
        // Backend rejected credentials -- don't fall back to local.
        return { ok: false, error: err.message };
      }
      // Network error: fall back to local mock store.
    }

    // 2. Offline fallback.
    const accounts = await loadAccounts();
    const account = accounts.find(
      (a) => a.profile.email.toLowerCase() === email.trim().toLowerCase(),
    );
    if (!account) return { ok: false, error: 'No account found for this email.' };
    if (account.password !== password) return { ok: false, error: 'Incorrect password.' };
    await storageService.setItem(STORAGE_KEYS.session, account.profile);
    return { ok: true, profile: account.profile };
  },

  async register(input: RegistrationInput): Promise<AuthResult> {
    const name = input.name.trim();
    const email = input.email.trim();
    if (name.length === 0) return { ok: false, error: 'Please enter your name.' };
    if (!isValidEmail(email)) return { ok: false, error: 'Please enter a valid email address.' };
    if (input.password.length < 4)
      return { ok: false, error: 'Password must be at least 4 characters.' };

    // 1. Try backend registration.
    try {
      const res = await authApi.register({
        username: email.trim(),
        email: email.trim(),
        password: input.password,
        full_name: name,
        school_id: input.school.trim() || undefined,
      });

      // Auto-login after registration.
      const loginRes = await authApi.login(email.trim(), input.password);
      tokenStore.setTokens(loginRes.access_token, loginRes.refresh_token);

      const profile: TeacherProfile = {
        id: res.id,
        name: res.full_name ?? name,
        email: res.email,
        school: res.school_id ?? input.school.trim(),
        teachingLanguage: 'hin',
        classroomLanguage: input.preferredLanguage,
        preferredLanguage: input.preferredLanguage,
        onboarded: false,
      };
      await storageService.setItem(STORAGE_KEYS.session, profile);
      return { ok: true, profile };
    } catch (err) {
      if (err instanceof ApiError && !err.isNetworkError) {
        return { ok: false, error: err.message };
      }
      // Network error: fall back to local mock store.
    }

    // 2. Offline fallback.
    const accounts = await loadAccounts();
    if (accounts.some((a) => a.profile.email.toLowerCase() === email.toLowerCase())) {
      return { ok: false, error: 'An account with this email already exists.' };
    }
    const profile: TeacherProfile = {
      id: `teacher-${Date.now()}`,
      name,
      email,
      school: input.school.trim(),
      teachingLanguage: 'hin',
      classroomLanguage: input.preferredLanguage,
      preferredLanguage: input.preferredLanguage,
      onboarded: false,
    };
    accounts.push({ profile, password: input.password });
    await saveAccounts(accounts);
    await storageService.setItem(STORAGE_KEYS.session, profile);
    return { ok: true, profile };
  },

  async getCurrent(): Promise<TeacherProfile | null> {
    return storageService.getItem<TeacherProfile | null>(STORAGE_KEYS.session, null);
  },

  async logout(): Promise<void> {
    tokenStore.clearTokens();
    await storageService.removeItem(STORAGE_KEYS.session);
  },

  /** Persist profile changes locally and, if online, sync to the backend. */
  async updateProfile(patch: Partial<TeacherProfile>): Promise<TeacherProfile | null> {
    const current = await this.getCurrent();
    if (!current) return null;
    const next: TeacherProfile = { ...current, ...patch, id: current.id, email: current.email };
    await storageService.setItem(STORAGE_KEYS.session, next);

    // Best-effort backend sync.
    if (tokenStore.isAuthenticated()) {
      try {
        await authApi.updateMe({
          full_name: next.name,
          preferred_language: next.preferredLanguage,
        });
      } catch {
        // Ignore -- local update already applied.
      }
    }

    // Also update local account store.
    const accounts = await loadAccounts();
    const idx = accounts.findIndex((a) => a.profile.id === current.id);
    if (idx >= 0) {
      accounts[idx].profile = next;
      await saveAccounts(accounts);
    }
    return next;
  },
};
