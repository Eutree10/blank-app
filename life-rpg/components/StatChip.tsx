import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { COLORS } from '../constants/colors';

interface Props {
  icon: string;
  value: string | number;
  color?: string;
}

// Compact pill showing a single stat (coins, life, level) in a header row.
function StatChip({ icon, value, color = COLORS.textDark }: Props) {
  return (
    <View style={styles.chip}>
      <Text style={styles.icon}>{icon}</Text>
      <Text style={[styles.value, { color }]}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  icon: { fontSize: 14, marginRight: 5 },
  value: { fontSize: 14, fontWeight: '800' },
});

export default StatChip;
