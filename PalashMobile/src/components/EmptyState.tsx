import React from 'react';
import { View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppText } from './AppText';
import { Button } from './Button';
import { colors, spacing, radius, borderWidth } from '@/theme';

type IconName = React.ComponentProps<typeof Ionicons>['name'];

interface EmptyStateProps {
  icon?: IconName;
  title: string;
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
}

/** Friendly empty placeholder with an optional call-to-action. */
export function EmptyState({ icon = 'sparkles-outline', title, message, actionLabel, onAction }: EmptyStateProps) {
  return (
    <View style={{ alignItems: 'center', paddingVertical: spacing.xxxl, paddingHorizontal: spacing.lg }}>
      <View
        style={{
          width: 72,
          height: 72,
          borderRadius: radius.lg,
          borderWidth: borderWidth.base,
          borderColor: colors.border,
          backgroundColor: colors.surfaceAlt,
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: spacing.lg,
          transform: [{ rotate: '45deg' }],
        }}
      >
        <View style={{ transform: [{ rotate: '-45deg' }] }}>
          <Ionicons name={icon} size={34} color={colors.text} />
        </View>
      </View>
      <AppText variant="h3" center>
        {title}
      </AppText>
      {message ? (
        <AppText variant="body" color={colors.textMuted} center style={{ marginTop: spacing.sm, maxWidth: 320 }}>
          {message}
        </AppText>
      ) : null}
      {actionLabel && onAction ? (
        <Button title={actionLabel} onPress={onAction} variant="primary" style={{ marginTop: spacing.xl }} />
      ) : null}
    </View>
  );
}
