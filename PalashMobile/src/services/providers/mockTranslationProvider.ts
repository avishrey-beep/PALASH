import type { TranslationProvider } from '@/services/types';
import type { TranslationRequest, TranslationResult } from '@/types';
import { SANTALI_DEMO_PHRASES, normalizePhrase, type DemoPhrase } from '@/data/phrases';

/** The exact message shown when a phrase has no real demo data (spec §2). */
export const UNAVAILABLE_MESSAGE =
  "This phrase isn't available in the offline demo dictionary yet.";

const UNSUPPORTED_TARGET_MESSAGE =
  'Only Hindi → Santali is available in the offline demo right now. Other languages are not yet supported.';

/** Small artificial pause so the PROCESSING state is visible. NOT reported as
 *  a performance metric anywhere -- purely UI pacing. */
const DEMO_PACING_MS = 280;

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Build the demo lookup index once (normalised Hindi -> phrase). */
const INDEX: Map<string, DemoPhrase> = (() => {
  const m = new Map<string, DemoPhrase>();
  for (const p of SANTALI_DEMO_PHRASES) m.set(normalizePhrase(p.hindi), p);
  return m;
})();

/**
 * Offline demo translation provider.
 *
 * Looks up the input in the real, human-verified Santali demo dictionary. It
 * NEVER fabricates a translation: an unknown phrase returns `UNAVAILABLE` with
 * a clear message. Results are always flagged `isDemo: true` and carry a
 * categorical `matchQuality` (never a fake probability, spec §52).
 */
export const mockTranslationProvider: TranslationProvider = {
  id: 'mock-santali-demo',
  label: 'Offline Demo Dictionary (Santali)',
  offlineCapable: true,

  async translate(request: TranslationRequest): Promise<TranslationResult> {
    const { text, sourceLang, targetLang } = request;

    const base: Pick<
      TranslationResult,
      'sourceText' | 'sourceLang' | 'targetLang' | 'provider' | 'isDemo'
    > = {
      sourceText: text,
      sourceLang,
      targetLang,
      provider: this.id,
      isDemo: true,
    };

    // Only Hindi -> Santali has real demo data. Anything else is honestly
    // reported as unavailable rather than guessed (spec §61).
    if (sourceLang !== 'hin' || targetLang !== 'sat') {
      await delay(DEMO_PACING_MS);
      return {
        ...base,
        outcome: 'UNAVAILABLE',
        source: 'NONE',
        matchQuality: 'none',
        fromCache: false,
        note: UNSUPPORTED_TARGET_MESSAGE,
      };
    }

    const started = Date.now();
    const key = normalizePhrase(text);
    const exact = INDEX.get(key);
    const lookupMs = Date.now() - started; // real measured lookup time

    await delay(DEMO_PACING_MS); // UI pacing only; excluded from lookupMs

    if (exact) {
      return {
        ...base,
        outcome: 'SUCCESS',
        translatedText: exact.targetText,
        script: exact.script,
        pronunciation: exact.pronunciation,
        source: 'DEMO_DICTIONARY',
        verification: exact.verification,
        matchQuality: key === exact.hindi.trim().toLowerCase() ? 'exact' : 'normalized',
        fromCache: false,
        latencyMs: lookupMs,
      };
    }

    return {
      ...base,
      outcome: 'UNAVAILABLE',
      source: 'NONE',
      matchQuality: 'none',
      fromCache: false,
      note: UNAVAILABLE_MESSAGE,
    };
  },
};
