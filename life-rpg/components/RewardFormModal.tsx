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
import { Reward, RewardType } from '../types';
import { COLORS } from '../constants/colors';
import { REWARD_ICONS } from '../constants/icons';
import IconPicker from './IconPicker';

interface Props {
  visible: boolean;
  onClose: () => void;
  onSave: (reward: Omit<Reward, 'id'>) => void;
}

function toInt(text: string): number {
  const n = parseInt(text.replace(/[^0-9]/g, ''), 10);
  return Number.isFinite(n) ? n : 0;
}

// Create form for a custom shop reward.
function RewardFormModal({ visible, onClose, onSave }: Props) {
  const [name, setName] = useState('');
  const [icon, setIcon] = useState(REWARD_ICONS[0]);
  const [price, setPrice] = useState('50');
  const [type, setType] = useState<RewardType>('normal');
  const [lifeAmount, setLifeAmount] = useState('100');

  useEffect(() => {
    if (!visible) return;
    setName('');
    setIcon(REWARD_ICONS[0]);
    setPrice('50');
    setType('normal');
    setLifeAmount('100');
  }, [visible]);

  const canSave = name.trim().length > 0 && toInt(price) > 0;

  const handleSave = () => {
    if (!canSave) return;
    onSave({
      name: name.trim(),
      icon,
      price: toInt(price),
      type,
      lifeAmount: type === 'life' ? toInt(lifeAmount) : 0,
    });
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
          <Text style={styles.title}>Nueva recompensa</Text>
          <ScrollView showsVerticalScrollIndicator={false}>
            <Text style={styles.label}>Nombre</Text>
            <TextInput
              style={styles.input}
              value={name}
              onChangeText={setName}
              placeholder="Nombre de la recompensa"
              placeholderTextColor={COLORS.textMuted}
            />

            <Text style={styles.label}>Icono</Text>
            <IconPicker icons={REWARD_ICONS} selected={icon} onSelect={setIcon} />

            <Text style={styles.label}>Precio</Text>
            <TextInput
              style={styles.input}
              value={price}
              onChangeText={setPrice}
              keyboardType="number-pad"
            />

            <Text style={styles.label}>Tipo</Text>
            <View style={styles.segment}>
              <Pressable
                style={[styles.segmentBtn, type === 'normal' && styles.segmentActive]}
                onPress={() => setType('normal')}
              >
                <Text style={[styles.segmentText, type === 'normal' && styles.segmentTextActive]}>
                  Normal
                </Text>
              </Pressable>
              <Pressable
                style={[styles.segmentBtn, type === 'life' && styles.segmentActive]}
                onPress={() => setType('life')}
              >
                <Text style={[styles.segmentText, type === 'life' && styles.segmentTextActive]}>
                  Recuperar vida
                </Text>
              </Pressable>
            </View>

            {type === 'life' && (
              <>
                <Text style={styles.label}>Cantidad de vida</Text>
                <TextInput
                  style={styles.input}
                  value={lifeAmount}
                  onChangeText={setLifeAmount}
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
  segment: { flexDirection: 'row', backgroundColor: COLORS.background, borderRadius: 12, padding: 4 },
  segmentBtn: { flex: 1, paddingVertical: 10, borderRadius: 9, alignItems: 'center' },
  segmentActive: { backgroundColor: COLORS.primary },
  segmentText: { fontWeight: '800', color: COLORS.textMuted, fontSize: 14 },
  segmentTextActive: { color: COLORS.white },
  actions: { flexDirection: 'row', gap: 12, marginTop: 18 },
  actionBtn: { flex: 1, paddingVertical: 14, borderRadius: 14, alignItems: 'center' },
  cancelBtn: { backgroundColor: COLORS.background, borderWidth: 1, borderColor: COLORS.border },
  cancelText: { fontWeight: '800', color: COLORS.textDark, fontSize: 15 },
  saveBtn: { backgroundColor: COLORS.primary },
  saveDisabled: { backgroundColor: '#E7C3C3' },
  saveText: { fontWeight: '800', color: COLORS.white, fontSize: 15 },
});

export default RewardFormModal;
