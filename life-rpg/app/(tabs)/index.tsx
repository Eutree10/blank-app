import React from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { usePlayer } from '../../context/PlayerContext';
import { COLORS } from '../../constants/colors';
import { MAX_LIFE } from '../../constants/game';
import { rankForLevel } from '../../utils/level';
import PixelCharacter from '../../components/PixelCharacter';
import StatBar from '../../components/StatBar';
import StatChip from '../../components/StatChip';

// Home screen: the most important information at a glance.
export default function HomeScreen() {
  const { state, xpNeeded, maxLevel, lifeZero } = usePlayer();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { stats } = state;

  const goodHabits = state.habits.filter((h) => h.type === 'good');
  const completedGoodToday = goodHabits.filter((h) => state.completedToday.includes(h.id)).length;

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={[styles.content, { paddingTop: insets.top + 12 }]}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <Text style={styles.greeting}>Tu aventura de hoy</Text>
      <View style={styles.chipsRow}>
        <StatChip icon="🎯" value={`Nivel ${stats.level}`} color={COLORS.primary} />
        <StatChip icon="🪙" value={stats.coins} color={COLORS.gold} />
        <StatChip icon="❤️" value={stats.life} color={COLORS.primaryDark} />
      </View>

      {/* Character */}
      <View style={styles.characterArea}>
        <View style={styles.rankBadge}>
          <Text style={styles.rankText}>{rankForLevel(stats.level)}</Text>
        </View>
        <PixelCharacter pixel={10} running={!lifeZero} />
      </View>

      {/* Progress card */}
      <View style={styles.card}>
        <StatBar
          label="Experiencia"
          value={stats.xp}
          max={xpNeeded}
          color={COLORS.gold}
          trackColor={COLORS.xpTrack}
          valueText={maxLevel ? 'Nivel máximo' : `${stats.xp} / ${xpNeeded} XP`}
        />
        <StatBar
          label="Vida"
          value={stats.life}
          max={MAX_LIFE}
          color={COLORS.primary}
          trackColor={COLORS.lifeTrack}
        />
        <View style={styles.coinsRow}>
          <Text style={styles.coinsLabel}>Monedas</Text>
          <Text style={styles.coinsValue}>🪙 {stats.coins}</Text>
        </View>
      </View>

      {/* Today summary */}
      <View style={styles.card}>
        <Text style={styles.summaryTitle}>Hábitos de hoy</Text>
        <Text style={styles.summaryText}>
          {completedGoodToday} de {goodHabits.length} hábitos buenos completados
        </Text>
      </View>

      {/* Primary action */}
      <Pressable style={styles.mainBtn} onPress={() => router.push('/habits')}>
        <Text style={styles.mainBtnText}>Ver hábitos</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background },
  content: { paddingHorizontal: 18, paddingBottom: 28 },
  greeting: { fontSize: 24, fontWeight: '900', color: COLORS.textDark, marginBottom: 12 },
  chipsRow: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
  characterArea: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 18,
    height: 190,
  },
  rankBadge: {
    backgroundColor: COLORS.primary,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 5,
    marginBottom: 16,
  },
  rankText: { color: COLORS.white, fontWeight: '800', fontSize: 13 },
  card: {
    backgroundColor: COLORS.card,
    borderRadius: 18,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
    shadowColor: COLORS.shadow,
    shadowOpacity: 0.04,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 1,
  },
  coinsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  coinsLabel: { fontSize: 13, fontWeight: '700', color: COLORS.textDark },
  coinsValue: { fontSize: 15, fontWeight: '800', color: COLORS.gold },
  summaryTitle: { fontSize: 15, fontWeight: '800', color: COLORS.textDark, marginBottom: 4 },
  summaryText: { fontSize: 14, color: COLORS.textMuted, fontWeight: '600' },
  mainBtn: {
    backgroundColor: COLORS.primary,
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 4,
  },
  mainBtnText: { color: COLORS.white, fontWeight: '900', fontSize: 16 },
});
