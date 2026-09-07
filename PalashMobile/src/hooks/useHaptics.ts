import { useCallback } from 'react';
import { Platform } from 'react-native';
import * as Haptics from 'expo-haptics';
import { useSettings } from '@/context/SettingsContext';

/**
 * Haptics that respect the user's setting and no-op safely on web. Kept tiny so
 * any tactile element (Button, chips) can add feel without repeating guards.
 */
export function useHaptics() {
  const { settings } = useSettings();
  const enabled = settings.hapticsEnabled && Platform.OS !== 'web';

  const tap = useCallback(() => {
    if (!enabled) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
  }, [enabled]);

  const success = useCallback(() => {
    if (!enabled) return;
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
  }, [enabled]);

  const warn = useCallback(() => {
    if (!enabled) return;
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});
  }, [enabled]);

  return { tap, success, warn };
}
