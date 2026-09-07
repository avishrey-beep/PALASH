import { storageService, STORAGE_KEYS } from './storageService';
import { normalizePhrase } from '@/data/phrases';
import type { SavedTranslation, TranslationResult } from '@/types';

/**
 * Offline cache + saved-translations store.
 *
 * Offline-first flow (spec): a successful translation is cached locally so the
 * same phrase resolves instantly and fully offline next time, returned with
 * outcome `CACHED`. "Saved" translations are a separate, teacher-curated list.
 *
 * Only translation *text* is cached -- never any audio or child voice data
 * (spec §37/§38).
 */

type CacheMap = Record<string, TranslationResult>;

function cacheKey(sourceLang: string, targetLang: string, text: string): string {
  return `${sourceLang}:${targetLang}:${normalizePhrase(text)}`;
}

export const offlineCacheService = {
  async getCached(
    sourceLang: string,
    targetLang: string,
    text: string,
  ): Promise<TranslationResult | null> {
    const map = await storageService.getItem<CacheMap>(STORAGE_KEYS.translationCache, {});
    const hit = map[cacheKey(sourceLang, targetLang, text)];
    return hit ?? null;
  },

  /** Cache a successful translation for offline reuse. */
  async cache(result: TranslationResult): Promise<void> {
    if (result.outcome !== 'SUCCESS' || !result.translatedText) return;
    const map = await storageService.getItem<CacheMap>(STORAGE_KEYS.translationCache, {});
    map[cacheKey(result.sourceLang, result.targetLang, result.sourceText)] = result;
    await storageService.setItem(STORAGE_KEYS.translationCache, map);
  },

  async clearCache(): Promise<void> {
    await storageService.removeItem(STORAGE_KEYS.translationCache);
  },

  async listSaved(): Promise<SavedTranslation[]> {
    return storageService.getItem<SavedTranslation[]>(STORAGE_KEYS.savedTranslations, []);
  },

  async save(result: TranslationResult): Promise<SavedTranslation | null> {
    if (!result.translatedText) return null;
    const list = await this.listSaved();
    const entry: SavedTranslation = {
      id: `saved-${Date.now()}`,
      sourceText: result.sourceText,
      translatedText: result.translatedText,
      sourceLang: result.sourceLang,
      targetLang: result.targetLang,
      script: result.script,
      pronunciation: result.pronunciation,
      savedAt: new Date().toISOString(),
      isDemo: result.isDemo,
    };
    // De-duplicate on the same source/target text.
    const filtered = list.filter(
      (s) =>
        !(
          normalizePhrase(s.sourceText) === normalizePhrase(entry.sourceText) &&
          s.targetLang === entry.targetLang
        ),
    );
    const next = [entry, ...filtered];
    await storageService.setItem(STORAGE_KEYS.savedTranslations, next);
    return entry;
  },

  async removeSaved(id: string): Promise<void> {
    const list = await this.listSaved();
    await storageService.setItem(
      STORAGE_KEYS.savedTranslations,
      list.filter((s) => s.id !== id),
    );
  },
};
