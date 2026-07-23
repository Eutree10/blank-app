import React from 'react';
import { StyleSheet, View } from 'react-native';

// Simple monochrome pixel icons (7x7) for the bottom navigation.
export type IconName = 'home' | 'habits' | 'shop' | 'profile';

const PATTERNS: Record<IconName, string[]> = {
  home: [
    '...X...',
    '..XXX..',
    '.XXXXX.',
    'XXXXXXX',
    '.XXXXX.',
    '.X...X.',
    '.X.X.X.',
  ],
  habits: [
    '.......',
    '.....X.',
    '....XX.',
    'X...XX.',
    'XX.XX..',
    '.XXX...',
    '..X....',
  ],
  shop: [
    '.XX.XX.',
    '.X...X.',
    'XXXXXXX',
    'XXXXXXX',
    'XXXXXXX',
    'XXXXXXX',
    '.XXXXX.',
  ],
  profile: [
    '..XXX..',
    '..XXX..',
    '.......',
    '.XXXXX.',
    'XXXXXXX',
    'XXXXXXX',
    'XXXXXXX',
  ],
};

interface Props {
  name: IconName;
  color: string;
  pixel?: number;
}

function PixelIcon({ name, color, pixel = 3 }: Props) {
  const rows = PATTERNS[name];
  return (
    <View>
      {rows.map((row, y) => (
        <View key={y} style={styles.row}>
          {row.split('').map((cell, x) => (
            <View
              key={x}
              style={{
                width: pixel,
                height: pixel,
                backgroundColor: cell === 'X' ? color : 'transparent',
              }}
            />
          ))}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row' },
});

export default React.memo(PixelIcon);
