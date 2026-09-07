import { Platform, ViewStyle } from 'react-native';

/**
 * Neo-brutalist "hard" offset shadows.
 *
 * A real hard shadow (solid, non-blurred, offset) cannot be produced portably
 * with RN's `shadow*` props (iOS/web only) or `elevation` (Android, always
 * blurred). The reliable cross-platform technique is to render a solid ink
 * rectangle offset behind the content -- see the `NeoSurface` component, which
 * consumes these offsets. The `hardShadow*` helpers below are an optional
 * iOS/web-only convenience for cases where an extra view is undesirable.
 */

export const shadowOffsets = {
  sm: { x: 2, y: 2 },
  md: { x: 4, y: 4 },
  lg: { x: 5, y: 5 },
  xl: { x: 7, y: 7 },
} as const;

export type ShadowSize = keyof typeof shadowOffsets;

/**
 * iOS/web-only hard shadow (no blur). Returns an empty object on Android where
 * these props are ignored; use `NeoSurface` there instead.
 */
export function hardShadowStyle(size: ShadowSize = 'md', color = '#2A2A2A'): ViewStyle {
  if (Platform.OS === 'android') return {};
  const { x, y } = shadowOffsets[size];
  return {
    shadowColor: color,
    shadowOffset: { width: x, height: y },
    shadowOpacity: 1,
    shadowRadius: 0,
  };
}
