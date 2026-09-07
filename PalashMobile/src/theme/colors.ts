/**
 * PALASH color system.
 *
 * These are the exact palette values from the product spec (terracotta,
 * mustard/ochre, forest, cream, sand, dark brown). Nothing here encodes any
 * cultural or tribal claim -- they are UI colors chosen for an earthy,
 * high-contrast neo-brutalist look. A few derived tokens (muted text, a
 * distinct danger red) are added purely for interface legibility and are
 * marked as derived.
 */

export const palette = {
  terracotta: '#8C3A2B',
  terracottaDeep: '#6E2C20',
  mustard: '#D97706',
  forest: '#2E6F57',
  forestDeep: '#235644',
  cream: '#F7F3E9',
  sand: '#E9D8A6',
  brownDark: '#2A2A2A',
  white: '#FFFFFF',

  // --- derived UI-only tokens (not part of the core brand palette) ---
  ink: '#2A2A2A', // borders + hard shadows + primary text (same as brownDark)
  inkSoft: '#6B5D4F', // muted warm brown-grey for secondary text
  sandDeep: '#DBC17F', // pressed/hover state for sand surfaces
  creamDeep: '#EFE7D2', // subtle alternating rows on cream
  danger: '#B23A2E', // error red, kept warm to sit beside terracotta
  dangerDeep: '#8F2C22',
} as const;

export const colors = {
  // surfaces
  background: palette.cream,
  surface: palette.white,
  surfaceAlt: palette.sand,
  surfaceMuted: palette.creamDeep,
  white: palette.white,

  // structure
  border: palette.ink,
  shadow: palette.ink,

  // brand actions
  primary: palette.terracotta,
  primaryDark: palette.terracottaDeep,
  accent: palette.mustard,
  success: palette.forest,
  successDark: palette.forestDeep,
  danger: palette.danger,
  dangerDark: palette.dangerDeep,

  // text
  text: palette.brownDark,
  textMuted: palette.inkSoft,
  textOnPrimary: palette.white,
  textOnAccent: palette.brownDark,
  textOnSuccess: palette.white,

  // pressed states
  primaryPressed: palette.terracottaDeep,
  accentPressed: '#B45F04',
  successPressed: palette.forestDeep,
  surfaceAltPressed: palette.sandDeep,
} as const;

/** Semantic colors for translation / status states used across the app. */
export const statusColors = {
  neutral: { bg: palette.sand, fg: palette.brownDark },
  processing: { bg: palette.mustard, fg: palette.brownDark },
  success: { bg: palette.forest, fg: palette.white },
  cached: { bg: palette.forestDeep, fg: palette.white },
  unavailable: { bg: palette.mustard, fg: palette.brownDark },
  error: { bg: palette.danger, fg: palette.white },
  offline: { bg: palette.brownDark, fg: palette.white },
  online: { bg: palette.forest, fg: palette.white },
} as const;

export type ColorToken = keyof typeof colors;
export type StatusKey = keyof typeof statusColors;
