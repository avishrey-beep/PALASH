import React from 'react';
import { View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Card } from './Card';
import { AppText } from './AppText';
import { StatusBadge } from './StatusBadge';
import { colors, spacing } from '@/theme';
import type { Worksheet } from '@/types';

interface WorksheetCardProps {
  worksheet: Worksheet;
  onPress: () => void;
}

/** Summary card for a worksheet in the worksheet list. */
export function WorksheetCard({ worksheet, onPress }: WorksheetCardProps) {
  return (
    <Card onPress={onPress} style={{ marginBottom: spacing.md }}>
      <View style={{ flexDirection: 'row', gap: spacing.md }}>
        <View style={{ flex: 1 }}>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginBottom: spacing.sm }}>
            <StatusBadge
              label={worksheet.status === 'READY' ? 'Ready' : 'Draft'}
              tone={worksheet.status === 'READY' ? 'success' : 'processing'}
            />
            <StatusBadge label={`Class ${worksheet.classGrade}`} tone="neutral" />
          </View>
          <AppText variant="subtitle" numberOfLines={2}>
            {worksheet.title}
          </AppText>
          <AppText variant="bodySmall" color={colors.textMuted} numberOfLines={1} style={{ marginTop: spacing.xxs }}>
            {worksheet.subject} · {worksheet.topic}
          </AppText>
          <AppText variant="caption" color={colors.textMuted} style={{ marginTop: spacing.sm }}>
            {worksheet.questions.length} questions
          </AppText>
        </View>
        <Ionicons name="chevron-forward" size={22} color={colors.text} style={{ alignSelf: 'center' }} />
      </View>
    </Card>
  );
}
