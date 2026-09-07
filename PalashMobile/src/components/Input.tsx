import React, { useState } from 'react';
import {
  TextInput,
  View,
  type StyleProp,
  type ViewStyle,
  type TextInputProps,
  type KeyboardTypeOptions,
} from 'react-native';
import { AppText } from './AppText';
import { colors, radius, spacing, borderWidth, typography } from '@/theme';

interface InputProps {
  label?: string;
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  multiline?: boolean;
  numberOfLines?: number;
  error?: string;
  helperText?: string;
  secureTextEntry?: boolean;
  autoCapitalize?: TextInputProps['autoCapitalize'];
  keyboardType?: KeyboardTypeOptions;
  autoFocus?: boolean;
  editable?: boolean;
  maxLength?: number;
  style?: StyleProp<ViewStyle>;
}

/**
 * Neo-brutalist text field: thick border, flat fill, bold uppercase label.
 * Border turns terracotta on focus and danger red on error.
 */
export function Input({
  label,
  value,
  onChangeText,
  placeholder,
  multiline = false,
  numberOfLines = 4,
  error,
  helperText,
  secureTextEntry,
  autoCapitalize = 'none',
  keyboardType,
  autoFocus,
  editable = true,
  maxLength,
  style,
}: InputProps) {
  const [focused, setFocused] = useState(false);
  const borderColor = error ? colors.danger : focused ? colors.primary : colors.border;

  return (
    <View style={style}>
      {label ? (
        <AppText variant="label" color={colors.textMuted} style={{ marginBottom: spacing.xs }}>
          {label.toUpperCase()}
        </AppText>
      ) : null}
      <View
        style={{
          borderWidth: borderWidth.base,
          borderColor,
          borderRadius: radius.md,
          backgroundColor: editable ? colors.surface : colors.surfaceMuted,
          paddingHorizontal: spacing.md,
        }}
      >
        <TextInput
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={colors.textMuted}
          multiline={multiline}
          numberOfLines={multiline ? numberOfLines : undefined}
          secureTextEntry={secureTextEntry}
          autoCapitalize={autoCapitalize}
          keyboardType={keyboardType}
          autoFocus={autoFocus}
          editable={editable}
          maxLength={maxLength}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          style={[
            typography.body,
            {
              color: colors.text,
              paddingVertical: spacing.md,
              minHeight: multiline ? numberOfLines * 24 : undefined,
              textAlignVertical: multiline ? 'top' : 'center',
            },
          ]}
        />
      </View>
      {error ? (
        <AppText variant="caption" color={colors.danger} style={{ marginTop: spacing.xs }}>
          {error}
        </AppText>
      ) : helperText ? (
        <AppText variant="caption" color={colors.textMuted} style={{ marginTop: spacing.xs }}>
          {helperText}
        </AppText>
      ) : null}
    </View>
  );
}
