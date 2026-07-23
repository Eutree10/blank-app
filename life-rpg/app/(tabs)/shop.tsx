import React, { useState } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { usePlayer } from '../../context/PlayerContext';
import { COLORS } from '../../constants/colors';
import { Reward } from '../../types';
import ShopItemCard from '../../components/ShopItemCard';
import RewardFormModal from '../../components/RewardFormModal';
import Toast from '../../components/Toast';
import { confirmAction } from '../../utils/confirm';

// Shop screen: two-column grid of rewards the player can buy with coins.
export default function ShopScreen() {
  const { state, buyReward, addReward, deleteReward } = usePlayer();
  const insets = useSafeAreaInsets();

  const [formVisible, setFormVisible] = useState(false);
  const [toast, setToast] = useState<{ message: string; error: boolean } | null>(null);

  const handleBuy = (reward: Reward) => {
    const result = buyReward(reward.id);
    setToast({ message: result.message, error: !result.ok });
  };

  const handleDelete = (reward: Reward) => {
    confirmAction('Eliminar recompensa', `¿Eliminar "${reward.name}"?`, () => deleteReward(reward.id), 'Eliminar');
  };

  return (
    <View style={[styles.screen, { paddingTop: insets.top + 12 }]}>
      <View style={styles.header}>
        <Text style={styles.title}>Tienda</Text>
        <View style={styles.coinsChip}>
          <Text style={styles.coinsText}>🪙 {state.stats.coins}</Text>
        </View>
      </View>

      <FlatList
        data={state.rewards}
        keyExtractor={(r) => r.id}
        numColumns={2}
        contentContainerStyle={styles.list}
        columnWrapperStyle={styles.column}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => (
          <ShopItemCard
            reward={item}
            affordable={state.stats.coins >= item.price}
            onBuy={() => handleBuy(item)}
            onDelete={() => handleDelete(item)}
          />
        )}
        ListFooterComponent={
          <Pressable style={styles.addBtn} onPress={() => setFormVisible(true)}>
            <Text style={styles.addBtnText}>+ Agregar recompensa</Text>
          </Pressable>
        }
        ListEmptyComponent={<Text style={styles.empty}>No hay recompensas todavía.</Text>}
      />

      <RewardFormModal
        visible={formVisible}
        onClose={() => setFormVisible(false)}
        onSave={addReward}
      />

      <Toast
        message={toast?.message ?? null}
        error={toast?.error}
        onHide={() => setToast(null)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background, paddingHorizontal: 12 },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 6,
    marginBottom: 12,
  },
  title: { fontSize: 24, fontWeight: '900', color: COLORS.textDark },
  coinsChip: {
    backgroundColor: COLORS.card,
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  coinsText: { fontSize: 15, fontWeight: '800', color: COLORS.gold },
  list: { paddingBottom: 100 },
  column: { justifyContent: 'space-between' },
  addBtn: {
    marginTop: 10,
    marginHorizontal: 6,
    backgroundColor: COLORS.card,
    borderRadius: 14,
    paddingVertical: 15,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: COLORS.primary,
    borderStyle: 'dashed',
  },
  addBtnText: { color: COLORS.primary, fontWeight: '800', fontSize: 15 },
  empty: { textAlign: 'center', color: COLORS.textMuted, marginTop: 40, fontSize: 14, fontWeight: '600' },
});
