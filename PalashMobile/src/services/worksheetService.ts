import { storageService, STORAGE_KEYS } from './storageService';
import { WORKSHEETS, getWorksheet } from '@/data/worksheets';
import type { Worksheet, WorksheetQuestion } from '@/types';

export interface WorksheetInput {
  title: string;
  classGrade: number;
  subject: string;
  topic: string;
  questionCount: number;
}

/**
 * Worksheet service. Returns bundled demo worksheets merged with the teacher's
 * locally-created ones.
 *
 * `create` builds a worksheet from a simple TEMPLATE -- it is NOT AI-generated
 * (spec §2: no fake AI). The UI must label these as template-based scaffolds
 * for the teacher to complete, not machine-authored content.
 */
export const worksheetService = {
  async list(): Promise<Worksheet[]> {
    const user = await storageService.getItem<Worksheet[]>(STORAGE_KEYS.userWorksheets, []);
    const userIds = new Set(user.map((w) => w.id));
    const merged = [...user, ...WORKSHEETS.filter((w) => !userIds.has(w.id))];
    return merged.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  },

  async get(id: string): Promise<Worksheet | null> {
    const user = await storageService.getItem<Worksheet[]>(STORAGE_KEYS.userWorksheets, []);
    return user.find((w) => w.id === id) ?? getWorksheet(id) ?? null;
  },

  /** Build a template worksheet scaffold (not AI-generated) and persist it. */
  async create(input: WorksheetInput): Promise<Worksheet> {
    const count = Math.max(1, Math.min(input.questionCount, 20));
    const questions: WorksheetQuestion[] = Array.from({ length: count }, (_, i) => ({
      id: `q${i + 1}`,
      type: 'short',
      prompt: `${input.topic} — प्रश्न ${i + 1}: ____________________`,
    }));

    const worksheet: Worksheet = {
      id: `ws-${Date.now()}`,
      title: input.title.trim() || input.topic.trim(),
      classGrade: input.classGrade,
      subject: input.subject,
      topic: input.topic.trim(),
      status: 'DRAFT',
      createdAt: new Date().toISOString(),
      questions,
    };

    const user = await storageService.getItem<Worksheet[]>(STORAGE_KEYS.userWorksheets, []);
    await storageService.setItem(STORAGE_KEYS.userWorksheets, [worksheet, ...user]);
    return worksheet;
  },
};
