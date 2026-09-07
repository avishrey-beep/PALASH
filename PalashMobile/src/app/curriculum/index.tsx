import React, { useCallback, useState } from 'react';
import { View } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { Screen, AppText, Card, Button, StatusBadge, LessonCard, LoadingState, EmptyState } from '@/components';
import { curriculumService } from '@/services';
import { colors, spacing } from '@/theme';
import type { Curriculum, Lesson } from '@/types';

export default function CurriculumScreen() {
  const router = useRouter();
  const [curricula, setCurricula] = useState<Curriculum[] | null>(null);
  const [lessonsByCur, setLessonsByCur] = useState<Record<string, Lesson[]>>({});

  useFocusEffect(
    useCallback(() => {
      let active = true;
      (async () => {
        const list = await curriculumService.list();
        const entries = await Promise.all(
          list.map(async (c) => [c.id, await curriculumService.lessonsFor(c.id)] as const),
        );
        if (!active) return;
        setCurricula(list);
        setLessonsByCur(Object.fromEntries(entries));
      })();
      return () => {
        active = false;
      };
    }, []),
  );

  return (
    <Screen
      title="Curriculum"
      subtitle="JCERT-aligned demo units"
      showBack
      headerRight={<Button title="Add" icon="add" size="sm" onPress={() => router.push('/curriculum/upload')} />}
    >
      {curricula === null ? (
        <LoadingState label="Loading curriculum…" />
      ) : curricula.length === 0 ? (
        <EmptyState icon="library-outline" title="No curriculum yet" message="Add a curriculum outline to organise your lessons." actionLabel="Add curriculum" onAction={() => router.push('/curriculum/upload')} />
      ) : (
        curricula.map((c) => {
          const lessons = lessonsByCur[c.id] ?? [];
          return (
            <View key={c.id} style={{ marginBottom: spacing.xxl }}>
              <Card>
                <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginBottom: spacing.sm }}>
                  <StatusBadge label={c.board} tone="processing" />
                  <StatusBadge label={c.state} tone="neutral" />
                  <StatusBadge label={`Class ${c.classGrade}`} tone="neutral" />
                  <StatusBadge label={c.subject} tone="neutral" />
                </View>
                <AppText variant="h3">{c.title}</AppText>
                <AppText variant="bodySmall" color={colors.textMuted} style={{ marginTop: spacing.xs }}>
                  {c.description}
                </AppText>
                <AppText variant="caption" color={colors.textMuted} style={{ marginTop: spacing.sm }}>
                  Medium: {c.medium} · {lessons.length} lesson{lessons.length === 1 ? '' : 's'}
                </AppText>
              </Card>

              {lessons.length > 0 ? (
                <View style={{ marginTop: spacing.md }}>
                  {lessons.map((l) => (
                    <LessonCard key={l.id} lesson={l} onPress={() => router.push(`/lesson/${l.id}`)} />
                  ))}
                </View>
              ) : (
                <AppText variant="bodySmall" color={colors.textMuted} style={{ marginTop: spacing.md, marginLeft: spacing.xs }}>
                  No lessons imported for this unit yet.
                </AppText>
              )}
            </View>
          );
        })
      )}
    </Screen>
  );
}
