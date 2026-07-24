import React from 'react';
import { ScrollView, StyleSheet, Switch, Text, View, Pressable } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { usePlayer } from '../../context/PlayerContext';
import { COLORS } from '../../constants/colors';
import { rankForLevel } from '../../utils/level';
import PixelCharacter from '../../components/PixelCharacter';
import { confirmAction } from '../../utils/confirm';

function StatRow({ label, value }: { label: string; value: string | number }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={styles.rowValue}>{value}</Text>
    </View>
  );
}

// Profile screen: player summary, settings and reset.
export default function ProfileScreen() {
  const { state, toggleSound, resetProgress } = usePlayer();
  const insets = useSafeAreaInsets();
  const { stats } = state;

  const handleReset = () => {
    confirmAction(
      'Reiniciar progreso',
      'Se borrará todo tu progreso. Esta acción no se puede deshacer.',
      resetProgress,
      'Reiniciar'
    );
  };

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={[styles.content, { paddingTop: insets.top + 12 }]}
      showsVerticalScrollIndicator={false}
    >
      <Text style={styles.title}>Perfil</Text>

      <View style={styles.hero}>
        <PixelCharacter pixel={9} running />
        <Text style={styles.level}>Nivel {stats.level}</Text>
        <View style={styles.rankBadge}>
          <Text style={styles.rankText}>{rankForLevel(stats.level)}</Text>
        </View>
      </View>

      <View style={styles.card}>
        <StatRow label="XP total obtenida" value={stats.totalXp} />
        <View style={styles.divider} />
        <StatRow label="Monedas actuales" value={stats.coins} />
        <View style={styles.divider} />
        <StatRow label="Hábitos completados" value={stats.habitsCompleted} />
        <View style={styles.divider} />
        <StatRow label="Días activos" value={stats.activeDays} />
      </View>

      <View style={styles.card}>
        <View style={styles.row}>
          <Text style={styles.rowLabel}>Sonido</Text>
          <Switch
            value={state.soundEnabled}
            onValueChange={toggleSound}
            trackColor={{ true: COLORS.green, false: COLORS.border }}
            thumbColor={COLORS.white}
          />
        </View>
      </View>

      <Pressable style={styles.resetBtn} onPress={handleReset}>
        <Text style={styles.resetText}>Reiniciar progreso</Text>
      </Pressable>

      <Text style={styles.note}>
        Tus datos se guardan únicamente en este dispositivo.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background },
  content: { paddingHorizontal: 18, paddingBottom: 40 },
  title: { fontSize: 24, fontWeight: '900', color: COLORS.textDark, marginBottom: 12 },
  hero: { alignItems: 'center', marginVertical: 10 },
  level: { fontSize: 26, fontWeight: '900', color: COLORS.textDark, marginTop: 14 },
  rankBadge: {
    backgroundColor: COLORS.primary,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 5,
    marginTop: 6,
  },
  rankText: { color: COLORS.white, fontWeight: '800', fontSize: 13 },
  card: {
    backgroundColor: COLORS.card,
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingVertical: 4,
    marginTop: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
  },
  rowLabel: { fontSize: 14, fontWeight: '600', color: COLORS.textMuted },
  rowValue: { fontSize: 16, fontWeight: '800', color: COLORS.textDark },
  divider: { height: 1, backgroundColor: COLORS.border },
  resetBtn: {
    marginTop: 20,
    backgroundColor: COLORS.card,
    borderRadius: 14,
    paddingVertical: 15,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: COLORS.primary,
  },
  resetText: { color: COLORS.primary, fontWeight: '800', fontSize: 15 },
  note: {
    textAlign: 'center',
    color: COLORS.textMuted,
    fontSize: 12,
    marginTop: 16,
    fontWeight: '500',
  },
});
