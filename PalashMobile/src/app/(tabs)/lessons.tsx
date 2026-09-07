import React, { useCallback, useState } from 'react';
import { useRouter, useFocusEffect } from 'expo-router';
import { Screen, Button, LessonCard, EmptyState, LoadingState, ErrorBoundary } from '@/components';
import { lessonService } from '@/services';
import type { Lesson } from '@/types';

function LessonsScreenContent() {
  const router = useRouter();
  const [lessons, setLessons] = useState<Lesson[] | null>(null);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      lessonService.list().then((items) => {
        if (active) setLessons(items ?? []);
      }).catch(() => {
        if (active) setLessons([]);
      });
      return () => { active = false; };
    }, []),
  );

  return (
    <Screen
      title="My Lessons"
      subtitle="Saved lesson plans on this device"
      headerRight={<Button title="Curriculum" icon="library-outline" variant="outline" size="sm" onPress={() => router.push('/curriculum')} />}
    >
      {lessons === null ? (
        <LoadingState label="Loading lessons…" />
      ) : lessons.length === 0 ? (
        <EmptyState
          icon="book-outline"
          title="No lessons saved"
          message="Browse the curriculum to open and save lesson plans for offline use."
          actionLabel="Browse curriculum"
          onAction={() => router.push('/curriculum')}
        />
      ) : (
        lessons.map((l) => (
          <LessonCard key={l.id} lesson={l} onPress={() => router.push(`/lesson/${l.id}`)} />
        ))
      )}
    </Screen>
  );
}

export default function LessonsScreen() {
  return (
    <ErrorBoundary fallbackTitle="Lessons error">
      <LessonsScreenContent />
    </ErrorBoundary>
  );
}
