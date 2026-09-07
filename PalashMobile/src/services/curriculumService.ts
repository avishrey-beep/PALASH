import { storageService, STORAGE_KEYS } from './storageService';
import { curriculumApi, tokenStore, ApiError } from './apiClient';
import { CURRICULA, getCurriculum } from '@/data/curriculum';
import { LESSONS } from '@/data/lessons';
import type { Curriculum, Lesson } from '@/types';

function mapBackendCurriculum(c: {
  id: string;
  title: string;
  state: string;
  board: string;
  class_grade: number;
  subject: string;
  description?: string;
  lessons_count?: number;
}): Curriculum {
  return {
    id: c.id,
    title: c.title,
    board: c.board,
    state: c.state,
    classGrade: c.class_grade,
    subject: c.subject,
    medium: 'Hindi',
    description: c.description ?? '',
    lessonIds: [],
  };
}

export interface CurriculumInput {
  title: string;
  board: string;
  state: string;
  classGrade: number;
  subject: string;
  medium: string;
  description: string;
}

/**
 * Curriculum service. Reads the bundled demo curriculum data merged with any
 * curriculum outlines the teacher added locally on-device.
 *
 * `create` stores a manually-entered outline. It does NOT parse or auto-import
 * documents (that needs the backend, Phase 5) -- the Upload screen is explicit
 * about this so no non-existent capability is implied (spec §2).
 *
 * The async signatures mirror the future backend-backed service so screens
 * don't change when the data source is swapped in Phase 5.
 */
export const curriculumService = {
  async list(): Promise<Curriculum[]> {
    const user = await storageService.getItem<Curriculum[]>(STORAGE_KEYS.userCurricula, []);
    const userIds = new Set(user.map((c) => c.id));

    if (tokenStore.isAuthenticated()) {
      try {
        const backendList = await curriculumApi.list();
        const backendCurricula = backendList.map(mapBackendCurriculum);
        return [...user, ...backendCurricula.filter((c) => !userIds.has(c.id))];
      } catch (err) {
        if (!(err instanceof ApiError && err.isNetworkError)) {
          console.warn('[curriculumService] backend error:', err);
        }
      }
    }

    return [...user, ...CURRICULA.filter((c) => !userIds.has(c.id))];
  },

  async get(id: string): Promise<Curriculum | null> {
    const user = await storageService.getItem<Curriculum[]>(STORAGE_KEYS.userCurricula, []);
    const local = user.find((c) => c.id === id) ?? getCurriculum(id) ?? null;

    if (tokenStore.isAuthenticated()) {
      try {
        const c = await curriculumApi.get(id);
        return mapBackendCurriculum(c);
      } catch (err) {
        if (!(err instanceof ApiError && err.isNetworkError)) {
          console.warn('[curriculumService] backend get error:', err);
        }
      }
    }

    return local;
  },

  async lessonsFor(curriculumId: string): Promise<Lesson[]> {
    if (tokenStore.isAuthenticated()) {
      try {
        const res = await import('./apiClient').then(({ lessonsApi }) =>
          lessonsApi.list({ curriculum_id: curriculumId, limit: 100 }),
        );
        return res.lessons.map((l) => ({
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
          status: 'PUBLISHED' as const,
          savedAt: new Date().toISOString(),
        }));
      } catch {
        // Fall through to local data.
      }
    }
    return LESSONS.filter((l) => l.curriculumId === curriculumId);
  },

  /** Persist a manually-entered curriculum outline (no document parsing). */
  async create(input: CurriculumInput): Promise<Curriculum> {
    const curriculum: Curriculum = {
      id: `cur-${Date.now()}`,
      title: input.title.trim(),
      board: input.board.trim(),
      state: input.state.trim(),
      classGrade: input.classGrade,
      subject: input.subject.trim(),
      medium: input.medium.trim(),
      description: input.description.trim(),
      lessonIds: [],
    };
    const user = await storageService.getItem<Curriculum[]>(STORAGE_KEYS.userCurricula, []);
    await storageService.setItem(STORAGE_KEYS.userCurricula, [curriculum, ...user]);
    return curriculum;
  },
};
