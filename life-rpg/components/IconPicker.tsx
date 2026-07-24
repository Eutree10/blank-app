import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { COLORS } from '../constants/colors';

interface Props {
  icons: string[];
  selected: string;
  onSelect: (icon: string) => void;
}

// A small wrapping grid of selectable icons.
function IconPicker({ icons, selected, onSelect }: Props) {
  return (
    <View style={styles.grid}>
      {icons.map((icon) => {
        const active = icon === selected;
        return (
          <Pressable
            key={icon}
            onPress={() => onSelect(icon)}
            style={[styles.cell, active && styles.cellActive]}
          >
            <Text style={styles.icon}>{icon}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 4 },
  cell: {
    width: 46,
    height: 46,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    margin: 4,
    backgroundColor: COLORS.background,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  cellActive: { borderColor: COLORS.primary, backgroundColor: '#FBE9E9' },
  icon: { fontSize: 22 },
});

export default IconPicker;
