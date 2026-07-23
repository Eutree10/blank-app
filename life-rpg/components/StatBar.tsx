import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { COLORS } from '../constants/colors';

interface Props {
  label: string;
  value: number;
  max: number;
  color: string;
  trackColor?: string;
  valueText?: string; // optional custom right-side text
}

// A labelled progress bar used for XP and Life.
function StatBar({ label, value, max, color, trackColor = COLORS.border, valueText }: Props) {
  const pct = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;
  return (
    <View style={styles.container}>
      <View style={styles.labelRow}>
        <Text style={styles.label}>{label}</Text>
        <Text style={styles.value}>{valueText ?? `${value} / ${max}`}</Text>
      </View>
      <View style={[styles.track, { backgroundColor: trackColor }]}>
        <View style={[styles.fill, { width: `${pct}%`, backgroundColor: color }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { width: '100%', marginVertical: 6 },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  label: { color: COLORS.textDark, fontWeight: '700', fontSize: 13 },
  value: { color: COLORS.textMuted, fontWeight: '600', fontSize: 13 },
  track: {
    height: 14,
    borderRadius: 8,
    overflow: 'hidden',
  },
  fill: { height: '100%', borderRadius: 8 },
});

export default React.memo(StatBar);
