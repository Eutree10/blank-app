import AsyncStorage from '@react-native-async-storage/async-storage';
import { PlayerState } from '../types';
import { INITIAL_HABITS, INITIAL_REWARDS } from '../constants/initialData';
import { STARTING_LIFE } from '../constants/game';
import { todayKey } from '../utils/date';

const STORAGE_KEY = 'life-rpg-state-v1';

// The default state for a brand new player.
export function createInitialState(): PlayerState {
  return {
    stats: {
      level: 1,
      xp: 0,
      coins: 0,
      life: STARTING_LIFE,
      totalXp: 0,
      habitsCompleted: 0,
      activeDays: 1,
    },
    habits: INITIAL_HABITS.map((h) => ({ ...h })),
    rewards: INITIAL_REWARDS.map((r) => ({ ...r })),
    completedToday: [],
    purchases: [],
    soundEnabled: true,
    lastActiveDate: todayKey(),
  };
}

export async function loadState(): Promise<PlayerState> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    if (!raw) return createInitialState();
    const parsed = JSON.parse(raw) as PlayerState;
    // Merge with defaults so older saved states remain valid.
    const base = createInitialState();
    return {
      ...base,
      ...parsed,
      stats: { ...base.stats, ...parsed.stats },
      habits: parsed.habits ?? base.habits,
      rewards: parsed.rewards ?? base.rewards,
      completedToday: parsed.completedToday ?? [],
      purchases: parsed.purchases ?? [],
    };
  } catch (e) {
    // If anything is corrupted, fall back to a fresh state rather than crash.
    return createInitialState();
  }
}

export async function saveState(state: PlayerState): Promise<void> {
  try {
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (e) {
    // Storage failures are non-fatal for the running session.
  }
}

export async function clearState(): Promise<void> {
  try {
    await AsyncStorage.removeItem(STORAGE_KEY);
  } catch (e) {
    // ignore
  }
}
