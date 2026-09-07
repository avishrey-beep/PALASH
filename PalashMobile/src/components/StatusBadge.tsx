import React from 'react';
import { View, type StyleProp, type ViewStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppText } from './AppText';
import { colors, radius, spacing, borderWidth, statusColors, type StatusKey } from '@/theme';

type IconName = React.ComponentProps<typeof Ionicons>['name'];

interface StatusBadgeProps {
  label: string;
  tone?: StatusKey;
  background?: string;
  color?: string;
  icon?: IconName;
  style?: StyleProp<ViewStyle>;
}

/** Compact bordered status chip (translation states, demo labels, etc.). */
export function StatusBadge({ label, tone, background, color, icon, style }: StatusBadgeProps) {
  const toneColors = tone ? statusColors[tone] : undefined;
  const bg = background ?? toneColors?.bg ?? colors.surfaceAlt;
  const fg = color ?? toneColors?.fg ?? colors.text;

  return (
    <View
      style={[
        {
          flexDirection: 'row',
          alignItems: 'center',
          gap: spacing.xxs,
          alignSelf: 'flex-start',
          backgroundColor: bg,
          borderColor: colors.border,
          borderWidth: borderWidth.thin,
          borderRadius: radius.sm,
          paddingHorizontal: spacing.sm,
          paddingVertical: spacing.xxs,
        },
        style,
      ]}
    >
      {icon ? <Ionicons name={icon} size={12} color={fg} /> : null}
      <AppText variant="label" color={fg}>
        {label.toUpperCase()}
      </AppText>
    </View>
  );
}
