import React from 'react';
import { ActivityIndicator, View } from 'react-native';
import { AppText } from './AppText';
import { colors, spacing } from '@/theme';

interface LoadingStateProps {
  label?: string;
  inline?: boolean;
}

/** Centered spinner with an optional label. */
export function LoadingState({ label, inline = false }: LoadingStateProps) {
  return (
    <View
      style={{
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: inline ? 'row' : 'column',
        gap: spacing.sm,
        paddingVertical: inline ? 0 : spacing.xxxl,
      }}
    >
      <ActivityIndicator color={colors.primary} size={inline ? 'small' : 'large'} />
      {label ? (
        <AppText variant="bodySmall" color={colors.textMuted}>
          {label}
        </AppText>
      ) : null}
    </View>
  );
}
