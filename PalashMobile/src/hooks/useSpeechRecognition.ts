import { useCallback, useEffect, useRef, useState } from 'react';
import { Platform } from 'react-native';

/**
 * Real speech-to-text via the browser Web Speech API (web target only).
 *
 * HONESTY (spec §2, §13, §61):
 *  - This is genuine speech recognition, NOT a simulation — but it only exists
 *    on the web build in Chromium-based browsers, where `webkitSpeechRecognition`
 *    is provided by the browser. On native (Expo Go) there is no ASR module, so
 *    `supported` is false and callers must fall back to an honest demo mode.
 *  - In Chrome the recognition runs through the browser's ONLINE speech service
 *    (Google), so it needs an internet connection. We surface that plainly in
 *    the UI rather than implying on-device offline recognition.
 *  - No audio is uploaded, stored, or logged by PALASH; the browser streams it
 *    to its speech service only while the user is actively recording, then the
 *    stream ends. We never persist a child's or teacher's voice (spec §37/§38).
 */

export type SpeechRecognitionStatus = 'unsupported' | 'idle' | 'listening' | 'error';

// Minimal typings for the Web Speech API so this compiles without the DOM lib.
interface SRAlternative {
  readonly transcript: string;
  readonly confidence: number;
}
interface SRResult {
  readonly length: number;
  readonly isFinal: boolean;
  readonly [index: number]: SRAlternative;
}
interface SRResultList {
  readonly length: number;
  readonly [index: number]: SRResult;
}
interface SREvent {
  readonly resultIndex: number;
  readonly results: SRResultList;
}
interface SRErrorEvent {
  readonly error: string;
  readonly message?: string;
}
interface MinimalSpeechRecognition {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onstart: (() => void) | null;
  onresult: ((event: SREvent) => void) | null;
  onerror: ((event: SRErrorEvent) => void) | null;
  onend: (() => void) | null;
}
type SpeechRecognitionCtor = new () => MinimalSpeechRecognition;

function getRecognitionCtor(): SpeechRecognitionCtor | null {
  if (Platform.OS !== 'web') return null;
  const w = globalThis as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

function mapError(code: string): string {
  switch (code) {
    case 'not-allowed':
    case 'service-not-allowed':
      return 'Microphone permission was blocked. Allow mic access in the browser and try again.';
    case 'no-speech':
      return "Didn't catch any speech. Tap the mic and speak clearly.";
    case 'audio-capture':
      return 'No microphone was found on this device.';
    case 'network':
      return 'Speech recognition needs an internet connection (it uses the browser service).';
    case 'aborted':
      return 'Recording stopped.';
    default:
      return `Speech recognition error: ${code}`;
  }
}

export interface SpeechRecognitionApi {
  /** True only on web with a Web Speech API implementation available. */
  supported: boolean;
  status: SpeechRecognitionStatus;
  /** Accumulated final transcript for the current utterance. */
  transcript: string;
  /** Live (not-yet-final) partial transcript shown while speaking. */
  interim: string;
  error: string | null;
  /** Begin listening. `lang` is a BCP-47 tag, default Hindi (hi-IN). */
  start: (lang?: string) => void;
  stop: () => void;
  reset: () => void;
}

export function useSpeechRecognition(): SpeechRecognitionApi {
  const supported = getRecognitionCtor() !== null;
  const [status, setStatus] = useState<SpeechRecognitionStatus>(
    supported ? 'idle' : 'unsupported',
  );
  const [transcript, setTranscript] = useState('');
  const [interim, setInterim] = useState('');
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<MinimalSpeechRecognition | null>(null);

  const stop = useCallback(() => {
    try {
      recognitionRef.current?.stop();
    } catch {
      // ignore
    }
  }, []);

  const reset = useCallback(() => {
    setTranscript('');
    setInterim('');
    setError(null);
    setStatus(supported ? 'idle' : 'unsupported');
  }, [supported]);

  const start = useCallback((lang = 'hi-IN') => {
    const Ctor = getRecognitionCtor();
    if (!Ctor) {
      setStatus('unsupported');
      return;
    }
    // Abort any in-flight recognition before starting a new one.
    try {
      recognitionRef.current?.abort();
    } catch {
      // ignore
    }

    const rec = new Ctor();
    rec.lang = lang;
    rec.continuous = false;
    rec.interimResults = true;
    rec.maxAlternatives = 1;

    setTranscript('');
    setInterim('');
    setError(null);

    rec.onstart = () => setStatus('listening');
    rec.onresult = (event: SREvent) => {
      let finalText = '';
      let interimText = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        const text = result[0]?.transcript ?? '';
        if (result.isFinal) finalText += text;
        else interimText += text;
      }
      if (finalText) setTranscript((prev) => `${prev}${finalText}`.trim());
      setInterim(interimText);
    };
    rec.onerror = (event: SRErrorEvent) => {
      setError(mapError(event.error));
      setStatus('error');
    };
    rec.onend = () => {
      setInterim('');
      setStatus((prev) => (prev === 'error' ? prev : 'idle'));
    };

    recognitionRef.current = rec;
    try {
      rec.start();
    } catch {
      // start() throws if called while already running; ignore.
    }
  }, []);

  useEffect(() => {
    return () => {
      try {
        recognitionRef.current?.abort();
      } catch {
        // ignore
      }
    };
  }, []);

  return { supported, status, transcript, interim, error, start, stop, reset };
}
