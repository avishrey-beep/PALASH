import React from 'react';
import { Pressable, View } from 'react-native';
import { AppText } from './AppText';
import { colors, spacing } from '@/theme';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  actionLabel?: string;
  onAction?: () => void;
}

/** Bold section title with an optional right-aligned text action. */
export function SectionHeader({ title, subtitle, actionLabel, onAction }: SectionHeaderProps) {
  return (
    <View
      style={{
        flexDirection: 'row',
        alignItems: 'flex-end',
        justifyContent: 'space-between',
        marginBottom: spacing.md,
      }}
    >
      <View style={{ flex: 1 }}>
        <AppText variant="h3">{title}</AppText>
        {subtitle ? (
          <AppText variant="bodySmall" color={colors.textMuted} style={{ marginTop: spacing.xxs }}>
            {subtitle}
          </AppText>
        ) : null}
      </View>
      {actionLabel && onAction ? (
        <Pressable onPress={onAction} hitSlop={8} accessibilityRole="button">
          <AppText variant="label" color={colors.primary}>
            {actionLabel.toUpperCase()}
          </AppText>
        </Pressable>
      ) : null}
    </View>
  );
}
