import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Animated, Pressable, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
import * as Speech from 'expo-speech';
import {
  Screen,
  AppText,
  Card,
  NeoSurface,
  StatusBadge,
  TranslationCard,
} from '@/components';
import { useSettings } from '@/context/SettingsContext';
import { useHaptics } from '@/hooks/useHaptics';
import { useSpeechRecognition } from '@/hooks/useSpeechRecognition';
import { voiceService, translationService, offlineCacheService, activityService } from '@/services';
import { SANTALI_DEMO_PHRASES, normalizePhrase } from '@/data/phrases';
import { languageName } from '@/data/languages';
import { colors, palette, spacing, radius } from '@/theme';
import type { TranslationResult, VoiceState } from '@/types';

/** Short, high-hit-rate phrases (incl. single-word numbers) that reliably
 *  match the offline dictionary — ideal to speak in the live web demo. */
const SUGGESTED = [
  'बैठ जाओ',
  'खड़े हो जाओ',
  'बहुत अच्छा',
  'एक',
  'दो',
  'तीन',
  'यहाँ देखो',
  'हाथ ऊपर करो',
].filter((h) => SANTALI_DEMO_PHRASES.some((p) => p.hindi === h));

export default function VoiceScreen() {
  const { settings } = useSettings();
  const haptics = useHaptics();
  const sr = useSpeechRecognition();
  const liveMode = sr.supported; // real browser speech recognition (web)

  const [selected, setSelected] = useState<string | null>(null);
  const [state, setState] = useState<VoiceState>('READY');
  const [recognized, setRecognized] = useState<string | null>(null);
  const [result, setResult] = useState<TranslationResult | null>(null);
  const [saved, setSaved] = useState(false);
  const [savedId, setSavedId] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const pulse = useRef(new Animated.Value(1)).current;
  const listening = state === 'LISTENING';
  const translating = state === 'PROCESSING' || state === 'TRANSLATING';

  // Pulsing mic while listening.
  useEffect(() => {
    if (listening) {
      const loop = Animated.loop(
        Animated.sequence([
          Animated.timing(pulse, { toValue: 1.09, duration: 480, useNativeDriver: true }),
          Animated.timing(pulse, { toValue: 1, duration: 480, useNativeDriver: true }),
        ]),
      );
      loop.start();
      return () => loop.stop();
    }
    pulse.setValue(1);
  }, [listening, pulse]);

  useEffect(() => {
    return () => {
      Speech.stop().catch(() => {});
    };
  }, []);

  const clearOutput = useCallback(() => {
    setResult(null);
    setRecognized(null);
    setSaved(false);
    setSavedId(null);
    Speech.stop().catch(() => {});
    setIsSpeaking(false);
  }, []);

  // Shared translation step: recognised Hindi -> Santali via the honest pipeline.
  const runTranslation = useCallback(
    async (hindi: string) => {
      setState('TRANSLATING');
      const res = await translationService.translate({
        text: hindi,
        sourceLang: 'hin',
        targetLang: 'sat',
      });
      setResult(res);

      if (res.outcome === 'SUCCESS' || res.outcome === 'CACHED') {
        setState('COMPLETE');
        haptics.success();
        const savedList = await offlineCacheService.listSaved();
        const match = savedList.find(
          (s) =>
            normalizePhrase(s.sourceText) === normalizePhrase(res.sourceText) &&
            s.targetLang === res.targetLang,
        );
        setSaved(!!match);
        setSavedId(match?.id ?? null);
        await activityService.log({
          kind: 'voice',
          title: res.sourceText,
          subtitle: liveMode ? 'Live voice · Hindi → Santali' : 'Demo voice · Hindi → Santali',
        });
      } else {
        setState('ERROR');
        haptics.warn();
      }
    },
    [haptics, liveMode],
  );

  // ── Live mode (web): react to real recognition status/results ──────────────
  useEffect(() => {
    if (!liveMode) return;
    if (sr.status === 'listening') setState('LISTENING');
    else if (sr.status === 'error') setState('ERROR');
  }, [liveMode, sr.status]);

  const lastHandled = useRef('');
  useEffect(() => {
    if (!liveMode) return;
    const text = sr.transcript.trim();
    if (text && text !== lastHandled.current) {
      lastHandled.current = text;
      setRecognized(text);
      void runTranslation(text);
    }
  }, [liveMode, sr.transcript, runTranslation]);

  // ── Demo mode (native/Expo Go): simulate recognition of a chosen phrase ─────
  const handleDemoListen = useCallback(
    async (phraseArg?: string) => {
      if (translating) return;
      // Fall back to the current selection, then the first suggestion, so the
      // mic always does something even before a phrase is picked.
      const phrase = phraseArg ?? selected ?? SUGGESTED[0];
      if (!phrase) return;
      setSelected(phrase);
      clearOutput();
      haptics.tap();

      setState('LISTENING');
      const rec = await voiceService.recognize(phrase);
      if (!rec.recognizedText) {
        setState('ERROR');
        haptics.warn();
        return;
      }
      setRecognized(rec.recognizedText);
      await runTranslation(rec.recognizedText);
    },
    [selected, translating, clearOutput, haptics, runTranslation],
  );

  const onMicPress = useCallback(() => {
    if (liveMode) {
      if (listening) {
        sr.stop();
        return;
      }
      lastHandled.current = '';
      clearOutput();
      sr.reset();
      haptics.tap();
      setState('LISTENING');
      sr.start('hi-IN');
    } else {
      void handleDemoListen();
    }
  }, [liveMode, listening, sr, clearOutput, haptics, handleDemoListen]);

  const pickPhrase = (phrase: string) => {
    if (liveMode) {
      // No mic? Tap a suggestion to run the same translation pipeline.
      clearOutput();
      setSelected(phrase);
      setRecognized(phrase);
      lastHandled.current = phrase;
      void runTranslation(phrase);
    } else {
      // One tap = simulate speaking it + translate, so the phone always responds.
      void handleDemoListen(phrase);
    }
  };

  const onCopy = async () => {
    if (!result?.translatedText) return;
    await Clipboard.setStringAsync(result.translatedText);
    haptics.tap();
  };

  const onSave = async () => {
    if (!result?.translatedText) return;
    if (saved && savedId) {
      await offlineCacheService.removeSaved(savedId);
      setSaved(false);
      setSavedId(null);
    } else {
      const entry = await offlineCacheService.save(result);
      setSaved(true);
      setSavedId(entry?.id ?? null);
    }
  };

  const onPlayAudio = () => {
    if (!result?.translatedText) return;
    if (isSpeaking) {
      Speech.stop().catch(() => {});
      setIsSpeaking(false);
      setState('COMPLETE');
      return;
    }
    const toSpeak = result.pronunciation || result.translatedText;
    try {
      setIsSpeaking(true);
      setState('SPEAKING');
      Speech.speak(toSpeak, {
        rate: settings.speechRate,
        pitch: settings.speechPitch,
        onDone: () => {
          setIsSpeaking(false);
          setState('COMPLETE');
        },
        onStopped: () => setIsSpeaking(false),
        onError: () => {
          setIsSpeaking(false);
          setState('COMPLETE');
        },
      });
    } catch {
      setIsSpeaking(false);
      setState('COMPLETE');
    }
  };

  const onAgain = () => {
    clearOutput();
    lastHandled.current = '';
    setState('READY');
  };

  const micColor = listening ? colors.accent : translating ? colors.textMuted : colors.primary;
  // The mic is always tappable except while a translation is in flight. In demo
  // mode a tap with nothing selected falls back to the first suggested phrase
  // (see handleDemoListen), so the button never sits inert on the phone.
  const micDisabled = translating;

  const hint = (() => {
    if (translating) return 'Translating…';
    if (state === 'SPEAKING') return 'Playing audio…';
    if (listening) return liveMode ? 'Listening… speak in Hindi, then pause' : 'Listening… (demo)';
    if (state === 'ERROR') return sr.error ?? 'Something went wrong';
    if (state === 'COMPLETE') return 'Done';
    return liveMode ? 'Tap the mic and speak a Hindi phrase' : 'Tap a phrase — or the mic — to hear it';
  })();

  return (
    <Screen title="Voice" subtitle="Speak a phrase, hear the mother tongue">
      {/* Mode banner — honest about what is real on this platform */}
      <Card
        backgroundColor={liveMode ? palette.forest : palette.sand}
        shadowSize="sm"
        style={{ marginBottom: spacing.xl }}
      >
        <View style={{ flexDirection: 'row', gap: spacing.sm, alignItems: 'flex-start' }}>
          <Ionicons
            name={liveMode ? 'mic-circle-outline' : 'information-circle-outline'}
            size={20}
            color={liveMode ? colors.white : colors.text}
          />
          <View style={{ flex: 1 }}>
            <AppText variant="bodyStrong" color={liveMode ? colors.white : colors.text}>
              {liveMode ? 'Live voice recognition' : 'Demo Voice Mode'}
            </AppText>
            <AppText
              variant="bodySmall"
              color={liveMode ? colors.white : colors.textMuted}
              style={{ marginTop: spacing.xxs }}
            >
              {liveMode
                ? "Real speech-to-text via your browser (needs internet). Speak a Hindi phrase and it's translated to Santali. No audio is stored."
                : 'This is not live speech recognition. Choose a phrase below to simulate speaking it — real on-device recognition needs a native build, and no child voice is recorded or stored.'}
            </AppText>
          </View>
        </View>
      </Card>

      {/* Language direction (fixed: Hindi → Santali) */}
      <View style={{ flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.lg }}>
        <StatusBadge label={languageName('hin')} tone="neutral" />
        <Ionicons name="arrow-forward" size={18} color={colors.textMuted} />
        <StatusBadge label={languageName('sat')} tone="neutral" />
      </View>

      {/* Mic control */}
      <View style={{ alignItems: 'center', marginBottom: spacing.lg }}>
        <Animated.View style={{ transform: [{ scale: pulse }] }}>
          <Pressable
            onPress={onMicPress}
            disabled={micDisabled}
            accessibilityRole="button"
            accessibilityLabel={listening ? 'Stop recording' : 'Tap to speak'}
            style={{ opacity: micDisabled ? 0.5 : 1 }}
          >
            {({ pressed }) => (
              <NeoSurface shadowSize="xl" radius={radius.pill} backgroundColor={micColor} pressed={pressed}>
                <View style={{ width: 128, height: 128, borderRadius: radius.pill, alignItems: 'center', justifyContent: 'center' }}>
                  <Ionicons name={listening ? 'radio' : 'mic'} size={52} color={colors.white} />
                </View>
              </NeoSurface>
            )}
          </Pressable>
        </Animated.View>
        <AppText variant="bodyStrong" color={colors.textMuted} center style={{ marginTop: spacing.lg }}>
          {hint}
        </AppText>
      </View>

      {/* Phrase suggestions / picker */}
      <AppText variant="label" color={colors.textMuted} style={{ marginBottom: spacing.sm }}>
        {liveMode ? 'TRY SAYING ONE OF THESE (OR TAP)' : 'CHOOSE A PHRASE TO SPEAK'}
      </AppText>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.xl }}>
        {SUGGESTED.map((phrase) => {
          const active = selected === phrase;
          return (
            <Pressable key={phrase} onPress={() => pickPhrase(phrase)} disabled={translating || listening}>
              {({ pressed }) => (
                <NeoSurface
                  shadowSize="sm"
                  backgroundColor={active ? colors.primary : colors.surface}
                  pressed={pressed}
                >
                  <View style={{ paddingVertical: spacing.sm, paddingHorizontal: spacing.md }}>
                    <AppText variant="bodyStrong" color={active ? colors.textOnPrimary : colors.text}>
                      {phrase}
                    </AppText>
                  </View>
                </NeoSurface>
              )}
            </Pressable>
          );
        })}
      </View>

      {/* Live interim transcript while speaking */}
      {liveMode && listening ? (
        <Card backgroundColor={colors.surfaceMuted} shadowSize="sm" style={{ marginBottom: spacing.md }}>
          <AppText variant="label" color={colors.textMuted}>
            HEARING…
          </AppText>
          <AppText variant="title" style={{ marginTop: spacing.xxs }}>
            {sr.interim || '…'}
          </AppText>
        </Card>
      ) : null}

      {/* Recognised text */}
      {recognized && !listening && (translating || state === 'COMPLETE' || state === 'SPEAKING') ? (
        <Card backgroundColor={colors.surfaceMuted} shadowSize="sm" style={{ marginBottom: spacing.md }}>
          <AppText variant="label" color={colors.textMuted}>
            {liveMode ? 'HEARD' : 'HEARD (SIMULATED)'}
          </AppText>
          <AppText variant="title" style={{ marginTop: spacing.xxs }}>
            {recognized}
          </AppText>
        </Card>
      ) : null}

      {/* Result */}
      {(state === 'COMPLETE' || state === 'SPEAKING') && result ? (
        <>
          <TranslationCard
            result={result}
            showPronunciation={settings.showPronunciation}
            saved={saved}
            isSpeaking={isSpeaking}
            onCopy={onCopy}
            onSave={onSave}
            onPlayAudio={onPlayAudio}
            onTranslateAgain={onAgain}
          />
          <AppText variant="caption" color={colors.textMuted} style={{ marginTop: spacing.sm }}>
            Audio is your device's built-in speech as an approximation — not a Santali AI voice.
          </AppText>
        </>
      ) : null}

      {/* Errors */}
      {state === 'ERROR' ? (
        <Card backgroundColor={colors.surface} borderColor={colors.danger} shadowSize="md">
          <View style={{ flexDirection: 'row', gap: spacing.md, alignItems: 'center' }}>
            <Ionicons name="alert-circle-outline" size={24} color={colors.danger} />
            <View style={{ flex: 1 }}>
              <AppText variant="bodyStrong" color={colors.danger}>
                {sr.error ? 'Voice input problem' : result?.note ? 'Not in the demo dictionary' : 'Voice demo error'}
              </AppText>
              <AppText variant="bodySmall" color={colors.textMuted} style={{ marginTop: spacing.xxs }}>
                {sr.error ?? result?.note ?? 'Please pick a phrase and try again.'}
              </AppText>
            </View>
          </View>
        </Card>
      ) : null}
    </Screen>
  );
}
