import { storageService, STORAGE_KEYS } from './storageService';
import { lessonsApi, tokenStore, ApiError } from './apiClient';
import { LESSONS, getLesson } from '@/data/lessons';
import type { Lesson } from '@/types';

/** Map a backend lesson to the frontend Lesson shape. */
function mapBackendLesson(l: {
  id: string;
  curriculum_id: string;
  unit_number?: number;
  lesson_number?: number;
  title_hindi?: string;
  topic?: string;
  learning_outcomes?: string[];
  vocabulary?: Array<{ hindi: string; gloss?: string }>;
  activities?: string[];
  assessments?: string[];
}): Lesson {
  return {
    id: l.id,
    curriculumId: l.curriculum_id,
    unit: l.unit_number ?? 1,
    lessonNumber: l.lesson_number ?? 1,
    titleHindi: l.title_hindi ?? '',
    topic: l.topic ?? '',
    learningOutcomes: l.learning_outcomes ?? [],
    activities: l.activities ?? [],
    assessments: l.assessments ?? [],
    vocabulary: l.vocabulary ?? [],
    status: 'PUBLISHED',
    savedAt: new Date().toISOString(),
  };
}

/**
 * Lesson service.
 *
 * When authenticated and online, fetches from the backend and merges with
 * locally saved lessons. Falls back to bundled demo data when offline.
 */
export const lessonService = {
  async list(): Promise<Lesson[]> {
    const user = await storageService.getItem<Lesson[]>(STORAGE_KEYS.userLessons, []);
    const userIds = new Set(user.map((l) => l.id));

    // Try backend when authenticated.
    if (tokenStore.isAuthenticated()) {
      try {
        const res = await lessonsApi.list({ limit: 100 });
        const backendLessons = res.lessons.map(mapBackendLesson);
        // User-saved lessons take precedence.
        const merged = [
          ...user,
          ...backendLessons.filter((l) => !userIds.has(l.id)),
        ];
        return merged.sort((a, b) => b.savedAt.localeCompare(a.savedAt));
      } catch (err) {
        if (!(err instanceof ApiError && err.isNetworkError)) {
          console.warn('[lessonService] backend error:', err);
        }
        // Fall through to local data.
      }
    }

    // Offline: merge user lessons with bundled demo data.
    const merged = [...user, ...LESSONS.filter((l) => !userIds.has(l.id))];
    return merged.sort((a, b) => b.savedAt.localeCompare(a.savedAt));
  },

  async get(id: string): Promise<Lesson | null> {
    // Check locally saved first.
    const user = await storageService.getItem<Lesson[]>(STORAGE_KEYS.userLessons, []);
    const local = user.find((l) => l.id === id) ?? getLesson(id) ?? null;

    // Try backend for the full detail payload.
    if (tokenStore.isAuthenticated()) {
      try {
        const l = await lessonsApi.get(id);
        return mapBackendLesson(l);
      } catch (err) {
        if (!(err instanceof ApiError && err.isNetworkError)) {
          console.warn('[lessonService] backend get error:', err);
        }
      }
    }

    return local;
  },

  async save(lesson: Lesson): Promise<void> {
    const user = await storageService.getItem<Lesson[]>(STORAGE_KEYS.userLessons, []);
    const next = [lesson, ...user.filter((l) => l.id !== lesson.id)];
    await storageService.setItem(STORAGE_KEYS.userLessons, next);
  },
};
