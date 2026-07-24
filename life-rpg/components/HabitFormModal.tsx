import React, { useEffect, useState } from 'react';
import {
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { Habit, HabitType } from '../types';
import { COLORS } from '../constants/colors';
import { HABIT_ICONS } from '../constants/icons';
import IconPicker from './IconPicker';

interface Props {
  visible: boolean;
  initial: Habit | null; // null = create new
  onClose: () => void;
  onSave: (habit: Habit | Omit<Habit, 'id'>) => void;
}

function toInt(text: string): number {
  const n = parseInt(text.replace(/[^0-9]/g, ''), 10);
  return Number.isFinite(n) ? n : 0;
}

// Create/edit form for a single habit.
function HabitFormModal({ visible, initial, onClose, onSave }: Props) {
  const [name, setName] = useState('');
  const [type, setType] = useState<HabitType>('good');
  const [icon, setIcon] = useState(HABIT_ICONS[0]);
  const [xp, setXp] = useState('10');
  const [coins, setCoins] = useState('5');
  const [life, setLife] = useState('50');

  useEffect(() => {
    if (!visible) return;
    if (initial) {
      setName(initial.name);
      setType(initial.type);
      setIcon(initial.icon);
      setXp(String(initial.xp));
      setCoins(String(initial.coins));
      setLife(String(initial.lifePenalty));
    } else {
      setName('');
      setType('good');
      setIcon(HABIT_ICONS[0]);
      setXp('10');
      setCoins('5');
      setLife('50');
    }
  }, [visible, initial]);

  const canSave = name.trim().length > 0;

  const handleSave = () => {
    if (!canSave) return;
    const isGood = type === 'good';
    const base = {
      name: name.trim(),
      type,
      icon,
      xp: isGood ? toInt(xp) : 0,
      coins: isGood ? toInt(coins) : 0,
      lifePenalty: isGood ? 0 : toInt(life),
    };
    if (initial) {
      onSave({ ...base, id: initial.id });
    } else {
      onSave(base);
    }
    onClose();
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.overlay}
      >
        <View style={styles.sheet}>
          <View style={styles.handle} />
          <Text style={styles.title}>{initial ? 'Editar hábito' : 'Nuevo hábito'}</Text>
          <ScrollView showsVerticalScrollIndicator={false}>
            <Text style={styles.label}>Nombre</Text>
            <TextInput
              style={styles.input}
              value={name}
              onChangeText={setName}
              placeholder="Nombre del hábito"
              placeholderTextColor={COLORS.textMuted}
            />

            <Text style={styles.label}>Tipo</Text>
            <View style={styles.segment}>
              <Pressable
                style={[styles.segmentBtn, type === 'good' && styles.segmentGood]}
                onPress={() => setType('good')}
              >
                <Text style={[styles.segmentText, type === 'good' && styles.segmentTextActive]}>
                  Bueno
                </Text>
              </Pressable>
              <Pressable
                style={[styles.segmentBtn, type === 'bad' && styles.segmentBad]}
                onPress={() => setType('bad')}
              >
                <Text style={[styles.segmentText, type === 'bad' && styles.segmentTextActive]}>
                  Malo
                </Text>
              </Pressable>
            </View>

            <Text style={styles.label}>Icono</Text>
            <IconPicker icons={HABIT_ICONS} selected={icon} onSelect={setIcon} />

            {type === 'good' ? (
              <View style={styles.row}>
                <View style={styles.rowItem}>
                  <Text style={styles.label}>XP</Text>
                  <TextInput
                    style={styles.input}
                    value={xp}
                    onChangeText={setXp}
                    keyboardType="number-pad"
                  />
                </View>
                <View style={styles.rowItem}>
                  <Text style={styles.label}>Monedas</Text>
                  <TextInput
                    style={styles.input}
                    value={coins}
                    onChangeText={setCoins}
                    keyboardType="number-pad"
                  />
                </View>
              </View>
            ) : (
              <>
                <Text style={styles.label}>Vida perdida</Text>
                <TextInput
                  style={styles.input}
                  value={life}
                  onChangeText={setLife}
                  keyboardType="number-pad"
                />
              </>
            )}
          </ScrollView>

          <View style={styles.actions}>
            <Pressable style={[styles.actionBtn, styles.cancelBtn]} onPress={onClose}>
              <Text style={styles.cancelText}>Cancelar</Text>
            </Pressable>
            <Pressable
              style={[styles.actionBtn, styles.saveBtn, !canSave && styles.saveDisabled]}
              onPress={handleSave}
              disabled={!canSave}
            >
              <Text style={styles.saveText}>Guardar</Text>
            </Pressable>
          </View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: COLORS.overlay, justifyContent: 'flex-end' },
  sheet: {
    backgroundColor: COLORS.card,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 24,
    maxHeight: '90%',
  },
  handle: {
    width: 44,
    height: 5,
    borderRadius: 3,
    backgroundColor: COLORS.border,
    alignSelf: 'center',
    marginBottom: 10,
  },
  title: { fontSize: 20, fontWeight: '900', color: COLORS.textDark, marginBottom: 8 },
  label: { fontSize: 13, fontWeight: '700', color: COLORS.textMuted, marginTop: 14, marginBottom: 6 },
  input: {
    backgroundColor: COLORS.background,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    color: COLORS.textDark,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  segment: {
    flexDirection: 'row',
    backgroundColor: COLORS.background,
    borderRadius: 12,
    padding: 4,
  },
  segmentBtn: { flex: 1, paddingVertical: 10, borderRadius: 9, alignItems: 'center' },
  segmentGood: { backgroundColor: COLORS.green },
  segmentBad: { backgroundColor: COLORS.primaryDark },
  segmentText: { fontWeight: '800', color: COLORS.textMuted, fontSize: 14 },
  segmentTextActive: { color: COLORS.white },
  row: { flexDirection: 'row', gap: 12 },
  rowItem: { flex: 1 },
  actions: { flexDirection: 'row', gap: 12, marginTop: 18 },
  actionBtn: { flex: 1, paddingVertical: 14, borderRadius: 14, alignItems: 'center' },
  cancelBtn: { backgroundColor: COLORS.background, borderWidth: 1, borderColor: COLORS.border },
  cancelText: { fontWeight: '800', color: COLORS.textDark, fontSize: 15 },
  saveBtn: { backgroundColor: COLORS.primary },
  saveDisabled: { backgroundColor: '#E7C3C3' },
  saveText: { fontWeight: '800', color: COLORS.white, fontSize: 15 },
});

export default HabitFormModal;
