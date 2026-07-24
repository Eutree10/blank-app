import React, { useRef, useState } from 'react';
import { Animated, Pressable, StyleSheet, Text, View } from 'react-native';
import { Habit } from '../types';
import { COLORS } from '../constants/colors';
import FloatingText from './FloatingText';

interface FloatMsg {
  id: number;
  text: string;
  color: string;
}

interface Props {
  habit: Habit;
  completed: boolean;
  onComplete: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

let floatCounter = 0;

function HabitCard({ habit, completed, onComplete, onEdit, onDelete }: Props) {
  const [showOptions, setShowOptions] = useState(false);
  const [floats, setFloats] = useState<FloatMsg[]>([]);
  const anim = useRef(new Animated.Value(0)).current;
  const isGood = habit.type === 'good';

  const pushFloat = (text: string, color: string) => {
    floatCounter += 1;
    setFloats((f) => [...f, { id: floatCounter, text, color }]);
  };

  const removeFloat = (id: number) => setFloats((f) => f.filter((m) => m.id !== id));

  const handlePress = () => {
    if (completed) return;
    onComplete();

    if (isGood) {
      pushFloat(`+${habit.xp} XP`, COLORS.gold);
      if (habit.coins > 0) {
        setTimeout(() => pushFloat(`+${habit.coins} monedas`, COLORS.green), 120);
      }
      // small positive bounce
      Animated.sequence([
        Animated.timing(anim, { toValue: 1, duration: 120, useNativeDriver: true }),
        Animated.spring(anim, { toValue: 0, useNativeDriver: true }),
      ]).start();
    } else {
      pushFloat(`-${habit.lifePenalty} de vida`, COLORS.primaryDark);
      // damage shake
      Animated.sequence([
        Animated.timing(anim, { toValue: -1, duration: 60, useNativeDriver: true }),
        Animated.timing(anim, { toValue: 1, duration: 60, useNativeDriver: true }),
        Animated.timing(anim, { toValue: -1, duration: 60, useNativeDriver: true }),
        Animated.timing(anim, { toValue: 0, duration: 60, useNativeDriver: true }),
      ]).start();
    }
  };

  const translateX = anim.interpolate({ inputRange: [-1, 0, 1], outputRange: [-6, 0, 6] });
  const rewardText = isGood
    ? `+${habit.xp} XP · +${habit.coins} monedas`
    : `-${habit.lifePenalty} de vida`;

  return (
    <Animated.View style={[styles.card, { transform: [{ translateX }] }]}>
      {floats.map((m) => (
        <FloatingText key={m.id} text={m.text} color={m.color} onDone={() => removeFloat(m.id)} />
      ))}

      <View style={[styles.iconBox, isGood ? styles.iconGood : styles.iconBad]}>
        <Text style={styles.icon}>{habit.icon}</Text>
      </View>

      <Pressable
        style={styles.info}
        onLongPress={() => setShowOptions((s) => !s)}
        delayLongPress={300}
      >
        <Text style={styles.name} numberOfLines={1}>
          {habit.name}
        </Text>
        <Text style={[styles.reward, { color: isGood ? COLORS.green : COLORS.primaryDark }]}>
          {rewardText}
        </Text>
      </Pressable>

      <Pressable
        onPress={() => setShowOptions((s) => !s)}
        hitSlop={8}
        style={styles.optionsBtn}
        accessibilityLabel="Opciones del hábito"
      >
        <Text style={styles.optionsDots}>⋯</Text>
      </Pressable>

      <Pressable
        onPress={handlePress}
        disabled={completed}
        style={[
          styles.markBtn,
          completed ? styles.markDone : isGood ? styles.markGood : styles.markBad,
        ]}
      >
        <Text style={styles.markText}>{completed ? 'Completado' : isGood ? 'Marcar' : 'Registrar'}</Text>
      </Pressable>

      {showOptions && (
        <View style={styles.optionsMenu}>
          <Pressable
            style={styles.optionItem}
            onPress={() => {
              setShowOptions(false);
              onEdit();
            }}
          >
            <Text style={styles.optionText}>Editar</Text>
          </Pressable>
          <View style={styles.optionDivider} />
          <Pressable
            style={styles.optionItem}
            onPress={() => {
              setShowOptions(false);
              onDelete();
            }}
          >
            <Text style={[styles.optionText, { color: COLORS.primary }]}>Eliminar</Text>
          </Pressable>
        </View>
      )}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    shadowColor: COLORS.shadow,
    shadowOpacity: 0.05,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  iconBox: {
    width: 46,
    height: 46,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  iconGood: { backgroundColor: '#EAF6EC' },
  iconBad: { backgroundColor: '#FBE9E9' },
  icon: { fontSize: 24 },
  info: { flex: 1, paddingRight: 6 },
  name: { fontSize: 15, fontWeight: '700', color: COLORS.textDark },
  reward: { fontSize: 13, fontWeight: '600', marginTop: 2 },
  optionsBtn: { paddingHorizontal: 6, paddingVertical: 2, marginRight: 2 },
  optionsDots: { fontSize: 20, color: COLORS.textMuted, fontWeight: '800' },
  markBtn: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 12,
    minWidth: 96,
    alignItems: 'center',
  },
  markGood: { backgroundColor: COLORS.green },
  markBad: { backgroundColor: COLORS.primaryDark },
  markDone: { backgroundColor: COLORS.border },
  markText: { color: COLORS.white, fontWeight: '800', fontSize: 13 },
  optionsMenu: {
    position: 'absolute',
    top: 44,
    right: 12,
    backgroundColor: COLORS.card,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    shadowColor: COLORS.shadow,
    shadowOpacity: 0.12,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 3 },
    elevation: 5,
    zIndex: 30,
    minWidth: 120,
  },
  optionItem: { paddingVertical: 12, paddingHorizontal: 16 },
  optionText: { fontSize: 14, fontWeight: '700', color: COLORS.textDark },
  optionDivider: { height: 1, backgroundColor: COLORS.border },
});

export default React.memo(HabitCard);
