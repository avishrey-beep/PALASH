import AsyncStorage from '@react-native-async-storage/async-storage';

/**
 * Thin, typed wrapper over AsyncStorage.
 *
 * All PALASH keys are namespaced under `palash:` so the storage area is easy to
 * reason about and clear. Values are JSON-serialised. Every method fails soft
 * (logs and returns a fallback) so a storage hiccup never crashes a screen --
 * the app is meant to keep working offline.
 */
const NS = 'palash:';

function key(k: string): string {
  return `${NS}${k}`;
}

export const storageService = {
  async getItem<T>(k: string, fallback: T): Promise<T> {
    try {
      const raw = await AsyncStorage.getItem(key(k));
      if (raw == null) return fallback;
      return JSON.parse(raw) as T;
    } catch (err) {
      console.warn(`[storage] read failed for "${k}":`, err);
      return fallback;
    }
  },

  async setItem<T>(k: string, value: T): Promise<void> {
    try {
      await AsyncStorage.setItem(key(k), JSON.stringify(value));
    } catch (err) {
      console.warn(`[storage] write failed for "${k}":`, err);
    }
  },

  async removeItem(k: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(key(k));
    } catch (err) {
      console.warn(`[storage] remove failed for "${k}":`, err);
    }
  },
};

export const STORAGE_KEYS = {
  session: 'auth.session',
  accounts: 'auth.accounts',
  settings: 'settings',
  translationCache: 'translation.cache',
  savedTranslations: 'translation.saved',
  activity: 'activity.recent',
  userLessons: 'lessons.user',
  userWorksheets: 'worksheets.user',
  userCurricula: 'curriculum.user',
  syncQueue: 'sync.queue',
  syncMeta: 'sync.meta',
} as const;
