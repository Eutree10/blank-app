import React from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';
import { COLORS } from '../constants/colors';
import PixelCharacter from './PixelCharacter';
import PixelConfetti from './PixelConfetti';
import { rankForLevel } from '../utils/level';
import { MAX_LEVEL } from '../constants/game';

interface Props {
  visible: boolean;
  level: number;
  onClose: () => void;
}

// Celebration shown when the player gains one or more levels.
function LevelUpModal({ visible, level, onClose }: Props) {
  const atMax = level >= MAX_LEVEL;
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <PixelConfetti active={visible} />
          <Text style={styles.title}>¡Subiste de nivel!</Text>
          <View style={styles.charWrap}>
            <PixelCharacter pixel={8} running />
          </View>
          <Text style={styles.level}>Nivel {level}</Text>
          <Text style={styles.rank}>{rankForLevel(level)}</Text>
          {atMax && <Text style={styles.maxNote}>¡Alcanzaste el nivel máximo!</Text>}
          <Pressable style={styles.btn} onPress={onClose}>
            <Text style={styles.btnText}>¡Genial!</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: COLORS.overlay,
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
    overflow: 'hidden',
  },
  title: { fontSize: 22, fontWeight: '900', color: COLORS.primary, marginBottom: 12 },
  charWrap: { marginVertical: 8, height: 130, justifyContent: 'center' },
  level: { fontSize: 30, fontWeight: '900', color: COLORS.textDark, marginTop: 4 },
  rank: { fontSize: 16, fontWeight: '700', color: COLORS.gold, marginTop: 2 },
  maxNote: { fontSize: 14, fontWeight: '700', color: COLORS.green, marginTop: 8 },
  btn: {
    marginTop: 20,
    backgroundColor: COLORS.primary,
    borderRadius: 14,
    paddingVertical: 12,
    paddingHorizontal: 40,
  },
  btnText: { color: COLORS.white, fontWeight: '800', fontSize: 16 },
});

export default LevelUpModal;
