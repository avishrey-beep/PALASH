import type { ActivityItem, TeacherProfile } from '@/types';

/**
 * Demo teacher account shown on the login screen.
 *
 * These are intentionally public demo credentials. The password matches the
 * backend seed (data/seed/init_db.py) so the demo login works whether the app
 * is running offline (local account store) or connected to the FastAPI backend.
 * Offline, the demo account also accepts any non-empty password for convenience.
 */
export const DEMO_TEACHER: TeacherProfile = {
  id: 'teacher-demo-01',
  name: 'Sunita Soren',
  email: 'teacher.dumka@schools.jharkhand.gov.in',
  school: 'GPS Dumka 01',
  teachingLanguage: 'hin',
  classroomLanguage: 'sat',
  preferredLanguage: 'sat',
  onboarded: true,
};

/** Single source of truth for the demo password (matches the backend seed). */
export const DEMO_PASSWORD = 'Teacher@Jharkhand2026';

/** Seed "recent activity" shown on the home dashboard for the demo account. */
export const SEED_ACTIVITY: ActivityItem[] = [
  {
    id: 'act-1',
    kind: 'translation',
    title: 'बैठ जाओ',
    subtitle: 'Hindi → Santali',
    timestamp: '2026-09-06T05:20:00.000Z',
  },
  {
    id: 'act-2',
    kind: 'lesson',
    title: 'संख्याओं का खेल - २० तक जोड़',
    subtitle: 'Opened lesson',
    timestamp: '2026-09-05T09:10:00.000Z',
  },
  {
    id: 'act-3',
    kind: 'worksheet',
    title: 'जोड़ अभ्यास - २० तक',
    subtitle: 'Worksheet',
    timestamp: '2026-09-04T12:45:00.000Z',
  },
];
