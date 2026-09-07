import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Speech from 'expo-speech';
import { Screen, AppText, Card, Button, StatusBadge } from '@/components';
import { useSettings } from '@/context/SettingsContext';
import { SANTALI_DEMO_PHRASES } from '@/data/phrases';
import { colors, palette, spacing } from '@/theme';

const RATE_PRESETS = [
  { label: 'Slow', value: 0.75 },
  { label: 'Normal', value: 0.9 },
  { label: 'Fast', value: 1.1 },
];
const PITCH_PRESETS = [
  { label: 'Low', value: 0.85 },
  { label: 'Normal', value: 1.0 },
  { label: 'High', value: 1.15 },
];

const SAMPLE = SANTALI_DEMO_PHRASES[0];

export default function VoiceProfileScreen() {
  const { settings, update } = useSettings();
  const [speaking, setSpeaking] = useState(false);
  const [voiceCount, setVoiceCount] = useState<number | null>(null);

  useEffect(() => {
    let active = true;
    Speech.getAvailableVoicesAsync()
      .then((voices) => {
        if (active) setVoiceCount(voices.length);
      })
      .catch(() => {
        if (active) setVoiceCount(null);
      });
    return () => {
      active = false;
      Speech.stop().catch(() => {});
    };
  }, []);

  const test = () => {
    if (speaking) {
      Speech.stop().catch(() => {});
      setSpeaking(false);
      return;
    }
    try {
      setSpeaking(true);
      Speech.speak(SAMPLE.pronunciation, {
        rate: settings.speechRate,
        pitch: settings.speechPitch,
        onDone: () => setSpeaking(false),
        onStopped: () => setSpeaking(false),
        onError: () => setSpeaking(false),
      });
    } catch {
      setSpeaking(false);
    }
  };

  const near = (a: number, b: number) => Math.abs(a - b) < 0.01;

  return (
    <Screen title="Teacher voice profile" subtitle="Tune audio playback" showBack>
      {/* Honest explanation */}
      <Card backgroundColor={palette.sand} shadowSize="sm" style={{ marginBottom: spacing.xl }}>
        <View style={{ flexDirection: 'row', gap: spacing.sm, alignItems: 'flex-start' }}>
          <Ionicons name="information-circle-outline" size={20} color={colors.text} />
          <View style={{ flex: 1 }}>
            <AppText variant="bodyStrong">How audio works</AppText>
            <AppText variant="bodySmall" color={colors.textMuted} style={{ marginTop: spacing.xxs }}>
              PALASH uses your device's built-in text-to-speech to read the romanised pronunciation.
              This is an approximation to help you, not a recording of a real Santali speaker and not
              a cloned teacher voice. You can adjust the speed and pitch below.
            </AppText>
          </View>
        </View>
      </Card>

      {/* Speed */}
      <AppText variant="label" color={colors.textMuted} style={{ marginBottom: spacing.sm }}>
        SPEAKING SPEED
      </AppText>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.xl }}>
        {RATE_PRESETS.map((p) => (
          <Button
            key={p.label}
            title={p.label}
            variant={near(settings.speechRate, p.value) ? 'primary' : 'outline'}
            size="sm"
            onPress={() => update({ speechRate: p.value })}
          />
        ))}
      </View>

      {/* Pitch */}
      <AppText variant="label" color={colors.textMuted} style={{ marginBottom: spacing.sm }}>
        PITCH
      </AppText>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.xl }}>
        {PITCH_PRESETS.map((p) => (
          <Button
            key={p.label}
            title={p.label}
            variant={near(settings.speechPitch, p.value) ? 'primary' : 'outline'}
            size="sm"
            onPress={() => update({ speechPitch: p.value })}
          />
        ))}
      </View>

      {/* Test */}
      <Card style={{ marginBottom: spacing.lg }}>
        <AppText variant="label" color={colors.textMuted}>
          SAMPLE
        </AppText>
        <AppText variant="title" style={{ marginTop: spacing.xxs }}>
          {SAMPLE.hindi}
        </AppText>
        <AppText variant="script" color={colors.primaryDark} style={{ marginTop: spacing.xs }}>
          {SAMPLE.targetText}
        </AppText>
        <AppText variant="bodyStrong" color={colors.textMuted} style={{ marginTop: spacing.xxs }}>
          {SAMPLE.pronunciation}
        </AppText>
        <Button
          title={speaking ? 'Stop' : 'Test voice'}
          icon={speaking ? 'stop-outline' : 'volume-high-outline'}
          variant="accent"
          onPress={test}
          style={{ marginTop: spacing.lg, alignSelf: 'flex-start' }}
        />
      </Card>

      <StatusBadge
        label={voiceCount === null ? 'Device voices: checking' : `Device voices available: ${voiceCount}`}
        tone="neutral"
        icon="hardware-chip-outline"
      />
      <AppText variant="caption" color={colors.textMuted} style={{ marginTop: spacing.sm }}>
        Available voices depend on your device's language packs. A Santali voice is very unlikely to
        be installed, so playback approximates the sounds using another voice.
      </AppText>
    </Screen>
  );
}
