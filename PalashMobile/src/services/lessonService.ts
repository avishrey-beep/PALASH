import { storageService, STORAGE_KEYS } from './storageService';
import { LESSONS, getLesson } from '@/data/lessons';
import type { Lesson } from '@/types';

/**
 * Lesson service. Returns the bundled demo lessons merged with any lessons the
 * teacher saved locally ("My Lessons"). User lessons take precedence on id.
 */
export const lessonService = {
  async list(): Promise<Lesson[]> {
    const user = await storageService.getItem<Lesson[]>(STORAGE_KEYS.userLessons, []);
    const userIds = new Set(user.map((l) => l.id));
    const merged = [...user, ...LESSONS.filter((l) => !userIds.has(l.id))];
    // Most-recently saved first.
    return merged.sort((a, b) => b.savedAt.localeCompare(a.savedAt));
  },

  async get(id: string): Promise<Lesson | null> {
    const user = await storageService.getItem<Lesson[]>(STORAGE_KEYS.userLessons, []);
    return user.find((l) => l.id === id) ?? getLesson(id) ?? null;
  },

  async save(lesson: Lesson): Promise<void> {
    const user = await storageService.getItem<Lesson[]>(STORAGE_KEYS.userLessons, []);
    const next = [lesson, ...user.filter((l) => l.id !== lesson.id)];
    await storageService.setItem(STORAGE_KEYS.userLessons, next);
  },
};
