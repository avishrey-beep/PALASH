import React from 'react';
import { View } from 'react-native';
import { Card } from './Card';
import { AppText } from './AppText';
import { Button } from './Button';
import { StatusBadge } from './StatusBadge';
import { colors, spacing, borderWidth, radius } from '@/theme';
import { languageName } from '@/data/languages';
import type { TranslationResult } from '@/types';

interface TranslationCardProps {
  result: TranslationResult; // expected outcome SUCCESS or CACHED
  showPronunciation: boolean;
  saved: boolean;
  isSpeaking: boolean;
  onCopy: () => void;
  onSave: () => void;
  onPlayAudio: () => void;
  onTranslateAgain: () => void;
}

/**
 * Renders a successful/cached translation with explicit provenance:
 *  - a CACHED or DEMO DICTIONARY badge and a categorical match label,
 *  - a clear "demo dictionary, not production" disclaimer (spec §10),
 *  - a pronunciation guide labelled as a guide, and
 *  - Copy / Save / Play Audio / Translate Again actions.
 */
export function TranslationCard({
  result,
  showPronunciation,
  saved,
  isSpeaking,
  onCopy,
  onSave,
  onPlayAudio,
  onTranslateAgain,
}: TranslationCardProps) {
  const cached = result.outcome === 'CACHED';

  return (
    <Card shadowSize="lg" padded={false}>
      <View style={{ padding: spacing.lg }}>
        {/* provenance badges */}
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginBottom: spacing.md }}>
          <StatusBadge
            label={cached ? 'Cached' : 'Demo dictionary'}
            tone={cached ? 'cached' : 'success'}
            icon={cached ? 'save-outline' : 'book-outline'}
          />
          {result.matchQuality !== 'none' ? (
            <StatusBadge label={`${result.matchQuality} match`} tone="neutral" />
          ) : null}
          {result.verification === 'human_verified' ? (
            <StatusBadge label="Human-verified source" tone="neutral" icon="shield-checkmark-outline" />
          ) : null}
        </View>

        {/* source */}
        <AppText variant="label" color={colors.textMuted}>
          {languageName(result.sourceLang).toUpperCase()}
        </AppText>
        <AppText variant="title" style={{ marginTop: spacing.xxs }}>
          {result.sourceText}
        </AppText>

        <View
          style={{
            height: borderWidth.thin,
            backgroundColor: colors.border,
            marginVertical: spacing.lg,
          }}
        />

        {/* target */}
        <AppText variant="label" color={colors.textMuted}>
          {languageName(result.targetLang).toUpperCase()}
          {result.script ? ` · ${result.script}` : ''}
        </AppText>
        <AppText variant="script" color={colors.primaryDark} style={{ marginTop: spacing.xs }}>
          {result.translatedText}
        </AppText>

        {showPronunciation && result.pronunciation ? (
          <View
            style={{
              marginTop: spacing.md,
              padding: spacing.md,
              backgroundColor: colors.surfaceMuted,
              borderRadius: radius.sm,
              borderWidth: borderWidth.thin,
              borderColor: colors.border,
            }}
          >
            <AppText variant="label" color={colors.textMuted}>
              PRONUNCIATION GUIDE
            </AppText>
            <AppText variant="bodyStrong" style={{ marginTop: spacing.xxs }}>
              {result.pronunciation}
            </AppText>
          </View>
        ) : null}

        {/* honesty disclaimer */}
        <AppText variant="caption" color={colors.textMuted} style={{ marginTop: spacing.md }}>
          Demo dictionary translation — verified sample data, not a production translation model.
        </AppText>

        {/* actions */}
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.lg }}>
          <Button title="Copy" icon="copy-outline" variant="outline" size="sm" onPress={onCopy} />
          <Button
            title={saved ? 'Saved' : 'Save'}
            icon={saved ? 'bookmark' : 'bookmark-outline'}
            variant={saved ? 'success' : 'outline'}
            size="sm"
            onPress={onSave}
          />
          <Button
            title={isSpeaking ? 'Stop' : 'Play audio'}
            icon={isSpeaking ? 'stop-outline' : 'volume-high-outline'}
            variant="accent"
            size="sm"
            onPress={onPlayAudio}
          />
          <Button title="Again" icon="refresh-outline" variant="outline" size="sm" onPress={onTranslateAgain} />
        </View>
      </View>
    </Card>
  );
}
