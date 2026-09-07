import type { VoiceProvider } from './types';
import { mockVoiceProvider } from './providers/mockVoiceProvider';
import type { VoiceRecognitionResult } from '@/types';

/**
 * Voice service -- the single entry point for voice recognition.
 *
 * Today it delegates to the demo provider (no real ASR). A real on-device ASR
 * provider can be configured later via `configureVoiceProvider` without
 * changing the voice screen.
 */

let provider: VoiceProvider = mockVoiceProvider;

export function configureVoiceProvider(next: VoiceProvider): void {
  provider = next;
}

export function getActiveVoiceProvider(): VoiceProvider {
  return provider;
}

export const voiceService = {
  isDemoMode(): boolean {
    // The demo provider is not real ASR; expose that so the UI can label it.
    return provider.id === mockVoiceProvider.id;
  },

  async recognize(phraseHint?: string): Promise<VoiceRecognitionResult> {
    return provider.recognize(phraseHint);
  },
};
