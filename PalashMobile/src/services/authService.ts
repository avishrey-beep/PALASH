import { storageService, STORAGE_KEYS } from './storageService';
import { DEMO_TEACHER, DEMO_PASSWORD } from '@/data/account';
import type { Credentials, RegistrationInput, TeacherProfile } from '@/types';

/**
 * Mock authentication service (Phase 1 -- no backend).
 *
 * This is deliberately NOT real security: accounts and the current session are
 * stored locally in plain form purely so the demo has a believable login/
 * register/onboarding flow. It will be replaced by a real backend auth
 * provider in Phase 5. Nothing here should be mistaken for production auth.
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

async function loadAccounts(): Promise<StoredAccount[]> {
  const accounts = await storageService.getItem<StoredAccount[]>(STORAGE_KEYS.accounts, []);
  // Ensure the public demo account always exists.
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

export const authService = {
  async login({ email, password }: Credentials): Promise<AuthResult> {
    const accounts = await loadAccounts();
    const account = accounts.find(
      (a) => a.profile.email.toLowerCase() === email.trim().toLowerCase(),
    );
    if (!account) {
      return { ok: false, error: 'No account found for this email.' };
    }
    if (account.password !== password) {
      return { ok: false, error: 'Incorrect password.' };
    }
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
    await storageService.removeItem(STORAGE_KEYS.session);
  },

  /** Persist profile changes to both the session and the stored account. */
  async updateProfile(patch: Partial<TeacherProfile>): Promise<TeacherProfile | null> {
    const current = await this.getCurrent();
    if (!current) return null;
    const next: TeacherProfile = { ...current, ...patch, id: current.id, email: current.email };
    await storageService.setItem(STORAGE_KEYS.session, next);

    const accounts = await loadAccounts();
    const idx = accounts.findIndex((a) => a.profile.id === current.id);
    if (idx >= 0) {
      accounts[idx].profile = next;
      await saveAccounts(accounts);
    }
    return next;
  },
};
