import { TextStyle } from 'react-native';

/**
 * Typography roles for PALASH.
 *
 * Bold, chunky headings for the neo-brutalist look; comfortable body sizes for
 * teachers reading in Hindi and target-language scripts (which can be tall, so
 * line-heights are a little generous). We rely on the platform system font --
 * no custom font files are bundled, so nothing is claimed that isn't shipped.
 */

const weights = {
  regular: '400',
  medium: '600',
  bold: '700',
  heavy: '800',
  black: '900',
} as const;

type Role =
  | 'display'
  | 'h1'
  | 'h2'
  | 'h3'
  | 'title'
  | 'subtitle'
  | 'body'
  | 'bodyStrong'
  | 'bodySmall'
  | 'label'
  | 'caption'
  | 'button'
  | 'script';

export const typography: Record<Role, TextStyle> = {
  display: { fontSize: 40, fontWeight: weights.black, lineHeight: 46, letterSpacing: -0.5 },
  h1: { fontSize: 30, fontWeight: weights.black, lineHeight: 36, letterSpacing: -0.3 },
  h2: { fontSize: 24, fontWeight: weights.heavy, lineHeight: 30, letterSpacing: -0.2 },
  h3: { fontSize: 20, fontWeight: weights.heavy, lineHeight: 26 },
  title: { fontSize: 18, fontWeight: weights.bold, lineHeight: 24 },
  subtitle: { fontSize: 16, fontWeight: weights.bold, lineHeight: 22 },
  body: { fontSize: 16, fontWeight: weights.regular, lineHeight: 24 },
  bodyStrong: { fontSize: 16, fontWeight: weights.medium, lineHeight: 24 },
  bodySmall: { fontSize: 14, fontWeight: weights.regular, lineHeight: 20 },
  label: { fontSize: 13, fontWeight: weights.heavy, lineHeight: 16, letterSpacing: 0.6 },
  caption: { fontSize: 12, fontWeight: weights.medium, lineHeight: 16 },
  button: { fontSize: 16, fontWeight: weights.heavy, lineHeight: 20, letterSpacing: 0.3 },
  // For target-language scripts (Ol Chiki etc.) and romanised pronunciation --
  // slightly larger with extra line-height so tall glyphs are not clipped.
  script: { fontSize: 22, fontWeight: weights.bold, lineHeight: 34 },
};

export { weights as fontWeights };
export type TypographyRole = Role;
