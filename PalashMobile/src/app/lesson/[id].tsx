import React, { useCallback, useState } from 'react';
import { View } from 'react-native';
import { useLocalSearchParams, useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Screen, AppText, Card, Button, StatusBadge, LoadingState, EmptyState, ErrorBoundary } from '@/components';
import { lessonService } from '@/services';
import { colors, spacing, radius, borderWidth } from '@/theme';
import type { Lesson } from '@/types';

function BulletList({ items }: { items: string[] }) {
  return (
    <View style={{ gap: spacing.sm }}>
      {items.map((item, i) => (
        <View key={i} style={{ flexDirection: 'row', gap: spacing.sm }}>
          <View style={{ width: 7, height: 7, borderRadius: 2, backgroundColor: colors.primary, marginTop: 7 }} />
          <AppText variant="body" style={{ flex: 1 }}>
            {item}
          </AppText>
        </View>
      ))}
    </View>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={{ marginTop: spacing.xl }}>
      <AppText variant="label" color={colors.textMuted} style={{ marginBottom: spacing.sm }}>
        {title.toUpperCase()}
      </AppText>
      {children}
    </View>
  );
}

function LessonDetailContent() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setLoading(true);
      lessonService.get(id ?? '').then((l) => {
        if (active) {
          setLesson(l);
          setLoading(false);
        }
      }).catch(() => {
        if (active) setLoading(false);
      });
      return () => { active = false; };
    }, [id]),
  );

  const onSave = async () => {
    if (!lesson) return;
    await lessonService.save({ ...lesson, savedAt: new Date().toISOString() });
    setSaved(true);
  };

  if (loading) {
    return (
      <Screen title="Lesson" showBack>
        <LoadingState label="Loading lesson…" />
      </Screen>
    );
  }

  if (!lesson) {
    return (
      <Screen title="Lesson" showBack>
        <EmptyState icon="book-outline" title="Lesson not found" message="This lesson is no longer available." />
      </Screen>
    );
  }

  return (
    <Screen
      title={lesson.titleHindi}
      showBack
      headerRight={
        <Button
          title={saved ? 'Saved' : 'Save'}
          icon={saved ? 'bookmark' : 'bookmark-outline'}
          variant={saved ? 'success' : 'outline'}
          size="sm"
          onPress={onSave}
        />
      }
    >
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs }}>
        <StatusBadge label={lesson.status === 'PUBLISHED' ? 'Published' : 'Draft'} tone={lesson.status === 'PUBLISHED' ? 'success' : 'neutral'} />
        <StatusBadge label={`Unit ${lesson.unit} · Lesson ${lesson.lessonNumber}`} tone="neutral" />
      </View>

      <AppText variant="body" color={colors.textMuted} style={{ marginTop: spacing.md }}>
        {lesson.topic}
      </AppText>

      <Section title="Learning outcomes">
        <BulletList items={lesson.learningOutcomes} />
      </Section>

      <Section title="Activities">
        <BulletList items={lesson.activities} />
      </Section>

      <Section title="Assessments">
        <BulletList items={lesson.assessments} />
      </Section>

      <Section title="Vocabulary — tap to translate">
        <View style={{ gap: spacing.sm }}>
          {lesson.vocabulary.map((v) => (
            <Card
              key={v.hindi}
              shadowSize="sm"
              padded={false}
              onPress={() => router.push({ pathname: '/(tabs)/translate', params: { phrase: v.hindi } })}
            >
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.md, padding: spacing.md }}>
                <View
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: radius.sm,
                    borderWidth: borderWidth.thin,
                    borderColor: colors.border,
                    backgroundColor: colors.surfaceAlt,
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Ionicons name="language-outline" size={18} color={colors.text} />
                </View>
                <View style={{ flex: 1 }}>
                  <AppText variant="subtitle">{v.hindi}</AppText>
                  {v.gloss ? (
                    <AppText variant="caption" color={colors.textMuted}>
                      {v.gloss}
                    </AppText>
                  ) : null}
                </View>
                <Ionicons name="arrow-forward" size={18} color={colors.textMuted} />
              </View>
            </Card>
          ))}
        </View>
        <AppText variant="caption" color={colors.textMuted} style={{ marginTop: spacing.sm }}>
          Only Hindi → Santali has demo translations. Other vocabulary opens the translator with an
          honest "not available" result.
        </AppText>
      </Section>
    </Screen>
  );
}

export default function LessonDetailScreen() {
  return (
    <ErrorBoundary fallbackTitle="Lesson error">
      <LessonDetailContent />
    </ErrorBoundary>
  );
}
