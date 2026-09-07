/**
 * Spacing, radius and border-width scales.
 *
 * Neo-brutalism favours generous, consistent spacing and chunky borders, so
 * the border scale intentionally starts thick (2px) and radii stay small --
 * hard rectangles, not soft pills.
 */

export const spacing = {
  none: 0,
  xxs: 2,
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
  huge: 48,
} as const;

export const radius = {
  none: 0,
  sm: 6,
  md: 10,
  lg: 14,
  xl: 20,
  pill: 999,
} as const;

export const borderWidth = {
  hairline: 1,
  thin: 2,
  base: 3,
  thick: 4,
} as const;

export type SpacingToken = keyof typeof spacing;
export type RadiusToken = keyof typeof radius;
