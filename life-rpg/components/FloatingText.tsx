import React, { useEffect, useRef } from 'react';
import { Animated, StyleSheet, Text } from 'react-native';

interface Props {
  text: string;
  color: string;
  onDone: () => void;
}

// A small "+10 XP" style message that rises and fades, then removes itself.
function FloatingText({ text, color, onDone }: Props) {
  const anim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(anim, {
      toValue: 1,
      duration: 900,
      useNativeDriver: true,
    }).start(() => onDone());
  }, [anim, onDone]);

  const translateY = anim.interpolate({ inputRange: [0, 1], outputRange: [0, -40] });
  const opacity = anim.interpolate({ inputRange: [0, 0.2, 1], outputRange: [0, 1, 0] });

  return (
    <Animated.View
      pointerEvents="none"
      style={[styles.wrap, { opacity, transform: [{ translateY }] }]}
    >
      <Text style={[styles.text, { color }]}>{text}</Text>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    position: 'absolute',
    top: -6,
    right: 12,
    zIndex: 20,
  },
  text: { fontSize: 15, fontWeight: '800' },
});

export default FloatingText;
