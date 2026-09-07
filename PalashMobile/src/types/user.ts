/** The signed-in teacher. Mock auth in Phase 1; shape mirrors the backend. */
export interface TeacherProfile {
  id: string;
  name: string;
  email: string;
  school: string;
  /** Language the teacher writes/speaks in (source), usually Hindi 'hin'. */
  teachingLanguage: string;
  /** Target classroom mother tongue, e.g. 'sat'. */
  classroomLanguage: string;
  /** Preferred UI/content language code. */
  preferredLanguage: string;
  /** Whether onboarding has been completed. */
  onboarded: boolean;
}

export interface Credentials {
  email: string;
  password: string;
}

export interface RegistrationInput {
  name: string;
  email: string;
  password: string;
  school: string;
  preferredLanguage: string;
}
