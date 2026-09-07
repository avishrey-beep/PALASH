import React from 'react';
import { Pressable, View, type StyleProp, type ViewStyle } from 'react-native';
import { NeoSurface } from './NeoSurface';
import { colors, radius as radiusScale, spacing, type ShadowSize } from '@/theme';
import { useHaptics } from '@/hooks/useHaptics';

interface CardProps {
  children: React.ReactNode;
  onPress?: () => void;
  padded?: boolean;
  shadowSize?: ShadowSize;
  backgroundColor?: string;
  borderColor?: string;
  radius?: number;
  style?: StyleProp<ViewStyle>;
  contentStyle?: StyleProp<ViewStyle>;
}

/**
 * Neo-brutalist card. Static by default; when `onPress` is given it becomes a
 * tactile pressable that depresses into its shadow.
 */
export function Card({
  children,
  onPress,
  padded = true,
  shadowSize = 'md',
  backgroundColor = colors.surface,
  borderColor = colors.border,
  radius = radiusScale.md,
  style,
  contentStyle,
}: CardProps) {
  const { tap } = useHaptics();
  const pad = padded ? { padding: spacing.lg } : undefined;

  if (!onPress) {
    return (
      <NeoSurface
        shadowSize={shadowSize}
        backgroundColor={backgroundColor}
        borderColor={borderColor}
        radius={radius}
        style={style}
        contentStyle={[pad, contentStyle]}
      >
        {children}
      </NeoSurface>
    );
  }

  return (
    <Pressable
      onPress={() => {
        tap();
        onPress();
      }}
      accessibilityRole="button"
      style={style}
    >
      {({ pressed }) => (
        <NeoSurface
          shadowSize={shadowSize}
          backgroundColor={backgroundColor}
          borderColor={borderColor}
          radius={radius}
          pressed={pressed}
          contentStyle={[pad, contentStyle]}
        >
          {children}
        </NeoSurface>
      )}
    </Pressable>
  );
}
