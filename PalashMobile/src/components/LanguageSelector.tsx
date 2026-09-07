import React, { useState } from 'react';
import { Modal, Pressable, ScrollView, View, type StyleProp, type ViewStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppText } from './AppText';
import { NeoSurface } from './NeoSurface';
import { StatusBadge } from './StatusBadge';
import { colors, spacing, radius, borderWidth } from '@/theme';
import type { Language } from '@/types';

interface LanguageSelectorProps {
  label: string;
  value: string;
  options: Language[];
  onChange: (code: string) => void;
  style?: StyleProp<ViewStyle>;
}

/**
 * Language chip that opens a modal picker. Languages without real demo data are
 * clearly marked "no demo data" so the teacher is never misled into expecting a
 * working translation (spec §61).
 */
export function LanguageSelector({ label, value, options, onChange, style }: LanguageSelectorProps) {
  const [open, setOpen] = useState(false);
  const selected = options.find((l) => l.code === value);

  return (
    <View style={style}>
      <AppText variant="label" color={colors.textMuted} style={{ marginBottom: spacing.xs }}>
        {label.toUpperCase()}
      </AppText>
      <Pressable onPress={() => setOpen(true)} accessibilityRole="button">
        {({ pressed }) => (
          <NeoSurface shadowSize="sm" backgroundColor={colors.surface} pressed={pressed}>
            <View
              style={{
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingVertical: spacing.md,
                paddingHorizontal: spacing.md,
                gap: spacing.sm,
              }}
            >
              <View style={{ flex: 1 }}>
                <AppText variant="subtitle" numberOfLines={1}>
                  {selected ? selected.name : 'Select'}
                </AppText>
                {selected ? (
                  <AppText variant="caption" color={colors.textMuted}>
                    {selected.nativeName} · {selected.script}
                  </AppText>
                ) : null}
              </View>
              <Ionicons name="chevron-down" size={20} color={colors.text} />
            </View>
          </NeoSurface>
        )}
      </Pressable>

      <Modal visible={open} transparent animationType="fade" onRequestClose={() => setOpen(false)}>
        <Pressable
          onPress={() => setOpen(false)}
          style={{
            flex: 1,
            backgroundColor: 'rgba(42,42,42,0.55)',
            justifyContent: 'center',
            padding: spacing.xl,
          }}
        >
          <Pressable onPress={() => {}} style={{ maxHeight: '70%' }}>
            <NeoSurface shadowSize="lg" backgroundColor={colors.background}>
              <View style={{ padding: spacing.lg }}>
                <AppText variant="h3" style={{ marginBottom: spacing.md }}>
                  {label}
                </AppText>
                <ScrollView>
                  {options.map((lang) => {
                    const active = lang.code === value;
                    return (
                      <Pressable
                        key={lang.code}
                        onPress={() => {
                          onChange(lang.code);
                          setOpen(false);
                        }}
                        style={{
                          flexDirection: 'row',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          paddingVertical: spacing.md,
                          paddingHorizontal: spacing.md,
                          marginBottom: spacing.sm,
                          borderWidth: borderWidth.thin,
                          borderColor: colors.border,
                          borderRadius: radius.sm,
                          backgroundColor: active ? colors.surfaceAlt : colors.surface,
                        }}
                      >
                        <View style={{ flex: 1 }}>
                          <AppText variant="subtitle">{lang.name}</AppText>
                          <AppText variant="caption" color={colors.textMuted}>
                            {lang.nativeName} · {lang.script}
                          </AppText>
                        </View>
                        {!lang.demoSupported ? (
                          <StatusBadge label="No demo data" tone="neutral" />
                        ) : active ? (
                          <Ionicons name="checkmark-circle" size={22} color={colors.success} />
                        ) : null}
                      </Pressable>
                    );
                  })}
                </ScrollView>
              </View>
            </NeoSurface>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
}
