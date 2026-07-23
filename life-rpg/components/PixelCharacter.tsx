import React, { useEffect, useRef } from 'react';
import { Animated, Easing, StyleSheet, View } from 'react-native';

// Pixel-art runner: red shirt, dark pants, backpack straps and sneakers.
// Built from a small character grid so it stays crisp and dependency-free.
// 12 columns x 16 rows.
const GRID: string[] = [
  '....HHHH....',
  '...HHHHHH...',
  '..HHKKKKHH..',
  '..HKKKKKKH..',
  '..KKEKKEKK..',
  '..KKKKKKKK..',
  '...KKKKKK...',
  '..BRRRRRRB..',
  '.KRRRRRRRRK.',
  '.KRRRRRRRRK.',
  '..RRRRRRRR..',
  '..RRRRRRRR..',
  '..PPPPPPPP..',
  '..PPP..PPP..',
  '..PPP..PPP..',
  '..SSS..SSS..',
];

const PALETTE: Record<string, string | undefined> = {
  '.': undefined, // transparent
  H: '#3A2A1A', // hair
  K: '#E8B891', // skin
  E: '#2A2A2A', // eyes
  R: '#E23B3B', // red shirt
  B: '#8B5A2B', // backpack strap
  P: '#2C2C3A', // dark pants
  S: '#FFFFFF', // sneakers
};

interface Props {
  pixel?: number; // size of one pixel block
  running?: boolean; // animate a small running bob
}

function PixelCharacter({ pixel = 9, running = true }: Props) {
  const bob = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!running) {
      bob.stopAnimation();
      bob.setValue(0);
      return;
    }
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(bob, {
          toValue: 1,
          duration: 260,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
        Animated.timing(bob, {
          toValue: 0,
          duration: 260,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [running, bob]);

  const translateY = bob.interpolate({ inputRange: [0, 1], outputRange: [0, -pixel] });

  return (
    <Animated.View style={{ transform: [{ translateY }] }}>
      <View style={styles.grid} accessibilityLabel="Personaje pixel art">
        {GRID.map((row, y) => (
          <View key={y} style={styles.row}>
            {row.split('').map((cell, x) => {
              const color = PALETTE[cell];
              return (
                <View
                  key={x}
                  style={{
                    width: pixel,
                    height: pixel,
                    backgroundColor: color ?? 'transparent',
                  }}
                />
              );
            })}
          </View>
        ))}
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  grid: { flexDirection: 'column' },
  row: { flexDirection: 'row' },
});

export default React.memo(PixelCharacter);
