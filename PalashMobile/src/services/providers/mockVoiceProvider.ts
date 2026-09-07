import type { VoiceProvider } from '@/services/types';
import type { VoiceRecognitionResult } from '@/types';
import { SANTALI_DEMO_PHRASES } from '@/data/phrases';

const DEMO_PACING_MS = 900; // simulate the feel of listening/recognising

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Demo voice provider.
 *
 * This does NOT perform real automatic speech recognition (spec §13). It
 * cannot transcribe arbitrary microphone audio. Instead the demo UI lets the
 * teacher pick a known phrase to "speak", and this provider echoes that phrase
 * back as the recognised text -- always flagged `isDemo: true`, `mode: 'DEMO'`.
 * A real on-device ASR provider will implement the same interface later.
 */
export const mockVoiceProvider: VoiceProvider = {
  id: 'mock-voice-demo',
  label: 'Demo Voice Mode (no real ASR)',
  offlineCapable: true,

  async recognize(phraseHint?: string): Promise<VoiceRecognitionResult> {
    await delay(DEMO_PACING_MS);

    const recognized =
      phraseHint && phraseHint.trim().length > 0
        ? phraseHint.trim()
        : SANTALI_DEMO_PHRASES[0]?.hindi;

    return {
      recognizedText: recognized,
      isDemo: true,
      mode: 'DEMO',
      provider: this.id,
      note: 'Demo voice mode: a chosen phrase is simulated, not recognised from live audio.',
    };
  },
};
