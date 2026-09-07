import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { authService } from '@/services';
import type { Credentials, RegistrationInput, TeacherProfile } from '@/types';

interface AuthContextValue {
  profile: TeacherProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: Credentials) => Promise<{ ok: boolean; error?: string; profile?: TeacherProfile }>;
  register: (input: RegistrationInput) => Promise<{ ok: boolean; error?: string; profile?: TeacherProfile }>;
  logout: () => Promise<void>;
  updateProfile: (patch: Partial<TeacherProfile>) => Promise<void>;
  completeOnboarding: (fields: {
    teachingLanguage: string;
    classroomLanguage: string;
  }) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<TeacherProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    (async () => {
      const current = await authService.getCurrent();
      if (active) {
        setProfile(current);
        setIsLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (credentials: Credentials) => {
    const result = await authService.login(credentials);
    if (result.ok && result.profile) setProfile(result.profile);
    return { ok: result.ok, error: result.error, profile: result.profile };
  }, []);

  const register = useCallback(async (input: RegistrationInput) => {
    const result = await authService.register(input);
    if (result.ok && result.profile) setProfile(result.profile);
    return { ok: result.ok, error: result.error, profile: result.profile };
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setProfile(null);
  }, []);

  const updateProfile = useCallback(async (patch: Partial<TeacherProfile>) => {
    const next = await authService.updateProfile(patch);
    if (next) setProfile(next);
  }, []);

  const completeOnboarding = useCallback(
    async (fields: { teachingLanguage: string; classroomLanguage: string }) => {
      const next = await authService.updateProfile({ ...fields, onboarded: true });
      if (next) setProfile(next);
    },
    [],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      profile,
      isLoading,
      isAuthenticated: profile !== null,
      login,
      register,
      logout,
      updateProfile,
      completeOnboarding,
    }),
    [profile, isLoading, login, register, logout, updateProfile, completeOnboarding],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
