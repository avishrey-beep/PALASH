import React from 'react';
import { Alert, Switch, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import {
  Screen,
  AppText,
  Card,
  Button,
  SectionHeader,
  StatusBadge,
  LanguageSelector,
  OfflineIndicator,
} from '@/components';
import { useAuth } from '@/context/AuthContext';
import { useSettings } from '@/context/SettingsContext';
import { offlineCacheService } from '@/services';
import { SOURCE_LANGUAGES, TARGET_LANGUAGES } from '@/data/languages';
import { colors, palette, spacing, borderWidth } from '@/theme';

function ToggleRow({
  icon,
  label,
  description,
  value,
  onChange,
}: {
  icon: React.ComponentProps<typeof Ionicons>['name'];
  label: string;
  description?: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingVertical: spacing.sm }}>
      <Ionicons name={icon} size={20} color={colors.text} />
      <View style={{ flex: 1 }}>
        <AppText variant="bodyStrong">{label}</AppText>
        {description ? (
          <AppText variant="caption" color={colors.textMuted}>
            {description}
          </AppText>
        ) : null}
      </View>
      <Switch
        value={value}
        onValueChange={onChange}
        trackColor={{ true: colors.success, false: palette.sandDeep }}
        thumbColor={colors.white}
        ios_backgroundColor={palette.sandDeep}
      />
    </View>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={{ paddingVertical: spacing.sm }}>
      <AppText variant="label" color={colors.textMuted}>
        {label.toUpperCase()}
      </AppText>
      <AppText variant="body" style={{ marginTop: spacing.xxs }}>
        {value}
      </AppText>
    </View>
  );
}

export default function SettingsScreen() {
  const router = useRouter();
  const { profile, logout, updateProfile } = useAuth();
  const { settings, update } = useSettings();

  const clearCache = () => {
    const run = async () => {
      await offlineCacheService.clearCache();
    };
    Alert.alert('Clear offline cache?', 'Cached translations will be removed. Your saved translations are kept.', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Clear', style: 'destructive', onPress: () => void run() },
    ]);
  };

  const doLogout = () => {
    Alert.alert('Log out?', 'You will need to sign in again.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Log out',
        style: 'destructive',
        onPress: async () => {
          await logout();
          router.replace('/(auth)/login');
        },
      },
    ]);
  };

  return (
    <Screen title="Settings" showBack>
      {/* Profile */}
      <SectionHeader title="Profile" />
      <Card style={{ marginBottom: spacing.xl }}>
        <InfoRow label="Name" value={profile?.name ?? '—'} />
        <View style={{ height: borderWidth.thin, backgroundColor: colors.border }} />
        <InfoRow label="Email" value={profile?.email ?? '—'} />
        <View style={{ height: borderWidth.thin, backgroundColor: colors.border }} />
        <InfoRow label="School" value={profile?.school ?? '—'} />
      </Card>

      <LanguageSelector
        label="You teach in"
        value={profile?.teachingLanguage ?? 'hin'}
        options={SOURCE_LANGUAGES}
        onChange={(code) => void updateProfile({ teachingLanguage: code })}
        style={{ marginBottom: spacing.lg }}
      />
      <LanguageSelector
        label="Class's mother tongue"
        value={profile?.classroomLanguage ?? 'sat'}
        options={TARGET_LANGUAGES}
        onChange={(code) => void updateProfile({ classroomLanguage: code })}
        style={{ marginBottom: spacing.xl }}
      />

      {/* Preferences */}
      <SectionHeader title="Preferences" />
      <Card style={{ marginBottom: spacing.xl }}>
        <ToggleRow
          icon="text-outline"
          label="Show pronunciation"
          description="Display the romanised guide with translations"
          value={settings.showPronunciation}
          onChange={(v) => update({ showPronunciation: v })}
        />
        <View style={{ height: borderWidth.thin, backgroundColor: colors.border }} />
        <ToggleRow
          icon="phone-portrait-outline"
          label="Haptic feedback"
          description="Vibrate on taps and results"
          value={settings.hapticsEnabled}
          onChange={(v) => update({ hapticsEnabled: v })}
        />
      </Card>

      <LanguageSelector
        label="Default translate — from"
        value={settings.sourceLanguage}
        options={SOURCE_LANGUAGES}
        onChange={(code) => update({ sourceLanguage: code })}
        style={{ marginBottom: spacing.lg }}
      />
      <LanguageSelector
        label="Default translate — to"
        value={settings.targetLanguage}
        options={TARGET_LANGUAGES}
        onChange={(code) => update({ targetLanguage: code })}
        style={{ marginBottom: spacing.xl }}
      />

      <Card onPress={() => router.push('/settings/voice-profile')} style={{ marginBottom: spacing.xl }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.md }}>
          <Ionicons name="recording-outline" size={22} color={colors.text} />
          <View style={{ flex: 1 }}>
            <AppText variant="bodyStrong">Teacher voice profile</AppText>
            <AppText variant="caption" color={colors.textMuted}>
              How audio playback works in PALASH
            </AppText>
          </View>
          <Ionicons name="chevron-forward" size={20} color={colors.text} />
        </View>
      </Card>

      {/* Offline & data */}
      <SectionHeader title="Offline & data" />
      <Card style={{ marginBottom: spacing.xl }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: spacing.sm }}>
          <AppText variant="bodyStrong">Connectivity</AppText>
          <OfflineIndicator />
        </View>
        <View style={{ height: borderWidth.thin, backgroundColor: colors.border, marginVertical: spacing.sm }} />
        <Button title="Clear offline cache" icon="trash-outline" variant="outline" size="sm" onPress={clearCache} />
      </Card>

      {/* About & honesty (spec §60/§61/§72) */}
      <SectionHeader title="About & data honesty" />
      <Card backgroundColor={palette.sand} style={{ marginBottom: spacing.xl }}>
        <View style={{ gap: spacing.sm }}>
          <StatusBadge label="Demo build" tone="processing" icon="flask-outline" />
          <AppText variant="bodySmall">
            Translations come from a small, human-verified Hindi→Santali demo dictionary seeded from
            real classroom phrases. It is a demo, not a production translation model, and does not
            claim linguistic completeness.
          </AppText>
          <AppText variant="bodySmall">
            Audio uses your device's built-in text-to-speech as an approximation. There is no Santali
            AI voice, and no real speech recognition (ASR) — Voice runs in an explicit demo mode.
          </AppText>
          <AppText variant="bodySmall">
            No student voice is recorded or stored. Ho and Mundari have no demo data yet, so the app
            reports them as unavailable rather than inventing translations.
          </AppText>
        </View>
      </Card>

      <Button title="Log out" icon="log-out-outline" variant="danger" onPress={doLogout} fullWidth />
    </Screen>
  );
}
