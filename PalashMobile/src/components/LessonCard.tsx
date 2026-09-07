import React from 'react';
import { View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Card } from './Card';
import { AppText } from './AppText';
import { StatusBadge } from './StatusBadge';
import { colors, spacing } from '@/theme';
import type { Lesson } from '@/types';

interface LessonCardProps {
  lesson: Lesson;
  onPress: () => void;
}

/** Summary card for a lesson in "My Lessons" / curriculum lists. */
export function LessonCard({ lesson, onPress }: LessonCardProps) {
  return (
    <Card onPress={onPress} style={{ marginBottom: spacing.md }}>
      <View style={{ flexDirection: 'row', gap: spacing.md }}>
        <View style={{ flex: 1 }}>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginBottom: spacing.sm }}>
            <StatusBadge
              label={lesson.status === 'PUBLISHED' ? 'Published' : 'Draft'}
              tone={lesson.status === 'PUBLISHED' ? 'success' : 'neutral'}
            />
            <StatusBadge label={`Unit ${lesson.unit} · L${lesson.lessonNumber}`} tone="neutral" />
          </View>
          <AppText variant="subtitle" numberOfLines={2}>
            {lesson.titleHindi}
          </AppText>
          <AppText variant="bodySmall" color={colors.textMuted} numberOfLines={2} style={{ marginTop: spacing.xxs }}>
            {lesson.topic}
          </AppText>
          <AppText variant="caption" color={colors.textMuted} style={{ marginTop: spacing.sm }}>
            {lesson.learningOutcomes.length} outcomes · {lesson.vocabulary.length} vocabulary
          </AppText>
        </View>
        <Ionicons name="chevron-forward" size={22} color={colors.text} style={{ alignSelf: 'center' }} />
      </View>
    </Card>
  );
}
