import React from 'react';
import { Pressable } from 'react-native';
import { StatusBadge } from './StatusBadge';
import { useSettings } from '@/context/SettingsContext';

/**
 * Live connectivity chip. Tapping it re-checks connectivity. The app is
 * offline-first, so being offline is a normal, non-error state -- labelled
 * "OFFLINE-READY" rather than as a failure.
 */
export function OfflineIndicator() {
  const { online, pendingSync, refreshConnectivity } = useSettings();

  const label = online
    ? pendingSync > 0
      ? `ONLINE · ${pendingSync} TO SYNC`
      : 'ONLINE'
    : 'OFFLINE-READY';

  return (
    <Pressable onPress={refreshConnectivity} accessibilityRole="button" accessibilityLabel="Connectivity status, tap to refresh">
      <StatusBadge
        label={label}
        tone={online ? 'online' : 'offline'}
        icon={online ? 'cloud-done-outline' : 'cloud-offline-outline'}
      />
    </Pressable>
  );
}
