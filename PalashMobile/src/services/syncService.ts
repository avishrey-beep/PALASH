import { storageService, STORAGE_KEYS } from './storageService';

/**
 * Sync service (offline-first).
 *
 * Phase 1 has NO backend, so nothing is actually uploaded yet. What is real:
 *  - a local pending-queue of items captured while offline, and
 *  - a best-effort connectivity check.
 *
 * `sync()` is intentionally a no-op placeholder that reports the queue state
 * honestly rather than pretending data was uploaded. The real upload path is
 * wired in Phase 5 against the FastAPI backend.
 */

export interface SyncMeta {
  lastSyncAt: string | null;
}

export interface SyncStatus {
  online: boolean;
  pending: number;
  lastSyncAt: string | null;
}

export interface PendingItem {
  id: string;
  kind: string;
  payload: unknown;
  queuedAt: string;
}

const CONNECTIVITY_TIMEOUT_MS = 2500;

export const syncService = {
  /** Genuine best-effort connectivity probe; false on any failure/timeout. */
  async checkConnectivity(): Promise<boolean> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), CONNECTIVITY_TIMEOUT_MS);
    try {
      // Lightweight, CORS-friendly, no-body endpoint.
      await fetch('https://clients3.google.com/generate_204', {
        method: 'GET',
        signal: controller.signal,
      });
      return true;
    } catch {
      return false;
    } finally {
      clearTimeout(timer);
    }
  },

  async pendingCount(): Promise<number> {
    const queue = await storageService.getItem<PendingItem[]>(STORAGE_KEYS.syncQueue, []);
    return queue.length;
  },

  async enqueue(kind: string, payload: unknown): Promise<void> {
    const queue = await storageService.getItem<PendingItem[]>(STORAGE_KEYS.syncQueue, []);
    queue.push({ id: `pending-${Date.now()}`, kind, payload, queuedAt: new Date().toISOString() });
    await storageService.setItem(STORAGE_KEYS.syncQueue, queue);
  },

  async getStatus(): Promise<SyncStatus> {
    const [online, pending, meta] = await Promise.all([
      this.checkConnectivity(),
      this.pendingCount(),
      storageService.getItem<SyncMeta>(STORAGE_KEYS.syncMeta, { lastSyncAt: null }),
    ]);
    return { online, pending, lastSyncAt: meta.lastSyncAt };
  },
};
