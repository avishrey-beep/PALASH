import type { Lesson } from '@/types';

/**
 * Demo lesson library ("My Lessons" + curriculum content).
 *
 * Lesson 1 is the project's real seeded JCERT Class 2 Mathematics lesson
 * (`data/seed/init_db.py`), copied verbatim. Lessons 2-3 are additional
 * Hindi-medium demo lesson plans for the prototype. All content is in Hindi/
 * English (the teacher's languages); no target-language material is fabricated
 * here.
 */
export const LESSONS: Lesson[] = [
  {
    id: 'lesson-num-1',
    curriculumId: 'cur-jcert-c2-math',
    unit: 1,
    lessonNumber: 1,
    titleHindi: 'संख्याओं का खेल - २० तक जोड़',
    topic: 'Addition up to 20 with concrete objects',
    learningOutcomes: [
      'Children can count objects from 1 to 20 in their home language and Hindi',
      'Children understand combining two groups of objects (addition)',
      'Children can verbally state the total number of objects',
    ],
    activities: [
      'Use tamarind seeds (imli ke beej) or pebbles to count up to 10',
      'Combine 3 pebbles and 2 pebbles, then count total',
      'Peer counting game in pairs',
    ],
    assessments: [
      'गिनो और बताओ: कितने आम हैं?',
      '३ और २ मिलाकर कितने होते हैं?',
      'अपनी किताब में दिए गए चित्रों को गिनकर लिखो।',
    ],
    vocabulary: [
      { hindi: 'जोड़', gloss: 'addition' },
      { hindi: 'गिनती', gloss: 'counting' },
      { hindi: 'कुल', gloss: 'total' },
      { hindi: 'बराबर', gloss: 'equals' },
    ],
    status: 'PUBLISHED',
    savedAt: '2026-08-21T09:15:00.000Z',
  },
  {
    id: 'lesson-num-2',
    curriculumId: 'cur-jcert-c2-math',
    unit: 1,
    lessonNumber: 2,
    titleHindi: 'घटाव की समझ - २० तक',
    topic: 'Subtraction up to 20 by taking away objects',
    learningOutcomes: [
      'Children understand "taking away" from a group of objects',
      'Children can find how many objects remain',
      'Children relate subtraction to everyday sharing situations',
    ],
    activities: [
      'Start with 8 pebbles, take away 3, count what remains',
      'Story sums: 5 mangoes, 2 are eaten — how many are left?',
      'Draw and cross out to show subtraction',
    ],
    assessments: [
      'सात में से तीन निकालो, कितने बचे?',
      'चित्र देखकर घटाव लिखो।',
    ],
    vocabulary: [
      { hindi: 'घटाव', gloss: 'subtraction' },
      { hindi: 'बचा', gloss: 'remaining' },
      { hindi: 'निकालो', gloss: 'take away' },
    ],
    status: 'PUBLISHED',
    savedAt: '2026-08-24T11:40:00.000Z',
  },
  {
    id: 'lesson-shapes-1',
    curriculumId: 'cur-jcert-c2-math',
    unit: 2,
    lessonNumber: 1,
    titleHindi: 'आकृतियाँ पहचानो',
    topic: 'Recognising basic shapes around us',
    learningOutcomes: [
      'Children can name circle, triangle and square',
      'Children can spot these shapes in classroom objects',
    ],
    activities: [
      'Shape hunt: find round, three-cornered and four-cornered objects',
      'Draw shapes in sand or on slate',
    ],
    assessments: ['कमरे में गोल चीज़ें ढूँढो और बताओ।'],
    vocabulary: [
      { hindi: 'गोल', gloss: 'circle / round' },
      { hindi: 'तिकोना', gloss: 'triangle' },
      { hindi: 'चौकोर', gloss: 'square' },
    ],
    status: 'DRAFT',
    savedAt: '2026-09-01T08:05:00.000Z',
  },
];

export function getLesson(id: string): Lesson | undefined {
  return LESSONS.find((l) => l.id === id);
}
