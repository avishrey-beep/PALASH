import React from 'react';
import { View, type ViewStyle, type StyleProp } from 'react-native';
import { colors, radius as radiusScale, borderWidth as bw, shadowOffsets, type ShadowSize } from '@/theme';

interface NeoSurfaceProps {
  children: React.ReactNode;
  /** Hard offset shadow size. */
  shadowSize?: ShadowSize;
  shadowColor?: string;
  backgroundColor?: string;
  borderColor?: string;
  borderWidth?: number;
  radius?: number;
  /** When true, content presses into the shadow (tactile button feel). */
  pressed?: boolean;
  style?: StyleProp<ViewStyle>;
  contentStyle?: StyleProp<ViewStyle>;
}

/**
 * The core neo-brutalist surface: a solid ink rectangle offset behind bordered
 * content. This renders a genuine HARD (non-blurred) shadow identically on iOS,
 * Android and web -- RN's native shadow/elevation props cannot do that (see
 * theme/shadows.ts). When `pressed`, the content shifts onto the shadow so
 * buttons feel physically depressed.
 */
export function NeoSurface({
  children,
  shadowSize = 'md',
  shadowColor = colors.shadow,
  backgroundColor = colors.surface,
  borderColor = colors.border,
  borderWidth = bw.base,
  radius = radiusScale.md,
  pressed = false,
  style,
  contentStyle,
}: NeoSurfaceProps) {
  const { x, y } = shadowOffsets[shadowSize];

  return (
    <View style={[{ paddingRight: x, paddingBottom: y }, style]}>
      {/* offset shadow layer */}
      <View
        style={{
          position: 'absolute',
          top: y,
          left: x,
          right: 0,
          bottom: 0,
          backgroundColor: shadowColor,
          borderRadius: radius,
          opacity: pressed ? 0 : 1,
        }}
      />
      {/* content layer */}
      <View
        style={[
          {
            backgroundColor,
            borderColor,
            borderWidth,
            borderRadius: radius,
            transform: pressed ? [{ translateX: x }, { translateY: y }] : undefined,
          },
          contentStyle,
        ]}
      >
        {children}
      </View>
    </View>
  );
}
