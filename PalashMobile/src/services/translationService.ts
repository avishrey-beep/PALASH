import type { TranslationProvider } from './types';
import { mockTranslationProvider } from './providers/mockTranslationProvider';
import { backendTranslationProvider } from './providers/backendTranslationProvider';
import { offlineCacheService } from './offlineCacheService';
import { tokenStore } from './apiClient';
import type { TranslationRequest, TranslationResult } from '@/types';

/**
 * Translation service -- the ONLY translation entry point for screens.
 *
 * Provider priority:
 *  1. Offline cache (always checked first -- fastest, works offline).
 *  2. Backend API provider (when the user is authenticated and online).
 *  3. Mock/demo provider (offline fallback with the bundled Santali dictionary).
 *
 * The provider is still swappable via `configureTranslationProvider` for tests.
 */

let _overrideProvider: TranslationProvider | null = null;

export function configureTranslationProvider(next: TranslationProvider): void {
  _overrideProvider = next;
}

export function getActiveTranslationProvider(): TranslationProvider {
  return _overrideProvider ?? (tokenStore.isAuthenticated() ? backendTranslationProvider : mockTranslationProvider);
}

export const translationService = {
  async translate(request: TranslationRequest): Promise<TranslationResult> {
    const text = request.text?.trim() ?? '';
    const activeProvider = getActiveTranslationProvider();

    if (text.length === 0) {
      return {
        outcome: 'ERROR',
        sourceText: request.text ?? '',
        sourceLang: request.sourceLang,
        targetLang: request.targetLang,
        source: 'NONE',
        matchQuality: 'none',
        isDemo: !tokenStore.isAuthenticated(),
        provider: activeProvider.id,
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

    // 2. Primary provider (backend if authenticated, mock otherwise).
    try {
      const result = await activeProvider.translate({ ...request, text });

      // If the backend returned a network error, fall back to the mock provider.
      if (result.errorCode === 'NETWORK_ERROR' && activeProvider.id !== mockTranslationProvider.id) {
        const fallback = await mockTranslationProvider.translate({ ...request, text });
        if (fallback.outcome === 'SUCCESS') {
          await offlineCacheService.cache(fallback);
        }
        return fallback;
      }

      if (result.outcome === 'SUCCESS') {
        await offlineCacheService.cache(result);
      }
      return result;
    } catch (err) {
      // Last-resort fallback to mock provider.
      try {
        return await mockTranslationProvider.translate({ ...request, text });
      } catch {
        return {
          outcome: 'ERROR',
          sourceText: text,
          sourceLang: request.sourceLang,
          targetLang: request.targetLang,
          source: 'NONE',
          matchQuality: 'none',
          isDemo: true,
          provider: activeProvider.id,
          fromCache: false,
          errorCode: 'PROVIDER_ERROR',
          note: 'Something went wrong while translating. Please try again.',
        };
      }
    }
  },
};
