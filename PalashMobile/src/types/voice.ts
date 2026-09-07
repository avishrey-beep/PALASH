/**
 * Voice-translation domain types.
 *
 * Until a real on-device ASR model is wired in, the app runs in an explicit
 * DEMO mode. Nothing here simulates recognition of arbitrary speech and then
 * presents it as real ASR (spec §13): the mock provider only recognises a
 * small set of known demo phrases and always self-labels as demo.
 */

export type VoiceState =
  | 'READY'
  | 'LISTENING'
  | 'PROCESSING' // recognising speech (ASR)
  | 'TRANSLATING'
  | 'SPEAKING' // playing target-language audio
  | 'COMPLETE'
  | 'ERROR';

/** Only DEMO is real today; REAL_ASR is reserved for a future provider. */
export type VoiceMode = 'DEMO' | 'REAL_ASR';

export interface VoiceRecognitionResult {
  /** Recognised source-language text, or undefined if nothing matched. */
  recognizedText?: string;
  /** True when the recognised text came from the fixed demo phrase set. */
  isDemo: boolean;
  mode: VoiceMode;
  /** Provider id that produced this. */
  provider: string;
  note?: string;
}
