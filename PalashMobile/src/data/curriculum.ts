import type { Curriculum } from '@/types';
import { LESSONS } from './lessons';

/**
 * Demo curriculum list. The primary entry mirrors the project's real seeded
 * JCERT Class 2 Mathematics curriculum. A second EVS entry is included so the
 * curriculum browser has more than one row; it is clearly a demo placeholder
 * with no lessons attached yet.
 */
export const CURRICULA: Curriculum[] = [
  {
    id: 'cur-jcert-c2-math',
    title: 'JCERT Class 2 Mathematics - Ganit Khel',
    board: 'JCERT',
    state: 'Jharkhand',
    classGrade: 2,
    subject: 'Mathematics',
    medium: 'Hindi',
    description:
      'Foundational Literacy and Numeracy (FLN) Grade 2 mathematics curriculum focusing on counting and addition up to 20.',
    lessonIds: LESSONS.filter((l) => l.curriculumId === 'cur-jcert-c2-math').map((l) => l.id),
  },
  {
    id: 'cur-jcert-c2-evs',
    title: 'JCERT Class 2 EVS - Aas-Paas',
    board: 'JCERT',
    state: 'Jharkhand',
    classGrade: 2,
    subject: 'EVS',
    medium: 'Hindi',
    description:
      'Environmental Studies for Grade 2 exploring plants, water and the local surroundings. (Demo entry — lessons not yet imported.)',
    lessonIds: [],
  },
];

export function getCurriculum(id: string): Curriculum | undefined {
  return CURRICULA.find((c) => c.id === id);
}
