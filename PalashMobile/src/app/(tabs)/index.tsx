import React, { useCallback, useState } from 'react';
import { Pressable, View } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import {
  Screen,
  AppText,
  Card,
  NeoSurface,
  QuickActionCard,
  SectionHeader,
  OfflineIndicator,
  EmptyState,
  MotifRow,
} from '@/components';
import { useAuth } from '@/context/AuthContext';
import { activityService } from '@/services';
import { greeting, relativeTime } from '@/utils/time';
import { colors, palette, spacing, radius, borderWidth } from '@/theme';
import type { ActivityItem, ActivityKind } from '@/types';

type IconName = React.ComponentProps<typeof Ionicons>['name'];

const ACTIVITY_ICON: Record<ActivityKind, IconName> = {
  translation: 'language-outline',
  voice: 'mic-outline',
  worksheet: 'document-text-outline',
  lesson: 'book-outline',
  curriculum: 'library-outline',
};

export default function HomeScreen() {
  const router = useRouter();
  const { profile } = useAuth();
  const [activity, setActivity] = useState<ActivityItem[]>([]);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      activityService.list().then((items) => {
        if (active) setActivity(items);
      });
      return () => {
        active = false;
      };
    }, []),
  );

  const firstName = profile?.name?.split(' ')[0] ?? 'Teacher';

  return (
    <Screen>
      {/* Hero */}
      <View style={{ flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: spacing.md }}>
        <View style={{ flex: 1 }}>
          <AppText variant="bodySmall" color={colors.textMuted}>
            {greeting()},
          </AppText>
          <AppText variant="h1">{firstName}</AppText>
          {profile?.school ? (
            <AppText variant="caption" color={colors.textMuted} style={{ marginTop: spacing.xxs }}>
              {profile.school}
            </AppText>
          ) : null}
        </View>
        <View style={{ alignItems: 'flex-end', gap: spacing.sm }}>
          <Pressable onPress={() => router.push('/settings')} accessibilityRole="button" accessibilityLabel="Settings">
            {({ pressed }) => (
              <NeoSurface shadowSize="sm" backgroundColor={colors.surface} pressed={pressed}>
                <View style={{ padding: spacing.sm }}>
                  <Ionicons name="settings-outline" size={22} color={colors.text} />
                </View>
              </NeoSurface>
            )}
          </Pressable>
          <OfflineIndicator />
        </View>
      </View>

      <MotifRow shape="dot" count={9} size={10} color={palette.mustard} style={{ width: 150, marginTop: spacing.md, marginBottom: spacing.xl }} />

      {/* Showcase action */}
      <QuickActionCard
        title="Translate a phrase"
        subtitle="Hindi → mother tongue · works offline"
        icon="language-outline"
        background={colors.primary}
        foreground={colors.textOnPrimary}
        onPress={() => router.push('/(tabs)/translate')}
        style={{ marginBottom: spacing.md }}
      />

      {/* Secondary actions, 2-col grid */}
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md }}>
        <QuickActionCard title="Voice" subtitle="Demo voice mode" icon="mic-outline" onPress={() => router.push('/(tabs)/voice')} style={{ width: '47.5%', flexGrow: 1 }} />
        <QuickActionCard title="Curriculum" subtitle="JCERT units" icon="library-outline" onPress={() => router.push('/curriculum')} style={{ width: '47.5%', flexGrow: 1 }} />
        <QuickActionCard title="Worksheet" subtitle="Build a template" icon="create-outline" onPress={() => router.push('/worksheet/create')} style={{ width: '47.5%', flexGrow: 1 }} />
        <QuickActionCard title="Lessons" subtitle="My library" icon="book-outline" onPress={() => router.push('/(tabs)/lessons')} style={{ width: '47.5%', flexGrow: 1 }} />
      </View>

      {/* Recent activity */}
      <View style={{ marginTop: spacing.xxl }}>
        <SectionHeader title="Recent activity" subtitle="On this device" />
        {activity.length === 0 ? (
          <EmptyState
            icon="time-outline"
            title="Nothing yet"
            message="Your recent translations and lessons will appear here."
          />
        ) : (
          activity.map((item) => (
            <Card key={item.id} shadowSize="sm" style={{ marginBottom: spacing.sm }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.md }}>
                <View
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: radius.sm,
                    borderWidth: borderWidth.thin,
                    borderColor: colors.border,
                    backgroundColor: colors.surfaceAlt,
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Ionicons name={ACTIVITY_ICON[item.kind]} size={20} color={colors.text} />
                </View>
                <View style={{ flex: 1 }}>
                  <AppText variant="bodyStrong" numberOfLines={1}>
                    {item.title}
                  </AppText>
                  {item.subtitle ? (
                    <AppText variant="caption" color={colors.textMuted} numberOfLines={1}>
                      {item.subtitle}
                    </AppText>
                  ) : null}
                </View>
                <AppText variant="caption" color={colors.textMuted}>
                  {relativeTime(item.timestamp)}
                </AppText>
              </View>
            </Card>
          ))
        )}
      </View>
    </Screen>
  );
}
