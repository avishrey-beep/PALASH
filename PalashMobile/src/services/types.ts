import type { TranslationRequest, TranslationResult, VoiceRecognitionResult } from '@/types';

/**
 * Provider interfaces.
 *
 * Screens never talk to a provider directly -- they call the services
 * (`translationService`, `voiceService`), which delegate to whichever provider
 * is configured. This is what lets us swap the mock providers for real
 * FastAPI-backed providers in Phase 5 WITHOUT changing any screen (spec
 * requirement: provider abstraction).
 */

export interface TranslationProvider {
  /** Stable identifier, surfaced in results for provenance. */
  readonly id: string;
  /** Human-readable name for diagnostics/settings. */
  readonly label: string;
  /**
   * Whether this provider works fully offline. The mock/demo provider does;
   * a future network provider would not.
   */
  readonly offlineCapable: boolean;
  translate(request: TranslationRequest): Promise<TranslationResult>;
}

export interface VoiceProvider {
  readonly id: string;
  readonly label: string;
  readonly offlineCapable: boolean;
  /**
   * "Recognise" source-language speech. In the demo provider this does NOT
   * perform real ASR -- see mockVoiceProvider. `phraseHint` lets the demo UI
   * pass the phrase the user chose to simulate speaking.
   */
  recognize(phraseHint?: string): Promise<VoiceRecognitionResult>;
}
