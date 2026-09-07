import React, { useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Screen, AppText, Input, Button, Card, ErrorBoundary } from '@/components';
import { curriculumService } from '@/services';
import { colors, palette, spacing } from '@/theme';

const SUBJECTS = ['Mathematics', 'EVS', 'Hindi'];
const GRADES = [1, 2, 3, 4, 5];

function CurriculumUploadContent() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('Mathematics');
  const [classGrade, setClassGrade] = useState(2);
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | undefined>();
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (title.trim().length === 0) {
      setError('Please give the curriculum a title.');
      return;
    }
    setError(undefined);
    setSaving(true);
    await curriculumService.create({
      title,
      subject,
      classGrade,
      description,
      board: 'JCERT',
      state: 'Jharkhand',
      medium: 'Hindi',
    });
    setSaving(false);
    router.replace('/curriculum');
  };

  return (
    <Screen
      title="Add curriculum"
      subtitle="Create an outline on this device"
      showBack
      footer={<Button title="Save outline" icon="save-outline" onPress={save} loading={saving} fullWidth />}
    >
      {/* Honest note: no document parsing in the offline demo */}
      <Card backgroundColor={palette.sand} shadowSize="sm" style={{ marginBottom: spacing.xl }}>
        <View style={{ flexDirection: 'row', gap: spacing.sm, alignItems: 'flex-start' }}>
          <Ionicons name="document-attach-outline" size={20} color={colors.text} />
          <View style={{ flex: 1 }}>
            <AppText variant="bodyStrong">Manual outline</AppText>
            <AppText variant="bodySmall" color={colors.textMuted} style={{ marginTop: spacing.xxs }}>
              Automatic document upload and parsing needs the server and isn't part of the offline
              demo. You can add a curriculum outline by hand here — it's saved on this device.
            </AppText>
          </View>
        </View>
      </Card>

      <Input label="Title" value={title} onChangeText={setTitle} placeholder="e.g. JCERT Class 3 Mathematics" autoCapitalize="sentences" style={{ marginBottom: spacing.lg }} />

      <AppText variant="label" color={colors.textMuted} style={{ marginBottom: spacing.sm }}>
        SUBJECT
      </AppText>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm }}>
        {SUBJECTS.map((s) => (
          <Button key={s} title={s} variant={s === subject ? 'primary' : 'outline'} size="sm" onPress={() => setSubject(s)} />
        ))}
      </View>

      <AppText variant="label" color={colors.textMuted} style={{ marginTop: spacing.lg, marginBottom: spacing.sm }}>
        CLASS
      </AppText>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm }}>
        {GRADES.map((g) => (
          <Button key={g} title={`Class ${g}`} variant={g === classGrade ? 'primary' : 'outline'} size="sm" onPress={() => setClassGrade(g)} />
        ))}
      </View>

      <Input
        label="Description"
        value={description}
        onChangeText={setDescription}
        placeholder="What does this curriculum cover?"
        multiline
        numberOfLines={4}
        autoCapitalize="sentences"
        style={{ marginTop: spacing.lg }}
      />

      {error ? (
        <AppText variant="caption" color={colors.danger} style={{ marginTop: spacing.lg }}>
          {error}
        </AppText>
      ) : null}
    </Screen>
  );
}

export default function CurriculumUploadScreen() {
  return (
    <ErrorBoundary fallbackTitle="Add curriculum error">
      <CurriculumUploadContent />
    </ErrorBoundary>
  );
}
