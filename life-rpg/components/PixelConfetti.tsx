import React, { useEffect, useRef } from 'react';
import { Animated, Easing, StyleSheet, View } from 'react-native';
import { COLORS } from '../constants/colors';

const PIECE_COLORS = [COLORS.primary, COLORS.gold, COLORS.green, COLORS.primaryDark, '#4A90D9'];

interface PieceProps {
  index: number;
  active: boolean;
}

// Deterministic pseudo-random from an index (no Math.random needed at render).
function seeded(i: number, salt: number): number {
  const x = Math.sin(i * 12.9898 + salt * 78.233) * 43758.5453;
  return x - Math.floor(x);
}

function Piece({ index, active }: PieceProps) {
  const fall = useRef(new Animated.Value(0)).current;
  const startX = seeded(index, 1) * 260 - 130;
  const drift = seeded(index, 2) * 60 - 30;
  const size = 6 + Math.floor(seeded(index, 3) * 5);
  const color = PIECE_COLORS[index % PIECE_COLORS.length];
  const delay = Math.floor(seeded(index, 4) * 300);

  useEffect(() => {
    if (!active) return;
    fall.setValue(0);
    Animated.timing(fall, {
      toValue: 1,
      duration: 1400,
      delay,
      easing: Easing.out(Easing.quad),
      useNativeDriver: true,
    }).start();
  }, [active, fall, delay]);

  const translateY = fall.interpolate({ inputRange: [0, 1], outputRange: [-40, 220] });
  const translateX = fall.interpolate({ inputRange: [0, 1], outputRange: [startX, startX + drift] });
  const opacity = fall.interpolate({ inputRange: [0, 0.8, 1], outputRange: [1, 1, 0] });
  const rotate = fall.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '220deg'] });

  return (
    <Animated.View
      pointerEvents="none"
      style={[
        styles.piece,
        {
          width: size,
          height: size,
          backgroundColor: color,
          opacity,
          transform: [{ translateX }, { translateY }, { rotate }],
        },
      ]}
    />
  );
}

// A burst of falling pixel squares used for level-up celebration.
function PixelConfetti({ active, count = 24 }: { active: boolean; count?: number }) {
  return (
    <View pointerEvents="none" style={styles.container}>
      {Array.from({ length: count }).map((_, i) => (
        <Piece key={i} index={i} active={active} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: 'center',
    justifyContent: 'flex-start',
  },
  piece: { position: 'absolute', top: 0, borderRadius: 1 },
});

export default PixelConfetti;
