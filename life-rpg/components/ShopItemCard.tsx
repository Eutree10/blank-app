import React, { useRef } from 'react';
import { Animated, Pressable, StyleSheet, Text, View } from 'react-native';
import { Reward } from '../types';
import { COLORS } from '../constants/colors';

interface Props {
  reward: Reward;
  affordable: boolean;
  onBuy: () => void;
  onDelete: () => void;
}

// A single reward tile in the shop grid (two-column layout).
function ShopItemCard({ reward, affordable, onBuy, onDelete }: Props) {
  const anim = useRef(new Animated.Value(1)).current;

  const handleBuy = () => {
    Animated.sequence([
      Animated.timing(anim, { toValue: 0.94, duration: 90, useNativeDriver: true }),
      Animated.spring(anim, { toValue: 1, useNativeDriver: true }),
    ]).start();
    onBuy();
  };

  return (
    <Animated.View style={[styles.card, { transform: [{ scale: anim }] }]}>
      <Pressable
        onPress={onDelete}
        hitSlop={6}
        style={styles.deleteBtn}
        accessibilityLabel="Eliminar recompensa"
      >
        <Text style={styles.deleteText}>×</Text>
      </Pressable>

      <View style={styles.iconBox}>
        <Text style={styles.icon}>{reward.icon}</Text>
      </View>
      <Text style={styles.name} numberOfLines={2}>
        {reward.name}
      </Text>
      <View style={styles.priceRow}>
        <Text style={styles.coin}>🪙</Text>
        <Text style={styles.price}>{reward.price}</Text>
      </View>
      <Pressable
        onPress={handleBuy}
        style={[styles.buyBtn, !affordable && styles.buyBtnDisabled]}
      >
        <Text style={styles.buyText}>Comprar</Text>
      </Pressable>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 14,
    margin: 6,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
    shadowColor: COLORS.shadow,
    shadowOpacity: 0.05,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  deleteBtn: {
    position: 'absolute',
    top: 6,
    right: 8,
    width: 22,
    height: 22,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 5,
  },
  deleteText: { fontSize: 18, color: COLORS.textMuted, fontWeight: '700', lineHeight: 20 },
  iconBox: {
    width: 52,
    height: 52,
    borderRadius: 14,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
    marginTop: 4,
  },
  icon: { fontSize: 28 },
  name: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.textDark,
    textAlign: 'center',
    minHeight: 36,
  },
  priceRow: { flexDirection: 'row', alignItems: 'center', marginVertical: 8 },
  coin: { fontSize: 14, marginRight: 4 },
  price: { fontSize: 15, fontWeight: '800', color: COLORS.gold },
  buyBtn: {
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    paddingVertical: 9,
    width: '100%',
    alignItems: 'center',
  },
  buyBtnDisabled: { backgroundColor: '#E7C3C3' },
  buyText: { color: COLORS.white, fontWeight: '800', fontSize: 13 },
});

export default React.memo(ShopItemCard);
