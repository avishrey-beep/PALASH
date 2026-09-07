import { storageService, STORAGE_KEYS } from './storageService';
import { CURRICULA, getCurriculum } from '@/data/curriculum';
import { LESSONS } from '@/data/lessons';
import type { Curriculum, Lesson } from '@/types';

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
    return [...user, ...CURRICULA.filter((c) => !userIds.has(c.id))];
  },

  async get(id: string): Promise<Curriculum | null> {
    const user = await storageService.getItem<Curriculum[]>(STORAGE_KEYS.userCurricula, []);
    return user.find((c) => c.id === id) ?? getCurriculum(id) ?? null;
  },

  async lessonsFor(curriculumId: string): Promise<Lesson[]> {
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
