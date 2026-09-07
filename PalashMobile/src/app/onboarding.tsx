import React, { useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Screen, AppText, Button, Card, LanguageSelector, MotifRow } from '@/components';
import { useAuth } from '@/context/AuthContext';
import { SOURCE_LANGUAGES, TARGET_LANGUAGES } from '@/data/languages';
import { colors, palette, spacing, radius, borderWidth } from '@/theme';

const STEPS: { icon: React.ComponentProps<typeof Ionicons>['name']; title: string; body: string }[] = [
  {
    icon: 'language-outline',
    title: 'Translate with context',
    body: 'Type a Hindi phrase and get a mother-tongue version from a verified demo dictionary — full sentences, not word-by-word.',
  },
  {
    icon: 'cloud-offline-outline',
    title: 'Works offline-first',
    body: 'Translations you use are cached on the device so they keep working without a network in the classroom.',
  },
  {
    icon: 'shield-checkmark-outline',
    title: 'Honest about limits',
    body: 'Demo data is clearly labelled. PALASH never invents a translation it does not actually have.',
  },
];

export default function OnboardingScreen() {
  const router = useRouter();
  const { profile, completeOnboarding } = useAuth();
  const [teachingLanguage, setTeachingLanguage] = useState('hin');
  const [classroomLanguage, setClassroomLanguage] = useState(profile?.preferredLanguage ?? 'sat');
  const [saving, setSaving] = useState(false);

  const finish = async () => {
    setSaving(true);
    await completeOnboarding({ teachingLanguage, classroomLanguage });
    setSaving(false);
    router.replace('/(tabs)');
  };

  return (
    <Screen
      title={`Welcome${profile?.name ? `, ${profile.name.split(' ')[0]}` : ''}`}
      subtitle="A quick setup before you start"
      footer={<Button title="Start teaching" icon="arrow-forward" onPress={finish} loading={saving} fullWidth />}
    >
      <MotifRow shape="diamond" count={7} size={12} color={palette.mustard} style={{ width: 170, marginBottom: spacing.lg }} />

      {STEPS.map((step) => (
        <Card key={step.title} style={{ marginBottom: spacing.md }}>
          <View style={{ flexDirection: 'row', gap: spacing.md, alignItems: 'flex-start' }}>
            <View
              style={{
                width: 44,
                height: 44,
                borderRadius: radius.md,
                borderWidth: borderWidth.thin,
                borderColor: colors.border,
                backgroundColor: colors.surfaceAlt,
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Ionicons name={step.icon} size={24} color={colors.primary} />
            </View>
            <View style={{ flex: 1 }}>
              <AppText variant="bodyStrong">{step.title}</AppText>
              <AppText variant="bodySmall" color={colors.textMuted} style={{ marginTop: spacing.xxs }}>
                {step.body}
              </AppText>
            </View>
          </View>
        </Card>
      ))}

      <AppText variant="h3" style={{ marginTop: spacing.lg, marginBottom: spacing.md }}>
        Your languages
      </AppText>
      <LanguageSelector
        label="You teach in"
        value={teachingLanguage}
        options={SOURCE_LANGUAGES}
        onChange={setTeachingLanguage}
        style={{ marginBottom: spacing.lg }}
      />
      <LanguageSelector
        label="Your class's mother tongue"
        value={classroomLanguage}
        options={TARGET_LANGUAGES}
        onChange={setClassroomLanguage}
      />
      <AppText variant="caption" color={colors.textMuted} style={{ marginTop: spacing.sm }}>
        You can change these any time in Settings.
      </AppText>
    </Screen>
  );
}
