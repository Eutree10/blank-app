import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { COLORS } from '../constants/colors';
import PixelIcon, { IconName } from './PixelIcon';

// Minimal shape of the props a bottom tab bar receives from Expo Router.
interface TabBarProps {
  state: {
    index: number;
    routes: { key: string; name: string }[];
  };
  navigation: {
    emit: (event: {
      type: 'tabPress';
      target: string;
      canPreventDefault: true;
    }) => { defaultPrevented: boolean };
    navigate: (name: string) => void;
  };
}

const TABS: { name: string; label: string; icon: IconName }[] = [
  { name: 'index', label: 'Inicio', icon: 'home' },
  { name: 'habits', label: 'Hábitos', icon: 'habits' },
  { name: 'shop', label: 'Tienda', icon: 'shop' },
  { name: 'profile', label: 'Perfil', icon: 'profile' },
];

// Fixed bottom navigation bar with four sections.
function BottomNavigation({ state, navigation }: TabBarProps) {
  const insets = useSafeAreaInsets();
  return (
    <View style={[styles.bar, { paddingBottom: Math.max(insets.bottom, 10) }]}>
      {TABS.map((tab, index) => {
        const focused = state.index === index;
        const color = focused ? COLORS.primary : COLORS.textMuted;
        return (
          <Pressable
            key={tab.name}
            style={styles.item}
            onPress={() => {
              const event = navigation.emit({
                type: 'tabPress',
                target: state.routes[index].key,
                canPreventDefault: true,
              });
              if (!focused && !event.defaultPrevented) {
                navigation.navigate(state.routes[index].name);
              }
            }}
            accessibilityRole="button"
            accessibilityState={{ selected: focused }}
          >
            <View style={[styles.iconWrap, focused && styles.iconWrapActive]}>
              <PixelIcon name={tab.icon} color={color} pixel={3} />
            </View>
            <Text style={[styles.label, { color }]}>{tab.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    backgroundColor: COLORS.card,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    paddingTop: 8,
    shadowColor: COLORS.shadow,
    shadowOpacity: 0.05,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: -2 },
    elevation: 8,
  },
  item: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  iconWrap: {
    width: 40,
    height: 30,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 10,
  },
  iconWrapActive: { backgroundColor: '#FBE9E9' },
  label: { fontSize: 11, fontWeight: '700', marginTop: 2 },
});

export default BottomNavigation;
