import React, { useState } from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Screen, AppText, Input, Button, Card, MotifRow } from '@/components';
import { useAuth } from '@/context/AuthContext';
import { DEMO_TEACHER } from '@/data/account';

const DEMO_PASSWORD = 'demo1234';
import { colors, palette, spacing } from '@/theme';
import type { TeacherProfile } from '@/types';

export default function LoginScreen() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);

  const goNext = (profile?: TeacherProfile) => {
    router.replace(profile?.onboarded ? '/(tabs)' : '/onboarding');
  };

  const submit = async (creds?: { email: string; password: string }) => {
    setError(undefined);
    setLoading(true);
    const result = await login(creds ?? { email, password });
    setLoading(false);
    if (!result.ok) {
      setError(result.error ?? 'Could not sign in.');
      return;
    }
    goNext(result.profile);
  };

  const useDemo = () => {
    setEmail(DEMO_TEACHER.email);
    setPassword(DEMO_PASSWORD);
    void submit({ email: DEMO_TEACHER.email, password: DEMO_PASSWORD });
  };

  return (
    <Screen>
      <View style={{ alignItems: 'center', marginTop: spacing.xl, marginBottom: spacing.xxl }}>
        <AppText variant="display" color={palette.terracotta}>
          PALASH
        </AppText>
        <AppText variant="bodySmall" color={colors.textMuted} center style={{ marginTop: spacing.xs }}>
          Sign in to your teacher account
        </AppText>
        <MotifRow shape="triangle" count={6} size={12} color={palette.mustard} style={{ width: 150, marginTop: spacing.lg }} />
      </View>

      <Input
        label="Email"
        value={email}
        onChangeText={setEmail}
        placeholder="teacher@school.gov.in"
        keyboardType="email-address"
        autoCapitalize="none"
        style={{ marginBottom: spacing.lg }}
      />
      <Input
        label="Password"
        value={password}
        onChangeText={setPassword}
        placeholder="Your password"
        secureTextEntry
        error={error}
        style={{ marginBottom: spacing.xl }}
      />

      <Button title="Log in" icon="log-in-outline" onPress={() => submit()} loading={loading} fullWidth />

      <View style={{ flexDirection: 'row', justifyContent: 'center', marginTop: spacing.xl, gap: spacing.xs }}>
        <AppText variant="body" color={colors.textMuted}>
          New teacher?
        </AppText>
        <Pressable onPress={() => router.push('/(auth)/register')} hitSlop={8}>
          <AppText variant="bodyStrong" color={colors.primary}>
            Create an account
          </AppText>
        </Pressable>
      </View>

      <Card backgroundColor={colors.surfaceAlt} style={{ marginTop: spacing.xxl }}>
        <AppText variant="label" color={colors.textMuted}>
          DEMO ACCOUNT
        </AppText>
        <AppText variant="bodySmall" style={{ marginTop: spacing.xs }}>
          {DEMO_TEACHER.email}
        </AppText>
        <AppText variant="bodySmall" style={{ marginBottom: spacing.md }}>
          Password: {DEMO_PASSWORD}
        </AppText>
        <Button title="Use demo account" icon="flash-outline" variant="accent" size="sm" onPress={useDemo} />
      </Card>
    </Screen>
  );
}
