import React, { useEffect, useRef } from 'react';
import { Animated, StyleSheet, Text } from 'react-native';
import { COLORS } from '../constants/colors';

interface Props {
  message: string | null;
  error?: boolean;
  onHide: () => void;
}

// A brief bottom banner used for shop / action confirmations.
function Toast({ message, error, onHide }: Props) {
  const anim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!message) return;
    anim.setValue(0);
    Animated.sequence([
      Animated.timing(anim, { toValue: 1, duration: 200, useNativeDriver: true }),
      Animated.delay(1300),
      Animated.timing(anim, { toValue: 0, duration: 250, useNativeDriver: true }),
    ]).start(() => onHide());
  }, [message, anim, onHide]);

  if (!message) return null;

  const translateY = anim.interpolate({ inputRange: [0, 1], outputRange: [30, 0] });

  return (
    <Animated.View
      pointerEvents="none"
      style={[
        styles.toast,
        { opacity: anim, transform: [{ translateY }] },
        error ? styles.error : styles.success,
      ]}
    >
      <Text style={styles.text}>{message}</Text>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  toast: {
    position: 'absolute',
    bottom: 24,
    alignSelf: 'center',
    paddingHorizontal: 22,
    paddingVertical: 12,
    borderRadius: 14,
    zIndex: 50,
    shadowColor: COLORS.shadow,
    shadowOpacity: 0.18,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 3 },
    elevation: 6,
  },
  success: { backgroundColor: COLORS.green },
  error: { backgroundColor: COLORS.primaryDark },
  text: { color: COLORS.white, fontWeight: '800', fontSize: 14 },
});

export default Toast;
