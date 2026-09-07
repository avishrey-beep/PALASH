import React from 'react';
import { Text as RNText, type TextProps, type TextStyle, type StyleProp } from 'react-native';
import { colors, typography, type TypographyRole } from '@/theme';

interface AppTextProps extends TextProps {
  variant?: TypographyRole;
  color?: string;
  center?: boolean;
  style?: StyleProp<TextStyle>;
}

/**
 * Typographic Text wrapper. Applies a role from the type scale plus a color,
 * so screens never hand-roll font sizes/weights. Defaults to body / ink text.
 */
export function AppText({
  variant = 'body',
  color = colors.text,
  center = false,
  style,
  children,
  ...rest
}: AppTextProps) {
  return (
    <RNText
      style={[typography[variant], { color }, center && { textAlign: 'center' }, style]}
      {...rest}
    >
      {children}
    </RNText>
  );
}
