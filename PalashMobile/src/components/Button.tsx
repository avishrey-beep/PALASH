import React from 'react';
import { ActivityIndicator, Pressable, View, type StyleProp, type ViewStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { NeoSurface } from './NeoSurface';
import { AppText } from './AppText';
import { colors, spacing, type ShadowSize } from '@/theme';
import { useHaptics } from '@/hooks/useHaptics';

type Variant = 'primary' | 'accent' | 'success' | 'danger' | 'outline' | 'ghost';
type Size = 'sm' | 'md' | 'lg';
type IconName = React.ComponentProps<typeof Ionicons>['name'];

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: Variant;
  size?: Size;
  icon?: IconName;
  iconRight?: IconName;
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  style?: StyleProp<ViewStyle>;
}

const VARIANT: Record<Variant, { bg: string; fg: string; hasSurface: boolean }> = {
  primary: { bg: colors.primary, fg: colors.textOnPrimary, hasSurface: true },
  accent: { bg: colors.accent, fg: colors.textOnAccent, hasSurface: true },
  success: { bg: colors.success, fg: colors.textOnSuccess, hasSurface: true },
  danger: { bg: colors.danger, fg: colors.white, hasSurface: true },
  outline: { bg: colors.surface, fg: colors.text, hasSurface: true },
  ghost: { bg: 'transparent', fg: colors.primary, hasSurface: false },
};

const SIZE: Record<Size, { padV: number; padH: number; icon: number; shadow: ShadowSize }> = {
  sm: { padV: spacing.sm, padH: spacing.md, icon: 16, shadow: 'sm' },
  md: { padV: spacing.md, padH: spacing.lg, icon: 20, shadow: 'md' },
  lg: { padV: spacing.lg, padH: spacing.xl, icon: 22, shadow: 'md' },
};

/**
 * Neo-brutalist button: flat fill, thick border, hard offset shadow that
 * depresses on press. `ghost` is a flat text-only variant (no shadow/border).
 */
export function Button({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  icon,
  iconRight,
  loading = false,
  disabled = false,
  fullWidth = false,
  style,
}: ButtonProps) {
  const v = VARIANT[variant];
  const s = SIZE[size];
  const { tap } = useHaptics();
  const isDisabled = disabled || loading;

  const handlePress = () => {
    if (isDisabled) return;
    tap();
    onPress();
  };

  const inner = (pressed: boolean) => {
    const content = (
      <View
        style={{
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'center',
          gap: spacing.sm,
          paddingVertical: s.padV,
          paddingHorizontal: s.padH,
        }}
      >
        {loading ? (
          <ActivityIndicator color={v.fg} />
        ) : (
          <>
            {icon ? <Ionicons name={icon} size={s.icon} color={v.fg} /> : null}
            <AppText variant="button" color={v.fg}>
              {title}
            </AppText>
            {iconRight ? <Ionicons name={iconRight} size={s.icon} color={v.fg} /> : null}
          </>
        )}
      </View>
    );

    if (!v.hasSurface) {
      // ghost: flat, slight press feedback via opacity
      return <View style={{ opacity: pressed ? 0.6 : 1 }}>{content}</View>;
    }

    return (
      <NeoSurface
        shadowSize={s.shadow}
        backgroundColor={v.bg}
        pressed={pressed}
        style={fullWidth ? { alignSelf: 'stretch' } : undefined}
      >
        {content}
      </NeoSurface>
    );
  };

  return (
    <Pressable
      onPress={handlePress}
      disabled={isDisabled}
      accessibilityRole="button"
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      accessibilityLabel={title}
      style={[
        fullWidth && { alignSelf: 'stretch' },
        isDisabled && { opacity: 0.5 },
        style,
      ]}
    >
      {({ pressed }) => inner(pressed)}
    </Pressable>
  );
}
