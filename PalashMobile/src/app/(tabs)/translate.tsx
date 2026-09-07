import React, { useCallback, useEffect, useRef, useState } from 'react';
import { View } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
import * as Speech from 'expo-speech';
import {
  Screen,
  AppText,
  Input,
  Button,
  Card,
  LanguageSelector,
  TranslationCard,
  StatusBadge,
  LoadingState,
  ErrorBoundary,
} from '@/components';
import { useSettings } from '@/context/SettingsContext';
import { useHaptics } from '@/hooks/useHaptics';
import { translationService, offlineCacheService, activityService } from '@/services';
import { SOURCE_LANGUAGES, TARGET_LANGUAGES, languageName } from '@/data/languages';
import { SANTALI_DEMO_PHRASES, normalizePhrase } from '@/data/phrases';
import { colors, palette, spacing, radius, borderWidth } from '@/theme';
import type { TranslationResult, TranslationScreenState } from '@/types';

/** A few real demo entries offered as tap-to-fill chips (Hindi → Santali). */
const SAMPLE_CHIPS = SANTALI_DEMO_PHRASES.slice(0, 8).map((p) => p.hindi);

function TranslateScreenContent() {
  const { settings, update } = useSettings();
  const haptics = useHaptics();
  const params = useLocalSearchParams<{ phrase?: string | string[] }>();

  const [text, setText] = useState('');
  const [state, setState] = useState<TranslationScreenState>('EMPTY');
  const [result, setResult] = useState<TranslationResult | null>(null);
  const [saved, setSaved] = useState(false);
  const [savedId, setSavedId] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [flash, setFlash] = useState<string | null>(null);

  const flashTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const showFlash = useCallback((msg: string) => {
    setFlash(msg);
    if (flashTimer.current) clearTimeout(flashTimer.current);
    flashTimer.current = setTimeout(() => setFlash(null), 1600);
  }, []);

  // Stop any speech and clear timers when leaving the screen.
  useEffect(() => {
    return () => {
      if (flashTimer.current) clearTimeout(flashTimer.current);
      Speech.stop().catch(() => {});
    };
  }, []);

  const resetOutput = useCallback(() => {
    setResult(null);
    setSaved(false);
    setSavedId(null);
    Speech.stop().catch(() => {});
    setIsSpeaking(false);
  }, []);

  const onChangeText = (value: string) => {
    setText(value);
    if (result) resetOutput();
    setState(value.trim().length === 0 ? 'EMPTY' : 'INPUT');
  };

  const changeSource = (code: string) => {
    update({ sourceLanguage: code });
    resetOutput();
    setState(text.trim() ? 'INPUT' : 'EMPTY');
  };

  const changeTarget = (code: string) => {
    update({ targetLanguage: code });
    resetOutput();
    setState(text.trim() ? 'INPUT' : 'EMPTY');
  };

  const runTranslate = useCallback(
    async (input: string) => {
      const phrase = input.trim();
      if (phrase.length === 0) return;

      resetOutput();
      setState('PROCESSING');

      const res = await translationService.translate({
        text: phrase,
        sourceLang: settings.sourceLanguage,
        targetLang: settings.targetLanguage,
      });
      setResult(res);
      setState(res.outcome); // SUCCESS | CACHED | UNAVAILABLE | ERROR

      if (res.outcome === 'SUCCESS' || res.outcome === 'CACHED') {
        haptics.success();
        // Reflect whether this phrase is already in the saved list.
        const savedList = await offlineCacheService.listSaved();
        const match = savedList.find(
          (s) =>
            normalizePhrase(s.sourceText) === normalizePhrase(res.sourceText) &&
            s.targetLang === res.targetLang,
        );
        setSaved(!!match);
        setSavedId(match?.id ?? null);
        await activityService.log({
          kind: 'translation',
          title: res.sourceText,
          subtitle: `${languageName(res.sourceLang)} → ${languageName(res.targetLang)}`,
        });
      } else {
        haptics.warn();
      }
    },
    [settings.sourceLanguage, settings.targetLanguage, haptics, resetOutput],
  );

  // Deep-link: a `phrase` param (e.g. tapping vocabulary in a lesson) prefills
  // and runs the translation once.
  const handledPhrase = useRef<string | null>(null);
  useEffect(() => {
    const raw = params.phrase;
    const phrase = Array.isArray(raw) ? raw[0] : raw;
    if (phrase && phrase !== handledPhrase.current) {
      handledPhrase.current = phrase;
      setText(phrase);
      void runTranslate(phrase);
    }
  }, [params.phrase, runTranslate]);

  const onUseChip = (phrase: string) => {
    setText(phrase);
    void runTranslate(phrase);
  };

  const onCopy = async () => {
    if (!result?.translatedText) return;
    await Clipboard.setStringAsync(result.translatedText);
    haptics.tap();
    showFlash('Copied to clipboard');
  };

  const onSave = async () => {
    if (!result?.translatedText) return;
    if (saved && savedId) {
      await offlineCacheService.removeSaved(savedId);
      setSaved(false);
      setSavedId(null);
      showFlash('Removed from saved');
    } else {
      const entry = await offlineCacheService.save(result);
      setSaved(true);
      setSavedId(entry?.id ?? null);
      showFlash('Saved for offline use');
    }
  };

  const onPlayAudio = () => {
    if (!result?.translatedText) return;
    if (isSpeaking) {
      Speech.stop().catch(() => {});
      setIsSpeaking(false);
      return;
    }
    // No real Santali TTS voice exists on-device; we speak the romanised
    // pronunciation as an APPROXIMATION using the platform speech engine.
    // This is never presented as a genuine Santali AI voice (spec §13).
    const toSpeak = result.pronunciation || result.translatedText;
    try {
      setIsSpeaking(true);
      Speech.speak(toSpeak, {
        rate: settings.speechRate,
        pitch: settings.speechPitch,
        onDone: () => setIsSpeaking(false),
        onStopped: () => setIsSpeaking(false),
        onError: () => setIsSpeaking(false),
      });
    } catch {
      setIsSpeaking(false);
      showFlash('Audio is not available on this device');
    }
  };

  const onAgain = () => {
    setText('');
    resetOutput();
    setState('EMPTY');
  };

  const showChips = settings.targetLanguage === 'sat';
  const canTranslate = text.trim().length > 0 && state !== 'PROCESSING';

  return (
    <Screen title="Translate" subtitle="Hindi → mother tongue">
      {/* language row */}
      <View style={{ flexDirection: 'row', gap: spacing.md, marginBottom: spacing.lg }}>
        <LanguageSelector
          label="From"
          value={settings.sourceLanguage}
          options={SOURCE_LANGUAGES}
          onChange={changeSource}
          style={{ flex: 1 }}
        />
        <View style={{ justifyContent: 'flex-end', paddingBottom: spacing.md }}>
          <Ionicons name="arrow-forward" size={20} color={colors.textMuted} />
        </View>
        <LanguageSelector
          label="To"
          value={settings.targetLanguage}
          options={TARGET_LANGUAGES}
          onChange={changeTarget}
          style={{ flex: 1 }}
        />
      </View>

      <Input
        label="Phrase to translate"
        value={text}
        onChangeText={onChangeText}
        placeholder="e.g. बैठ जाओ"
        multiline
        numberOfLines={3}
        helperText="Type a full phrase — translation uses whole-sentence context, not word-by-word."
        style={{ marginBottom: spacing.lg }}
      />

      <Button
        title="Translate"
        icon="arrow-forward-circle-outline"
        onPress={() => void runTranslate(text)}
        disabled={!canTranslate}
        fullWidth
      />

      {/* demo phrase chips */}
      {showChips && (state === 'EMPTY' || state === 'INPUT' || state === 'UNAVAILABLE') ? (
        <View style={{ marginTop: spacing.xl }}>
          <AppText variant="label" color={colors.textMuted} style={{ marginBottom: spacing.sm }}>
            TRY A DEMO PHRASE
          </AppText>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm }}>
            {SAMPLE_CHIPS.map((phrase) => (
              <Button key={phrase} title={phrase} variant="outline" size="sm" onPress={() => onUseChip(phrase)} />
            ))}
          </View>
        </View>
      ) : null}

      {/* transient feedback */}
      {flash ? (
        <View style={{ marginTop: spacing.lg }}>
          <StatusBadge label={flash} tone="success" icon="checkmark-circle-outline" />
        </View>
      ) : null}

      {/* result region */}
      <View style={{ marginTop: spacing.xl }}>
        {state === 'PROCESSING' ? <LoadingState label="Translating…" /> : null}

        {(state === 'SUCCESS' || state === 'CACHED') && result ? (
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
              Play audio uses your device's built-in speech engine as an approximation. It is not a
              Santali AI voice.
            </AppText>
          </>
        ) : null}

        {state === 'UNAVAILABLE' && result ? (
          <Card backgroundColor={palette.sand} shadowSize="md">
            <View style={{ flexDirection: 'row', gap: spacing.md, alignItems: 'flex-start' }}>
              <View
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: radius.sm,
                  borderWidth: borderWidth.thin,
                  borderColor: colors.border,
                  backgroundColor: colors.surface,
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Ionicons name="alert-circle-outline" size={22} color={colors.text} />
              </View>
              <View style={{ flex: 1 }}>
                <AppText variant="bodyStrong">Not in the demo dictionary</AppText>
                <AppText variant="bodySmall" color={colors.textMuted} style={{ marginTop: spacing.xxs }}>
                  {result.note}
                </AppText>
                <AppText variant="caption" color={colors.textMuted} style={{ marginTop: spacing.sm }}>
                  Nothing was invented — PALASH only shows translations it can verify.
                </AppText>
              </View>
            </View>
          </Card>
        ) : null}

        {state === 'ERROR' && result ? (
          <Card backgroundColor={colors.surface} borderColor={colors.danger} shadowSize="md">
            <View style={{ flexDirection: 'row', gap: spacing.md, alignItems: 'center' }}>
              <Ionicons name="close-circle-outline" size={24} color={colors.danger} />
              <View style={{ flex: 1 }}>
                <AppText variant="bodyStrong" color={colors.danger}>
                  Couldn't translate
                </AppText>
                <AppText variant="bodySmall" color={colors.textMuted} style={{ marginTop: spacing.xxs }}>
                  {result.note}
                </AppText>
              </View>
            </View>
            <Button title="Try again" icon="refresh-outline" variant="outline" size="sm" onPress={() => void runTranslate(text)} style={{ marginTop: spacing.md, alignSelf: 'flex-start' }} />
          </Card>
        ) : null}
      </View>
    </Screen>
  );
}

export default function TranslateScreen() {
  return (
    <ErrorBoundary fallbackTitle="Translate error">
      <TranslateScreenContent />
    </ErrorBoundary>
  );
}
