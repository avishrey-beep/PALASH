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
  ErrorBoundary,
} from '@/components';
import { useSettings } from '@/context/SettingsContext';
import { useHaptics } from '@/hooks/useHaptics';
import { voiceService, translationService, offlineCacheService, activityService } from '@/services';
import { SANTALI_DEMO_PHRASES, normalizePhrase } from '@/data/phrases';
import { languageName } from '@/data/languages';
import { colors, palette, spacing, radius, borderWidth } from '@/theme';
import type { TranslationResult, VoiceState } from '@/types';

const DEMO_PHRASES = SANTALI_DEMO_PHRASES.slice(0, 8).map((p) => p.hindi);

const STATE_LABEL: Record<VoiceState, string> = {
  READY: 'Pick a phrase, then tap to speak',
  LISTENING: 'Listening… (demo)',
  PROCESSING: 'Recognising…',
  TRANSLATING: 'Translating…',
  SPEAKING: 'Playing audio…',
  COMPLETE: 'Done',
  ERROR: 'Something went wrong',
};

function VoiceScreenContent() {
  const { settings } = useSettings();
  const haptics = useHaptics();

  const [selected, setSelected] = useState<string | null>(null);
  const [state, setState] = useState<VoiceState>('READY');
  const [recognized, setRecognized] = useState<string | null>(null);
  const [result, setResult] = useState<TranslationResult | null>(null);
  const [saved, setSaved] = useState(false);
  const [savedId, setSavedId] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const pulse = useRef(new Animated.Value(1)).current;
  const busy = state === 'LISTENING' || state === 'PROCESSING' || state === 'TRANSLATING';

  useEffect(() => {
    if (state === 'LISTENING') {
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
  }, [state, pulse]);

  useEffect(() => {
    return () => {
      Speech.stop().catch(() => {});
    };
  }, []);

  const reset = useCallback(() => {
    setRecognized(null);
    setResult(null);
    setSaved(false);
    setSavedId(null);
    Speech.stop().catch(() => {});
    setIsSpeaking(false);
  }, []);

  const pickPhrase = (phrase: string) => {
    setSelected(phrase);
    reset();
    setState('READY');
  };

  const handleListen = useCallback(async () => {
    if (!selected || busy) return;
    reset();
    haptics.tap();

    // 1. "Listen" + recognise (demo: echoes the chosen phrase, no real ASR).
    setState('LISTENING');
    const rec = await voiceService.recognize(selected);
    if (!rec.recognizedText) {
      setState('ERROR');
      haptics.warn();
      return;
    }
    setRecognized(rec.recognizedText);

    // 2. Translate the recognised Hindi via the same honest pipeline.
    setState('TRANSLATING');
    const res = await translationService.translate({
      text: rec.recognizedText,
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
        subtitle: 'Demo voice · Hindi → Santali',
      });
    } else {
      setState('ERROR');
      haptics.warn();
    }
  }, [selected, busy, reset, haptics]);

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
    reset();
    setState('READY');
  };

  const micColor = state === 'LISTENING' ? colors.accent : busy ? colors.textMuted : colors.primary;

  return (
    <Screen title="Voice" subtitle="Speak a phrase, hear the mother tongue">
      {/* Honest demo-mode banner */}
      <Card backgroundColor={palette.sand} shadowSize="sm" style={{ marginBottom: spacing.xl }}>
        <View style={{ flexDirection: 'row', gap: spacing.sm, alignItems: 'flex-start' }}>
          <Ionicons name="information-circle-outline" size={20} color={colors.text} />
          <View style={{ flex: 1 }}>
            <AppText variant="bodyStrong">Demo Voice Mode</AppText>
            <AppText variant="bodySmall" color={colors.textMuted} style={{ marginTop: spacing.xxs }}>
              This is not live speech recognition. Choose a phrase below to simulate speaking it —
              PALASH does not transcribe arbitrary audio yet, and no child voice is recorded or
              stored.
            </AppText>
          </View>
        </View>
      </Card>

      {/* Language direction (fixed for the voice demo) */}
      <View style={{ flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.lg }}>
        <StatusBadge label={languageName('hin')} tone="neutral" />
        <Ionicons name="arrow-forward" size={18} color={colors.textMuted} />
        <StatusBadge label={languageName('sat')} tone="neutral" />
      </View>

      {/* Mic control */}
      <View style={{ alignItems: 'center', marginBottom: spacing.lg }}>
        <Animated.View style={{ transform: [{ scale: pulse }] }}>
          <Pressable
            onPress={() => void handleListen()}
            disabled={!selected || busy}
            accessibilityRole="button"
            accessibilityLabel="Tap to speak the selected phrase"
            style={{ opacity: !selected ? 0.5 : 1 }}
          >
            {({ pressed }) => (
              <NeoSurface shadowSize="xl" radius={radius.pill} backgroundColor={micColor} pressed={pressed}>
                <View style={{ width: 128, height: 128, borderRadius: radius.pill, alignItems: 'center', justifyContent: 'center' }}>
                  <Ionicons name={state === 'LISTENING' ? 'radio' : 'mic'} size={52} color={colors.white} />
                </View>
              </NeoSurface>
            )}
          </Pressable>
        </Animated.View>
        <AppText variant="bodyStrong" color={colors.textMuted} center style={{ marginTop: spacing.lg }}>
          {STATE_LABEL[state]}
        </AppText>
      </View>

      {/* Phrase picker */}
      <AppText variant="label" color={colors.textMuted} style={{ marginBottom: spacing.sm }}>
        CHOOSE A PHRASE TO SPEAK
      </AppText>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.xl }}>
        {DEMO_PHRASES.map((phrase) => {
          const active = selected === phrase;
          return (
            <Pressable key={phrase} onPress={() => pickPhrase(phrase)} disabled={busy}>
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

      {/* Recognised text (demo) */}
      {recognized && (state === 'TRANSLATING' || state === 'COMPLETE' || state === 'SPEAKING') ? (
        <Card backgroundColor={colors.surfaceMuted} shadowSize="sm" style={{ marginBottom: spacing.md }}>
          <AppText variant="label" color={colors.textMuted}>
            HEARD (SIMULATED)
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

      {state === 'ERROR' ? (
        <Card backgroundColor={colors.surface} borderColor={colors.danger} shadowSize="md">
          <View style={{ flexDirection: 'row', gap: spacing.md, alignItems: 'center' }}>
            <Ionicons name="alert-circle-outline" size={24} color={colors.danger} />
            <View style={{ flex: 1 }}>
              <AppText variant="bodyStrong" color={colors.danger}>
                {result?.note ? 'Not in the demo dictionary' : 'Voice demo error'}
              </AppText>
              <AppText variant="bodySmall" color={colors.textMuted} style={{ marginTop: spacing.xxs }}>
                {result?.note ?? 'Please pick a phrase and try again.'}
              </AppText>
            </View>
          </View>
        </Card>
      ) : null}
    </Screen>
  );
}

export default function VoiceScreen() {
  return (
    <ErrorBoundary fallbackTitle="Voice screen error">
      <VoiceScreenContent />
    </ErrorBoundary>
  );
}
