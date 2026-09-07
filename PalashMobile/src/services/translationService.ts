import type { TranslationProvider } from './types';
import { mockTranslationProvider } from './providers/mockTranslationProvider';
import { offlineCacheService } from './offlineCacheService';
import type { TranslationRequest, TranslationResult } from '@/types';

/**
 * Translation service -- the ONLY translation entry point for screens.
 *
 * Responsibilities:
 *  1. Validate input (empty text -> ERROR, never a fabricated result).
 *  2. Check the offline cache first; a hit is returned as outcome `CACHED`.
 *  3. Delegate to the configured provider (mock/demo today, FastAPI later).
 *  4. Cache successful results for offline reuse.
 *
 * The provider is swappable via `configureTranslationProvider`, so Phase 5 can
 * plug in a real backend provider without touching any screen.
 */

let provider: TranslationProvider = mockTranslationProvider;

export function configureTranslationProvider(next: TranslationProvider): void {
  provider = next;
}

export function getActiveTranslationProvider(): TranslationProvider {
  return provider;
}

export const translationService = {
  async translate(request: TranslationRequest): Promise<TranslationResult> {
    const text = request.text?.trim() ?? '';

    if (text.length === 0) {
      return {
        outcome: 'ERROR',
        sourceText: request.text ?? '',
        sourceLang: request.sourceLang,
        targetLang: request.targetLang,
        source: 'NONE',
        matchQuality: 'none',
        isDemo: true,
        provider: provider.id,
        fromCache: false,
        errorCode: 'EMPTY_INPUT',
        note: 'Please type something to translate.',
      };
    }

    // 1. Offline cache first.
    try {
      const cached = await offlineCacheService.getCached(
        request.sourceLang,
        request.targetLang,
        text,
      );
      if (cached?.translatedText) {
        return { ...cached, outcome: 'CACHED', fromCache: true, source: 'CACHE' };
      }
    } catch {
      // Cache is best-effort; fall through to the provider.
    }

    // 2. Provider.
    try {
      const result = await provider.translate({ ...request, text });
      if (result.outcome === 'SUCCESS') {
        await offlineCacheService.cache(result);
      }
      return result;
    } catch (err) {
      return {
        outcome: 'ERROR',
        sourceText: text,
        sourceLang: request.sourceLang,
        targetLang: request.targetLang,
        source: 'NONE',
        matchQuality: 'none',
        isDemo: true,
        provider: provider.id,
        fromCache: false,
        errorCode: 'PROVIDER_ERROR',
        note: 'Something went wrong while translating. Please try again.',
      };
    }
  },
};
