import type { Language } from '@/types';

/**
 * Languages PALASH knows about, mirroring the backend's seeded set.
 *
 * Only Hindi (source) and Santali (target) have real demo data in this
 * prototype, so `demoSupported` is true only for those. Mundari and Ho are
 * listed because the platform targets them, but the app must NOT imply working
 * translation for them (spec §61) -- selecting them yields an honest
 * "not available in the offline demo" result, never a fabricated one.
 */
export const LANGUAGES: Language[] = [
  {
    code: 'hin',
    name: 'Hindi',
    nativeName: 'हिन्दी',
    script: 'Devanagari',
    isSource: true,
    isTarget: false,
    demoSupported: true,
  },
  {
    code: 'sat',
    name: 'Santali',
    nativeName: 'ᱥᱟᱱᱛᱟᱲᱤ',
    script: 'Ol Chiki',
    isSource: false,
    isTarget: true,
    demoSupported: true,
  },
  {
    code: 'unr',
    name: 'Mundari',
    nativeName: 'मुंडारी',
    script: 'Mundari Bani / Devanagari',
    isSource: false,
    isTarget: true,
    demoSupported: false,
  },
  {
    code: 'hoc',
    name: 'Ho',
    nativeName: 'ᱦᱳ',
    script: 'Warang Chiti / Devanagari',
    isSource: false,
    isTarget: true,
    demoSupported: false,
  },
];

export const SOURCE_LANGUAGES = LANGUAGES.filter((l) => l.isSource);
export const TARGET_LANGUAGES = LANGUAGES.filter((l) => l.isTarget);

export function getLanguage(code: string): Language | undefined {
  return LANGUAGES.find((l) => l.code === code);
}

export function languageName(code: string): string {
  return getLanguage(code)?.name ?? code;
}
