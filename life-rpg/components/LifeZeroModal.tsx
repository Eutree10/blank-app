import React from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';
import { COLORS } from '../constants/colors';
import PixelCharacter from './PixelCharacter';
import { PUNISHMENT_TEXT } from '../constants/game';

interface Props {
  visible: boolean;
  onConfirm: () => void;
}

// Mandatory modal shown when life reaches 0. The character is stopped.
function LifeZeroModal({ visible, onConfirm }: Props) {
  return (
    <Modal visible={visible} transparent animationType="fade">
      <View style={styles.overlay}>
        <View style={styles.card}>
          <View style={styles.charWrap}>
            <PixelCharacter pixel={8} running={false} />
          </View>
          <Text style={styles.title}>Te quedaste sin vida</Text>
          <Text style={styles.subtitle}>{PUNISHMENT_TEXT}</Text>
          <Pressable style={styles.btn} onPress={onConfirm}>
            <Text style={styles.btnText}>Castigo completado</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(40,0,0,0.72)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  card: {
    width: '100%',
    maxWidth: 340,
    backgroundColor: COLORS.card,
    borderRadius: 24,
    paddingVertical: 28,
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  charWrap: { height: 130, justifyContent: 'center', opacity: 0.6 },
  title: { fontSize: 22, fontWeight: '900', color: COLORS.primaryDark, marginTop: 8 },
  subtitle: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.textDark,
    textAlign: 'center',
    marginTop: 10,
    lineHeight: 21,
  },
  btn: {
    marginTop: 22,
    backgroundColor: COLORS.primaryDark,
    borderRadius: 14,
    paddingVertical: 12,
    paddingHorizontal: 32,
  },
  btnText: { color: COLORS.white, fontWeight: '800', fontSize: 16 },
});

export default LifeZeroModal;
