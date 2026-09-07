import type { VerificationStatus } from '@/types';

/**
 * Offline demo translation dictionary: Hindi -> Santali (Ol Chiki).
 *
 * IMPORTANT (spec §2, §10, §61):
 *  - Every pair below is copied verbatim from the project's real seeded
 *    classroom phrase data (`data/seed/init_db.py`), which was human-verified
 *    at origin. Nothing here is machine-generated or fabricated.
 *  - This is a small DEMO dictionary. It is NOT a production translation model
 *    and must always be labelled as demo/local in the UI. We do not claim
 *    production-quality linguistic accuracy.
 *  - Ol Chiki text is the genuine Santali script. We make no claim about
 *    Ho/Mundari coverage here -- those languages have no demo pairs yet, and
 *    the provider returns UNAVAILABLE for them rather than inventing text.
 */
export interface DemoPhrase {
  hindi: string;
  targetText: string; // Ol Chiki
  pronunciation: string; // romanised guide
  script: string;
  targetLang: string; // ISO 639-3
  domain: string;
  subject: string;
  verification: VerificationStatus;
}

export const SANTALI_DEMO_PHRASES: DemoPhrase[] = [
  // --- Classroom management & instructions ---
  { hindi: 'बैठ जाओ', targetText: 'ᱫᱩᱲᱩᱵ ᱢᱮ', pronunciation: "duṛup' me", script: 'Ol Chiki', targetLang: 'sat', domain: 'classroom', subject: 'General', verification: 'human_verified' },
  { hindi: 'खड़े हो जाओ', targetText: 'ᱛᱤᱸᱜᱩᱱ ᱢᱮ', pronunciation: 'tĩgun me', script: 'Ol Chiki', targetLang: 'sat', domain: 'classroom', subject: 'General', verification: 'human_verified' },
  { hindi: 'अपनी किताब खोलो', targetText: 'ᱯᱚᱛᱚᱵ ᱡᱷᱤᱡᱽ ᱢᱮ', pronunciation: 'potob jhij me', script: 'Ol Chiki', targetLang: 'sat', domain: 'classroom', subject: 'General', verification: 'human_verified' },
  { hindi: 'ध्यान से सुनो', targetText: 'ᱫᱷᱮᱭᱟᱱ ᱛᱮ ᱟᱧᱡᱚᱢ ᱢᱮ', pronunciation: 'dhiyan te añjom me', script: 'Ol Chiki', targetLang: 'sat', domain: 'classroom', subject: 'General', verification: 'human_verified' },
  { hindi: 'अपनी कॉपी में लिखो', targetText: 'ᱟᱢᱟᱜ ᱠᱷᱟᱛᱟ ᱨᱮ ᱚᱞ ᱢᱮ', pronunciation: 'amag khata re ol me', script: 'Ol Chiki', targetLang: 'sat', domain: 'classroom', subject: 'Instruction', verification: 'human_verified' },
  { hindi: 'यहाँ देखो', targetText: 'ᱱᱚᱸᱰᱮ ᱧᱮᱞ ᱢᱮ', pronunciation: 'nõṇḍe ñel me', script: 'Ol Chiki', targetLang: 'sat', domain: 'classroom', subject: 'Instruction', verification: 'human_verified' },
  { hindi: 'श्यामपट्ट पर देखो', targetText: 'ᱵᱽᱞᱮᱠᱵᱳᱨᱰ ᱨᱮ ᱧᱮᱞ ᱢᱮ', pronunciation: 'blackboard re ñel me', script: 'Ol Chiki', targetLang: 'sat', domain: 'classroom', subject: 'Instruction', verification: 'human_verified' },
  { hindi: 'मेरे बाद दोहराओ', targetText: 'ᱤᱧ ᱛᱟᱭᱚᱢ ᱛᱮ ᱨᱚᱲ ᱢᱮ', pronunciation: 'iñ tayom te roṛ me', script: 'Ol Chiki', targetLang: 'sat', domain: 'classroom', subject: 'Instruction', verification: 'human_verified' },
  { hindi: 'हाथ ऊपर करो', targetText: 'ᱛᱤ ᱛᱩᱞ ᱢᱮ', pronunciation: 'ti tul me', script: 'Ol Chiki', targetLang: 'sat', domain: 'classroom', subject: 'Activity', verification: 'human_verified' },
  { hindi: 'क्या तुमने समझ लिया?', targetText: 'ᱪᱮᱫ ᱟᱢ ᱵᱩᱡᱷᱟᱹᱣ ᱠᱮᱫ-ᱟ?', pronunciation: "chet' am bujhəw ket'-a?", script: 'Ol Chiki', targetLang: 'sat', domain: 'classroom', subject: 'Check', verification: 'human_verified' },

  // --- Praise ---
  { hindi: 'बहुत अच्छा', targetText: 'ᱟᱹᱰᱤ ᱵᱷᱟᱹᱜᱤ', pronunciation: 'aḍi bhagi', script: 'Ol Chiki', targetLang: 'sat', domain: 'classroom', subject: 'Praise', verification: 'human_verified' },
  { hindi: 'शाबाश बच्चों', targetText: 'ᱥᱟᱨᱦᱟᱣ ᱜᱤᱫᱽᱨᱟᱹ ᱠᱚ', pronunciation: 'sarhaw gidrə ko', script: 'Ol Chiki', targetLang: 'sat', domain: 'classroom', subject: 'Praise', verification: 'human_verified' },

  // --- Mathematics prompts ---
  { hindi: 'गिनो और बताओ', targetText: 'ᱞᱮᱠᱷᱟᱭ ᱢᱮ ᱟᱨ ᱞᱟᱹᱭ ᱢᱮ', pronunciation: 'lekhai me ar ləy me', script: 'Ol Chiki', targetLang: 'sat', domain: 'numeracy', subject: 'Mathematics', verification: 'human_verified' },
  { hindi: 'कितने आम हैं?', targetText: 'ᱛᱤᱱᱟᱹᱜ ᱩᱞ ᱢᱮᱱᱟᱜ-ᱟ?', pronunciation: 'tinəg ul menag-a?', script: 'Ol Chiki', targetLang: 'sat', domain: 'numeracy', subject: 'Mathematics', verification: 'human_verified' },
  { hindi: 'तीन और दो मिलाकर कितने होते हैं?', targetText: 'ᱯᱮ ᱟᱨ ᱵᱟᱨ ᱢᱮᱥᱟ ᱠᱟᱛᱮ ᱛᱤᱱᱟᱹᱜ ᱦᱩᱭᱩᱜ-ᱟ?', pronunciation: 'pe ar bar mesa kate tinəg huyug-a?', script: 'Ol Chiki', targetLang: 'sat', domain: 'numeracy', subject: 'Mathematics', verification: 'human_verified' },

  // --- Numbers 1-10 ---
  { hindi: 'एक', targetText: 'ᱢᱤᱫ', pronunciation: "mit'", script: 'Ol Chiki', targetLang: 'sat', domain: 'numeracy', subject: 'Mathematics', verification: 'human_verified' },
  { hindi: 'दो', targetText: 'ᱵᱟᱨ', pronunciation: 'bar', script: 'Ol Chiki', targetLang: 'sat', domain: 'numeracy', subject: 'Mathematics', verification: 'human_verified' },
  { hindi: 'तीन', targetText: 'ᱯᱮ', pronunciation: 'pe', script: 'Ol Chiki', targetLang: 'sat', domain: 'numeracy', subject: 'Mathematics', verification: 'human_verified' },
  { hindi: 'चार', targetText: 'ᱯᱳᱱ', pronunciation: 'pon', script: 'Ol Chiki', targetLang: 'sat', domain: 'numeracy', subject: 'Mathematics', verification: 'human_verified' },
  { hindi: 'पाँच', targetText: 'ᱢᱚᱬᱮ', pronunciation: 'mõṛẽ', script: 'Ol Chiki', targetLang: 'sat', domain: 'numeracy', subject: 'Mathematics', verification: 'human_verified' },
  { hindi: 'छह', targetText: 'ᱛᱩᱨᱩᱭ', pronunciation: 'turui', script: 'Ol Chiki', targetLang: 'sat', domain: 'numeracy', subject: 'Mathematics', verification: 'human_verified' },
  { hindi: 'सात', targetText: 'ᱮᱭᱟᱭ', pronunciation: 'eyae', script: 'Ol Chiki', targetLang: 'sat', domain: 'numeracy', subject: 'Mathematics', verification: 'human_verified' },
  { hindi: 'आठ', targetText: 'ᱤᱨᱟᱹᱞ', pronunciation: 'irəl', script: 'Ol Chiki', targetLang: 'sat', domain: 'numeracy', subject: 'Mathematics', verification: 'human_verified' },
  { hindi: 'नौ', targetText: 'ᱟᱨᱮ', pronunciation: 'are', script: 'Ol Chiki', targetLang: 'sat', domain: 'numeracy', subject: 'Mathematics', verification: 'human_verified' },
  { hindi: 'दस', targetText: 'ᱜᱮᱞ', pronunciation: 'gel', script: 'Ol Chiki', targetLang: 'sat', domain: 'numeracy', subject: 'Mathematics', verification: 'human_verified' },
];

/** Normalise a Hindi phrase for lookup (trim, collapse spaces, drop trailing ?/।). */
export function normalizePhrase(text: string): string {
  return text
    .trim()
    .replace(/\s+/g, ' ')
    .replace(/[?।.!]+$/u, '')
    .toLowerCase();
}
