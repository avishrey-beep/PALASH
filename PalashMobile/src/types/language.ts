/** A language PALASH can work with. */
export interface Language {
  /** ISO 639-3 code, e.g. 'hin', 'sat', 'unr', 'hoc'. */
  code: string;
  /** English name. */
  name: string;
  /** Endonym (name in its own script). */
  nativeName: string;
  /** Script name, e.g. 'Devanagari', 'Ol Chiki'. */
  script: string;
  /** Usable as a translation *source* (the teacher's input language). */
  isSource: boolean;
  /** Usable as a translation *target* (the classroom mother tongue). */
  isTarget: boolean;
  /**
   * Whether the offline demo actually ships real, human-verified sample data
   * for this language. Honesty flag: the UI must not imply support we cannot
   * demonstrate (spec §61). Only Santali is `true` in this prototype.
   */
  demoSupported: boolean;
}
