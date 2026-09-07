import React, { useEffect, useRef, useState } from 'react';
import { Animated, View } from 'react-native';
import { Redirect } from 'expo-router';
import { useAuth } from '@/context/AuthContext';
import { AppText, MotifRow } from '@/components';
import { colors, palette, spacing } from '@/theme';

const MIN_SPLASH_MS = 1100;

/** Branded splash that also gates navigation based on auth + onboarding. */
export default function Index() {
  const { isLoading, isAuthenticated, profile } = useAuth();
  const [minElapsed, setMinElapsed] = useState(false);
  const fade = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fade, { toValue: 1, duration: 600, useNativeDriver: true }).start();
    const t = setTimeout(() => setMinElapsed(true), MIN_SPLASH_MS);
    return () => clearTimeout(t);
  }, [fade]);

  const ready = minElapsed && !isLoading;

  if (ready) {
    if (!isAuthenticated) return <Redirect href="/(auth)/login" />;
    if (!profile?.onboarded) return <Redirect href="/onboarding" />;
    return <Redirect href="/(tabs)" />;
  }

  return (
    <View style={{ flex: 1, backgroundColor: palette.terracotta, alignItems: 'center', justifyContent: 'center', padding: spacing.xl }}>
      <Animated.View style={{ opacity: fade, alignItems: 'center' }}>
        <View
          style={{
            borderWidth: 4,
            borderColor: palette.brownDark,
            backgroundColor: palette.cream,
            paddingHorizontal: spacing.xl,
            paddingVertical: spacing.md,
            borderRadius: 14,
            // hard offset shadow (iOS/web); Android shows the flat block
            shadowColor: palette.brownDark,
            shadowOffset: { width: 5, height: 5 },
            shadowOpacity: 1,
            shadowRadius: 0,
          }}
        >
          <AppText variant="display" color={palette.terracottaDeep}>
            PALASH
          </AppText>
        </View>
        <AppText variant="subtitle" color={palette.cream} center style={{ marginTop: spacing.xl }}>
          Mother-tongue teaching companion
        </AppText>
        <AppText variant="caption" color={palette.sand} center style={{ marginTop: spacing.xs }}>
          Offline-first · built for Jharkhand classrooms
        </AppText>
        <MotifRow shape="diamond" count={7} size={12} color={palette.sand} style={{ width: 180, marginTop: spacing.xxl }} />
      </Animated.View>
    </View>
  );
}
