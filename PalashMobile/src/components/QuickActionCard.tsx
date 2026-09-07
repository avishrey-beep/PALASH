import React from 'react';
import { View, type StyleProp, type ViewStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Card } from './Card';
import { AppText } from './AppText';
import { colors, spacing, radius, borderWidth } from '@/theme';

type IconName = React.ComponentProps<typeof Ionicons>['name'];

interface QuickActionCardProps {
  title: string;
  subtitle?: string;
  icon: IconName;
  background?: string;
  foreground?: string;
  onPress: () => void;
  style?: StyleProp<ViewStyle>;
}

/** Big tactile action tile for the home dashboard quick actions. */
export function QuickActionCard({
  title,
  subtitle,
  icon,
  background = colors.surface,
  foreground = colors.text,
  onPress,
  style,
}: QuickActionCardProps) {
  return (
    <Card onPress={onPress} backgroundColor={background} padded={false} style={style} shadowSize="md">
      <View style={{ padding: spacing.lg, minHeight: 112, justifyContent: 'space-between' }}>
        <View
          style={{
            width: 44,
            height: 44,
            borderRadius: radius.sm,
            borderWidth: borderWidth.thin,
            borderColor: colors.border,
            backgroundColor: colors.surface,
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Ionicons name={icon} size={24} color={colors.text} />
        </View>
        <View style={{ marginTop: spacing.md }}>
          <AppText variant="subtitle" color={foreground}>
            {title}
          </AppText>
          {subtitle ? (
            <AppText variant="caption" color={foreground} style={{ opacity: 0.85, marginTop: spacing.xxs }}>
              {subtitle}
            </AppText>
          ) : null}
        </View>
      </View>
    </Card>
  );
}
