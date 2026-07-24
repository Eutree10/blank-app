import React, { useState } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { usePlayer } from '../../context/PlayerContext';
import { COLORS } from '../../constants/colors';
import { Habit, HabitType } from '../../types';
import HabitCard from '../../components/HabitCard';
import HabitFormModal from '../../components/HabitFormModal';
import { confirmAction } from '../../utils/confirm';

// Habits screen: two tabs (good / bad) with a floating "+" to create habits.
export default function HabitsScreen() {
  const {
    state,
    completeGoodHabit,
    registerBadHabit,
    addHabit,
    updateHabit,
    deleteHabit,
  } = usePlayer();
  const insets = useSafeAreaInsets();

  const [tab, setTab] = useState<HabitType>('good');
  const [formVisible, setFormVisible] = useState(false);
  const [editing, setEditing] = useState<Habit | null>(null);

  const habits = state.habits.filter((h) => h.type === tab);

  const openCreate = () => {
    setEditing(null);
    setFormVisible(true);
  };

  const openEdit = (habit: Habit) => {
    setEditing(habit);
    setFormVisible(true);
  };

  const handleDelete = (habit: Habit) => {
    confirmAction('Eliminar hábito', `¿Eliminar "${habit.name}"?`, () => deleteHabit(habit.id), 'Eliminar');
  };

  const handleSave = (habit: Habit | Omit<Habit, 'id'>) => {
    if ('id' in habit) updateHabit(habit as Habit);
    else addHabit(habit);
  };

  return (
    <View style={[styles.screen, { paddingTop: insets.top + 12 }]}>
      <Text style={styles.title}>Hábitos</Text>

      {/* Tabs */}
      <View style={styles.tabs}>
        <Pressable
          style={[styles.tab, tab === 'good' && styles.tabActiveGood]}
          onPress={() => setTab('good')}
        >
          <Text style={[styles.tabText, tab === 'good' && styles.tabTextActive]}>Buenos</Text>
        </Pressable>
        <Pressable
          style={[styles.tab, tab === 'bad' && styles.tabActiveBad]}
          onPress={() => setTab('bad')}
        >
          <Text style={[styles.tabText, tab === 'bad' && styles.tabTextActive]}>Malos</Text>
        </Pressable>
      </View>

      <FlatList
        data={habits}
        keyExtractor={(h) => h.id}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => (
          <HabitCard
            habit={item}
            completed={state.completedToday.includes(item.id)}
            onComplete={() =>
              item.type === 'good' ? completeGoodHabit(item.id) : registerBadHabit(item.id)
            }
            onEdit={() => openEdit(item)}
            onDelete={() => handleDelete(item)}
          />
        )}
        ListEmptyComponent={
          <Text style={styles.empty}>
            No hay hábitos {tab === 'good' ? 'buenos' : 'malos'} todavía.
          </Text>
        }
      />

      {/* Floating add button */}
      <Pressable
        style={[styles.fab, { bottom: 20 }]}
        onPress={openCreate}
        accessibilityLabel="Crear nuevo hábito"
      >
        <Text style={styles.fabText}>+</Text>
      </Pressable>

      <HabitFormModal
        visible={formVisible}
        initial={editing}
        onClose={() => setFormVisible(false)}
        onSave={handleSave}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background, paddingHorizontal: 18 },
  title: { fontSize: 24, fontWeight: '900', color: COLORS.textDark, marginBottom: 12 },
  tabs: {
    flexDirection: 'row',
    backgroundColor: COLORS.card,
    borderRadius: 14,
    padding: 4,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: 14,
  },
  tab: { flex: 1, paddingVertical: 11, borderRadius: 10, alignItems: 'center' },
  tabActiveGood: { backgroundColor: COLORS.green },
  tabActiveBad: { backgroundColor: COLORS.primaryDark },
  tabText: { fontWeight: '800', color: COLORS.textMuted, fontSize: 14 },
  tabTextActive: { color: COLORS.white },
  list: { paddingBottom: 100 },
  empty: { textAlign: 'center', color: COLORS.textMuted, marginTop: 40, fontSize: 14, fontWeight: '600' },
  fab: {
    position: 'absolute',
    right: 20,
    width: 58,
    height: 58,
    borderRadius: 29,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: COLORS.shadow,
    shadowOpacity: 0.25,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
    elevation: 6,
  },
  fabText: { color: COLORS.white, fontSize: 32, fontWeight: '700', lineHeight: 36, marginTop: -2 },
});
