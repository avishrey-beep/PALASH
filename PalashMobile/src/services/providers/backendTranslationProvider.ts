import type { TranslationProvider } from '@/services/types';
import type { TranslationRequest, TranslationResult } from '@/types';
import { translationApi, ApiError } from '@/services/apiClient';

/**
 * Backend translation provider.
 *
 * Delegates to the FastAPI /api/v1/translation/translate endpoint.
 * Falls back gracefully: network errors return outcome ERROR so the
 * translation service can fall through to the offline cache or mock provider.
 */
export const backendTranslationProvider: TranslationProvider = {
  id: 'backend-palash-api',
  label: 'PALASH Backend API',
  offlineCapable: false,

  async translate(request: TranslationRequest): Promise<TranslationResult> {
    const { text, sourceLang, targetLang } = request;

    const base = {
      sourceText: text,
      sourceLang,
      targetLang,
      provider: this.id,
      isDemo: false,
      fromCache: false,
    } as const;

    try {
      const res = await translationApi.translate(text, sourceLang, targetLang);

      if (res.translated_text) {
        return {
          ...base,
          outcome: 'SUCCESS',
          translatedText: res.translated_text,
          pronunciation: res.pronunciation ?? undefined,
          script: res.script ?? undefined,
          source: 'BACKEND',
          matchQuality: res.confidence != null && res.confidence >= 0.9 ? 'exact' : 'normalized',
          latencyMs: res.latency_ms ?? undefined,
        };
      }

      return {
        ...base,
        outcome: 'UNAVAILABLE',
        source: 'NONE',
        matchQuality: 'none',
        note:
          res.note ??
          "This phrase isn't available in the translation database yet.",
      };
    } catch (err) {
      if (err instanceof ApiError && err.isNetworkError) {
        // Signal to the caller that we're offline so it can fall back.
        return {
          ...base,
          outcome: 'ERROR',
          source: 'NONE',
          matchQuality: 'none',
          errorCode: 'NETWORK_ERROR',
          note: 'No connection to the server. Checking offline cache…',
        };
      }

      return {
        ...base,
        outcome: 'ERROR',
        source: 'NONE',
        matchQuality: 'none',
        errorCode: 'BACKEND_ERROR',
        note:
          err instanceof ApiError
            ? err.message
            : 'Something went wrong while translating.',
      };
    }
  },
};
