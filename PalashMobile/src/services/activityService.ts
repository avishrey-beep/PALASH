import { storageService, STORAGE_KEYS } from './storageService';
import { SEED_ACTIVITY } from '@/data/account';
import type { ActivityItem } from '@/types';

const MAX_ITEMS = 25;

/**
 * Recent-activity feed for the home dashboard.
 *
 * Merges the demo seed activity with events logged during use (translations,
 * opened lessons, created worksheets). Stored locally only.
 */
export const activityService = {
  async list(): Promise<ActivityItem[]> {
    const logged = await storageService.getItem<ActivityItem[]>(STORAGE_KEYS.activity, []);
    const loggedIds = new Set(logged.map((a) => a.id));
    const merged = [...logged, ...SEED_ACTIVITY.filter((a) => !loggedIds.has(a.id))];
    return merged
      .sort((a, b) => b.timestamp.localeCompare(a.timestamp))
      .slice(0, MAX_ITEMS);
  },

  async log(item: Omit<ActivityItem, 'id' | 'timestamp'>): Promise<void> {
    const logged = await storageService.getItem<ActivityItem[]>(STORAGE_KEYS.activity, []);
    const entry: ActivityItem = {
      ...item,
      id: `act-${Date.now()}`,
      timestamp: new Date().toISOString(),
    };
    await storageService.setItem(STORAGE_KEYS.activity, [entry, ...logged].slice(0, MAX_ITEMS));
  },
};
