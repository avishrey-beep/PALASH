import React, { useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { Screen, AppText, Input, Button, LanguageSelector } from '@/components';
import { useAuth } from '@/context/AuthContext';
import { TARGET_LANGUAGES } from '@/data/languages';
import { colors, spacing } from '@/theme';

export default function RegisterScreen() {
  const router = useRouter();
  const { register } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [school, setSchool] = useState('');
  const [preferredLanguage, setPreferredLanguage] = useState('sat');
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setError(undefined);
    setLoading(true);
    const result = await register({ name, email, password, school, preferredLanguage });
    setLoading(false);
    if (!result.ok) {
      setError(result.error ?? 'Could not create account.');
      return;
    }
    // New accounts always start un-onboarded.
    router.replace('/onboarding');
  };

  return (
    <Screen title="Create account" subtitle="Set up your teacher profile" showBack>
      <View style={{ marginTop: spacing.md }}>
        <Input label="Full name" value={name} onChangeText={setName} placeholder="e.g. Sunita Soren" autoCapitalize="words" style={{ marginBottom: spacing.lg }} />
        <Input label="Email" value={email} onChangeText={setEmail} placeholder="teacher@school.gov.in" keyboardType="email-address" style={{ marginBottom: spacing.lg }} />
        <Input label="Password" value={password} onChangeText={setPassword} placeholder="At least 4 characters" secureTextEntry style={{ marginBottom: spacing.lg }} />
        <Input label="School" value={school} onChangeText={setSchool} placeholder="e.g. GPS Dumka 01" autoCapitalize="words" style={{ marginBottom: spacing.lg }} />
        <LanguageSelector
          label="Preferred classroom language"
          value={preferredLanguage}
          options={TARGET_LANGUAGES}
          onChange={setPreferredLanguage}
          style={{ marginBottom: spacing.md }}
        />
        {error ? (
          <AppText variant="caption" color={colors.danger} style={{ marginBottom: spacing.md }}>
            {error}
          </AppText>
        ) : null}
        <Button title="Create account" icon="person-add-outline" onPress={submit} loading={loading} fullWidth style={{ marginTop: spacing.md }} />
      </View>
    </Screen>
  );
}
