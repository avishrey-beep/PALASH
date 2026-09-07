import React, { useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Screen, AppText, Input, Button, Card, ErrorBoundary } from '@/components';
import { worksheetService } from '@/services';
import { colors, palette, spacing } from '@/theme';

const SUBJECTS = ['Mathematics', 'EVS', 'Hindi'];
const GRADES = [1, 2, 3, 4, 5];
const COUNTS = [4, 6, 8, 10];

function ChipRow<T extends string | number>({
  options,
  value,
  onChange,
  format,
}: {
  options: readonly T[];
  value: T;
  onChange: (v: T) => void;
  format?: (v: T) => string;
}) {
  return (
    <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm }}>
      {options.map((opt) => (
        <Button
          key={String(opt)}
          title={format ? format(opt) : String(opt)}
          variant={opt === value ? 'primary' : 'outline'}
          size="sm"
          onPress={() => onChange(opt)}
        />
      ))}
    </View>
  );
}

function WorksheetCreateContent() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState<string>('Mathematics');
  const [topic, setTopic] = useState('');
  const [classGrade, setClassGrade] = useState<number>(2);
  const [questionCount, setQuestionCount] = useState<number>(6);
  const [error, setError] = useState<string | undefined>();
  const [creating, setCreating] = useState(false);

  const create = async () => {
    if (topic.trim().length === 0) {
      setError('Please enter a topic for the worksheet.');
      return;
    }
    setError(undefined);
    setCreating(true);
    const ws = await worksheetService.create({
      title: title.trim() || topic.trim(),
      subject,
      topic: topic.trim(),
      classGrade,
      questionCount,
    });
    setCreating(false);
    router.replace(`/worksheet/${ws.id}`);
  };

  return (
    <Screen
      title="New worksheet"
      subtitle="Build a printable template"
      showBack
      footer={<Button title="Create worksheet" icon="add-circle-outline" onPress={create} loading={creating} fullWidth />}
    >
      <Card backgroundColor={palette.sand} shadowSize="sm" style={{ marginBottom: spacing.xl }}>
        <View style={{ flexDirection: 'row', gap: spacing.sm, alignItems: 'flex-start' }}>
          <Ionicons name="information-circle-outline" size={20} color={colors.text} />
          <AppText variant="bodySmall" style={{ flex: 1 }}>
            PALASH builds a blank template with numbered questions for you to fill in. It does not
            auto-write questions with AI.
          </AppText>
        </View>
      </Card>

      <Input label="Title (optional)" value={title} onChangeText={setTitle} placeholder="e.g. जोड़ अभ्यास - २० तक" autoCapitalize="sentences" style={{ marginBottom: spacing.lg }} />
      <Input label="Topic" value={topic} onChangeText={setTopic} placeholder="e.g. Addition up to 20" autoCapitalize="sentences" style={{ marginBottom: spacing.lg }} />

      <AppText variant="label" color={colors.textMuted} style={{ marginBottom: spacing.sm }}>
        SUBJECT
      </AppText>
      <ChipRow options={SUBJECTS} value={subject} onChange={setSubject} />

      <AppText variant="label" color={colors.textMuted} style={{ marginTop: spacing.lg, marginBottom: spacing.sm }}>
        CLASS
      </AppText>
      <ChipRow options={GRADES} value={classGrade} onChange={setClassGrade} format={(g) => `Class ${g}`} />

      <AppText variant="label" color={colors.textMuted} style={{ marginTop: spacing.lg, marginBottom: spacing.sm }}>
        NUMBER OF QUESTIONS
      </AppText>
      <ChipRow options={COUNTS} value={questionCount} onChange={setQuestionCount} />

      {error ? (
        <AppText variant="caption" color={colors.danger} style={{ marginTop: spacing.lg }}>
          {error}
        </AppText>
      ) : null}
    </Screen>
  );
}

export default function WorksheetCreateScreen() {
  return (
    <ErrorBoundary fallbackTitle="Create worksheet error">
      <WorksheetCreateContent />
    </ErrorBoundary>
  );
}
