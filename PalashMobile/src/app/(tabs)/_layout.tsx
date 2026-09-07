import React from 'react';
import { Platform, type ColorValue } from 'react-native';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, palette, spacing, borderWidth, fontWeights } from '@/theme';

type IconName = React.ComponentProps<typeof Ionicons>['name'];

function tabIcon(focused: IconName, unfocused: IconName) {
  return ({ color, focused: isFocused, size }: { color: ColorValue; focused: boolean; size: number }) => (
    <Ionicons name={isFocused ? focused : unfocused} size={size} color={color} />
  );
}

/** Bottom navigation: Home / Translate / Voice / Sheets / Lessons. */
export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopWidth: borderWidth.base,
          borderTopColor: colors.border,
          height: Platform.OS === 'ios' ? 88 : 66,
          paddingTop: spacing.sm,
          paddingBottom: Platform.OS === 'ios' ? spacing.xxl : spacing.sm,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: fontWeights.bold,
          letterSpacing: 0.3,
        },
        tabBarActiveBackgroundColor: palette.creamDeep,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{ title: 'Home', tabBarIcon: tabIcon('home', 'home-outline') }}
      />
      <Tabs.Screen
        name="translate"
        options={{ title: 'Translate', tabBarIcon: tabIcon('language', 'language-outline') }}
      />
      <Tabs.Screen
        name="voice"
        options={{ title: 'Voice', tabBarIcon: tabIcon('mic', 'mic-outline') }}
      />
      <Tabs.Screen
        name="sheets"
        options={{ title: 'Sheets', tabBarIcon: tabIcon('document-text', 'document-text-outline') }}
      />
      <Tabs.Screen
        name="lessons"
        options={{ title: 'Lessons', tabBarIcon: tabIcon('book', 'book-outline') }}
      />
    </Tabs>
  );
}
