import React from 'react';
import { View, type StyleProp, type ViewStyle } from 'react-native';
import { colors } from '@/theme';

/**
 * Simple, generic geometric motifs (dots, diamonds, triangles) built from
 * Views. These are ordinary shapes for an earthy, folk-inspired feel -- they
 * are NOT tribal symbols or scripts, and make no cultural claim (spec: do not
 * fabricate tribal symbols/scripts).
 */

type Shape = 'dot' | 'diamond' | 'triangle';

function Dot({ size, color }: { size: number; color: string }) {
  return <View style={{ width: size, height: size, borderRadius: size / 2, backgroundColor: color }} />;
}

function Diamond({ size, color }: { size: number; color: string }) {
  return <View style={{ width: size, height: size, backgroundColor: color, transform: [{ rotate: '45deg' }] }} />;
}

function Triangle({ size, color }: { size: number; color: string }) {
  return (
    <View
      style={{
        width: 0,
        height: 0,
        borderLeftWidth: size / 2,
        borderRightWidth: size / 2,
        borderBottomWidth: size,
        borderLeftColor: 'transparent',
        borderRightColor: 'transparent',
        borderBottomColor: color,
      }}
    />
  );
}

interface MotifRowProps {
  shape?: Shape;
  count?: number;
  size?: number;
  color?: string;
  style?: StyleProp<ViewStyle>;
}

/** A single row of evenly spaced motif shapes -- a decorative band. */
export function MotifRow({
  shape = 'diamond',
  count = 8,
  size = 10,
  color = colors.primary,
  style,
}: MotifRowProps) {
  const Item = shape === 'dot' ? Dot : shape === 'triangle' ? Triangle : Diamond;
  return (
    <View
      style={[{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }, style]}
      pointerEvents="none"
    >
      {Array.from({ length: count }).map((_, i) => (
        <Item key={i} size={size} color={color} />
      ))}
    </View>
  );
}

export { Dot, Diamond, Triangle };
