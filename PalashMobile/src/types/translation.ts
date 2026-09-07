/**
 * Translation domain types.
 *
 * The result carries explicit provenance and honesty metadata so no screen can
 * present a fabricated or over-confident translation:
 *  - `source` says where the text came from (demo dictionary, cache, model...).
 *  - `matchQuality` is a categorical label, never a calibrated probability
 *    (spec §52 forbids presenting fake probabilities).
 *  - `isDemo` marks demo/local translations that are NOT production-grade.
 *  - an unavailable phrase returns outcome `UNAVAILABLE`, never a guessed
 *    translation (spec §2 / §46: no fabrication, no word-by-word invention).
 */

/** UI-level states of the translation screen. */
export type TranslationScreenState =
  | 'EMPTY' // no input yet
  | 'INPUT' // user has typed but not translated
  | 'PROCESSING' // request in flight
  | 'SUCCESS' // fresh translation produced
  | 'CACHED' // served from local cache
  | 'UNAVAILABLE' // no real data for this phrase; nothing fabricated
  | 'ERROR'; // something went wrong

/** Lifecycle outcome returned by the translation service. */
export type TranslationOutcome = 'SUCCESS' | 'CACHED' | 'UNAVAILABLE' | 'ERROR';

/** Where a translation actually originated. */
export type TranslationSource =
  | 'DEMO_DICTIONARY'
  | 'CACHE'
  | 'NEURAL_MODEL'
  | 'NONE';

/** Categorical match description. NOT a probability (spec §52). */
export type MatchQuality = 'exact' | 'normalized' | 'none';

/** Human-review provenance of the underlying data. */
export type VerificationStatus = 'human_verified' | 'unverified' | 'machine';

export interface TranslationRequest {
  text: string;
  sourceLang: string;
  targetLang: string;
}

export interface TranslationResult {
  outcome: TranslationOutcome;

  // echo of the request
  sourceText: string;
  sourceLang: string;
  targetLang: string;

  // present only when outcome is SUCCESS or CACHED
  translatedText?: string;
  script?: string;
  pronunciation?: string;

  // provenance / honesty
  source: TranslationSource;
  verification?: VerificationStatus;
  matchQuality: MatchQuality;
  isDemo: boolean;
  provider: string;
  fromCache: boolean;

  // diagnostics
  latencyMs?: number; // MEASURED wall-clock inside the provider
  note?: string; // human-readable explanation (esp. for UNAVAILABLE/ERROR)
  errorCode?: string;
}

/** A translation the teacher chose to save locally. */
export interface SavedTranslation {
  id: string;
  sourceText: string;
  translatedText: string;
  sourceLang: string;
  targetLang: string;
  script?: string;
  pronunciation?: string;
  savedAt: string; // ISO timestamp
  isDemo: boolean;
}
