import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { storageService, STORAGE_KEYS, syncService } from '@/services';

export interface AppSettings {
  sourceLanguage: string;
  targetLanguage: string;
  showPronunciation: boolean;
  hapticsEnabled: boolean;
  /** Device text-to-speech tuning for the (approximate) audio playback. */
  speechRate: number;
  speechPitch: number;
}

const DEFAULT_SETTINGS: AppSettings = {
  sourceLanguage: 'hin',
  targetLanguage: 'sat',
  showPronunciation: true,
  hapticsEnabled: true,
  speechRate: 0.9,
  speechPitch: 1.0,
};

interface SettingsContextValue {
  settings: AppSettings;
  online: boolean;
  pendingSync: number;
  update: (patch: Partial<AppSettings>) => void;
  refreshConnectivity: () => Promise<void>;
}

const SettingsContext = createContext<SettingsContextValue | undefined>(undefined);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);
  const [online, setOnline] = useState(false);
  const [pendingSync, setPendingSync] = useState(0);

  useEffect(() => {
    (async () => {
      const stored = await storageService.getItem<AppSettings>(
        STORAGE_KEYS.settings,
        DEFAULT_SETTINGS,
      );
      setSettings({ ...DEFAULT_SETTINGS, ...stored });
    })();
  }, []);

  const refreshConnectivity = useCallback(async () => {
    const status = await syncService.getStatus();
    setOnline(status.online);
    setPendingSync(status.pending);
  }, []);

  useEffect(() => {
    refreshConnectivity();
  }, [refreshConnectivity]);

  const update = useCallback((patch: Partial<AppSettings>) => {
    setSettings((prev) => {
      const next = { ...prev, ...patch };
      void storageService.setItem(STORAGE_KEYS.settings, next);
      return next;
    });
  }, []);

  const value = useMemo<SettingsContextValue>(
    () => ({ settings, online, pendingSync, update, refreshConnectivity }),
    [settings, online, pendingSync, update, refreshConnectivity],
  );

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error('useSettings must be used within a SettingsProvider');
  return ctx;
}
