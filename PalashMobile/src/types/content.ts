/** Curriculum, lesson, worksheet and activity content types. */

export interface Curriculum {
  id: string;
  title: string;
  board: string; // e.g. 'JCERT'
  state: string; // e.g. 'Jharkhand'
  classGrade: number;
  subject: string;
  medium: string; // language of instruction, e.g. 'Hindi'
  description: string;
  lessonIds: string[];
}

export interface VocabularyItem {
  hindi: string;
  gloss?: string; // short English gloss for clarity
}

export interface Lesson {
  id: string;
  curriculumId: string;
  unit: number;
  lessonNumber: number;
  titleHindi: string;
  topic: string;
  learningOutcomes: string[];
  activities: string[];
  assessments: string[];
  vocabulary: VocabularyItem[];
  /** Local library metadata (for "My Lessons"). */
  status: 'PUBLISHED' | 'DRAFT';
  savedAt: string; // ISO timestamp
}

export type WorksheetStatus = 'DRAFT' | 'READY';
export type QuestionType = 'mcq' | 'short' | 'fill';

export interface WorksheetQuestion {
  id: string;
  type: QuestionType;
  prompt: string;
  options?: string[]; // for mcq
  answer?: string;
}

export interface Worksheet {
  id: string;
  title: string;
  classGrade: number;
  subject: string;
  topic: string;
  status: WorksheetStatus;
  createdAt: string; // ISO timestamp
  questions: WorksheetQuestion[];
}

export type ActivityKind = 'translation' | 'voice' | 'worksheet' | 'lesson' | 'curriculum';

export interface ActivityItem {
  id: string;
  kind: ActivityKind;
  title: string;
  subtitle?: string;
  timestamp: string; // ISO timestamp
}
