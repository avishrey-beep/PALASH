export { colors, palette, statusColors } from './colors';
export type { ColorToken, StatusKey } from './colors';
export { spacing, radius, borderWidth } from './spacing';
export type { SpacingToken, RadiusToken } from './spacing';
export { typography, fontWeights } from './typography';
export type { TypographyRole } from './typography';
export { shadowOffsets, hardShadowStyle } from './shadows';
export type { ShadowSize } from './shadows';

import { colors, palette, statusColors } from './colors';
import { spacing, radius, borderWidth } from './spacing';
import { typography } from './typography';
import { shadowOffsets } from './shadows';

/** Convenience bundle so screens can `import { theme } from '@/theme'`. */
export const theme = {
  colors,
  palette,
  statusColors,
  spacing,
  radius,
  borderWidth,
  typography,
  shadowOffsets,
} as const;
