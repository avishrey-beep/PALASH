import React from 'react';
import {
  Pressable,
  ScrollView,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';
import { SafeAreaView, type Edge } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { AppText } from './AppText';
import { NeoSurface } from './NeoSurface';
import { colors, spacing } from '@/theme';

interface ScreenProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  showBack?: boolean;
  headerRight?: React.ReactNode;
  scroll?: boolean;
  padded?: boolean;
  background?: string;
  footer?: React.ReactNode;
  edges?: Edge[];
  contentContainerStyle?: StyleProp<ViewStyle>;
}

/**
 * Shared screen scaffold: safe-area aware, optional bold header with a
 * tactile back button, scrollable body, and an optional sticky footer.
 */
export function Screen({
  children,
  title,
  subtitle,
  showBack = false,
  headerRight,
  scroll = true,
  padded = true,
  background = colors.background,
  footer,
  edges = ['top', 'left', 'right'],
  contentContainerStyle,
}: ScreenProps) {
  const router = useRouter();
  const bodyPad = padded ? { padding: spacing.lg } : undefined;

  const header =
    title || showBack || headerRight ? (
      <View
        style={{
          flexDirection: 'row',
          alignItems: 'center',
          gap: spacing.md,
          paddingHorizontal: spacing.lg,
          paddingTop: spacing.md,
          paddingBottom: spacing.sm,
        }}
      >
        {showBack ? (
          <Pressable onPress={() => (router.canGoBack() ? router.back() : router.replace('/'))} accessibilityLabel="Go back" accessibilityRole="button">
            {({ pressed }) => (
              <NeoSurface shadowSize="sm" backgroundColor={colors.surface} pressed={pressed}>
                <View style={{ padding: spacing.sm }}>
                  <Ionicons name="chevron-back" size={22} color={colors.text} />
                </View>
              </NeoSurface>
            )}
          </Pressable>
        ) : null}
        <View style={{ flex: 1 }}>
          {title ? <AppText variant="h2">{title}</AppText> : null}
          {subtitle ? (
            <AppText variant="bodySmall" color={colors.textMuted}>
              {subtitle}
            </AppText>
          ) : null}
        </View>
        {headerRight}
      </View>
    ) : null;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: background }} edges={edges}>
      {header}
      {scroll ? (
        <ScrollView
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={[bodyPad, { paddingBottom: spacing.huge }, contentContainerStyle]}
          showsVerticalScrollIndicator={false}
        >
          {children}
        </ScrollView>
      ) : (
        <View style={[{ flex: 1 }, bodyPad, contentContainerStyle]}>{children}</View>
      )}
      {footer ? (
        <View
          style={{
            padding: spacing.lg,
            backgroundColor: background,
            borderTopWidth: 2,
            borderTopColor: colors.border,
          }}
        >
          {footer}
        </View>
      ) : null}
    </SafeAreaView>
  );
}
